"""
RLAgent is a reinforcement learning agent for Othello, based on the Q-learning algorithm.
It inherits from the Player base class and uses a neural network to estimate Q-values
for board positions, choosing moves using an ε-greedy strategy.
"""

import torch
import torch.nn.functional as F 
import numpy as np
import random
import collections

from game.player import Player
from rl_agent.q_network import QNetwork
from rl_agent.utils import board_to_tensor, action_to_index, index_to_action

class RLAgent(Player):
    def __init__(self, color, board_size=8, epsilon=0.1, lr=1e-4, device=None, target_update_freq=100, replay_buffer_size=10000, batch_size=32):
        super().__init__(color)
        self.board_size = board_size
        self.epsilon = epsilon
        self.device = device or torch.device("cpu")
        self.model = QNetwork(board_size).to(self.device)
        self.target_model = QNetwork(board_size).to(self.device)
        self.target_model.load_state_dict(self.model.state_dict())
        self.target_model.eval()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        self.transitions = []
        self.replay_buffer = collections.deque(maxlen=replay_buffer_size)
        self.batch_size = batch_size
        self.train_steps = 0
        self.target_update_freq = target_update_freq

    def _to_tensor(self, board_state):
        return board_to_tensor(board_state, self.color).unsqueeze(0).to(self.device)

    def get_move(self, board_obj):
        valid_moves = board_obj.get_valid_moves(self.color)
        if not valid_moves:
            return None
        if random.random() < self.epsilon:
            return random.choice(valid_moves)
        q_values = self.model(self._to_tensor(board_obj.state)).detach().cpu().numpy().flatten()
        return max(valid_moves, key=lambda m: q_values[action_to_index(m, self.board_size)])

    def store_transition(self, state, action, reward, next_state, done):
        clipped_reward = float(np.clip(reward, -1, 1))
        transition = (state, action, clipped_reward, next_state, done)
        self.transitions.append(transition)
        self.replay_buffer.append(transition)

    def update_target_network(self):
        self.target_model.load_state_dict(self.model.state_dict())

    def train_step(self, gamma=0.99):
        if len(self.replay_buffer) < self.batch_size:
            self.transitions.clear()
            return None
        batch = random.sample(self.replay_buffer, self.batch_size)
        losses = [self._compute_loss(*sample, gamma) for sample in batch if sample[1] is not None]
        self.transitions.clear()
        if losses:
            avg_loss = sum(losses) / len(losses)
            return avg_loss
        return None

    def _compute_loss(self, state, action, reward, next_state, done, gamma):
        state_tensor = self._to_tensor(state)
        next_state_tensor = self._to_tensor(next_state)
        q_vals = self.model(state_tensor)
        target_q = reward
        if not done:
            with torch.no_grad():
                target_q += gamma * torch.max(self.target_model(next_state_tensor)).item()
        action_idx = action_to_index(action, self.board_size)
        pred_q = q_vals[0, action_idx]
        loss = F.smooth_l1_loss(pred_q, torch.tensor(target_q, dtype=torch.float32, device=self.device))
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=10.0)
        self.optimizer.step()
        self.train_steps += 1
        if self.train_steps % self.target_update_freq == 0:
            self.update_target_network()
        return loss.item()
