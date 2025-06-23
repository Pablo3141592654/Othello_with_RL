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
    def __init__(self, color, board_size=8, epsilon=0.1, lr=1e-3, device=None, target_update_freq=100, replay_buffer_size=10000, batch_size=32):
        super().__init__(color)
        self.board_size = board_size
        self.epsilon = epsilon
        self.device = device if device is not None else torch.device("cpu")
        self.model = QNetwork(board_size).to(self.device)
        self.target_model = QNetwork(board_size).to(self.device)
        self.target_model.load_state_dict(self.model.state_dict())
        self.target_model.eval()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        self.transitions = []  # List of (state, action, reward, next_state, done) for current episode
        self.replay_buffer = collections.deque(maxlen=replay_buffer_size)
        self.batch_size = batch_size
        self.train_steps = 0
        self.target_update_freq = target_update_freq

    def get_move(self, board_obj):
        board_tensor = board_to_tensor(board_obj.state, self.color).unsqueeze(0).to(self.device)  # shape [1, 2, 8, 8]
        q_values = self.model(board_tensor).detach().cpu().numpy().flatten()

        valid_moves = board_obj.get_valid_moves(self.color)
        if not valid_moves:
            return None

        if random.random() < self.epsilon:
            return random.choice(valid_moves)

        # Pick move with highest Q-value (mask illegal moves)
        best_move = max(valid_moves, key=lambda m: q_values[action_to_index(m, self.board_size)])
        return best_move

    def store_transition(self, state, action, reward, next_state, done):
        self.transitions.append((state, action, reward, next_state, done))
        self.replay_buffer.append((state, action, reward, next_state, done))
        print(f"Stored transition. Total transitions this episode: {len(self.transitions)} | Replay buffer size: {len(self.replay_buffer)}")

    def update_target_network(self):
        self.target_model.load_state_dict(self.model.state_dict())
        print("Target network updated.")

    def train_step(self, gamma=0.99):
        if len(self.replay_buffer) < self.batch_size:
            print(f"Not enough samples in replay buffer to train. Current size: {len(self.replay_buffer)}")
            self.transitions.clear()
            return None
        batch = random.sample(self.replay_buffer, self.batch_size)
        losses = []
        for state, action, reward, next_state, done in batch:
            if action is None:
                continue  # Skip final reward transitions with no action
            state_tensor = board_to_tensor(state, self.color).unsqueeze(0).to(self.device)
            next_state_tensor = board_to_tensor(next_state, self.color).unsqueeze(0).to(self.device)
            q_vals = self.model(state_tensor)
            target_q = reward
            if not done:
                with torch.no_grad():
                    next_q_vals = self.target_model(next_state_tensor)
                    target_q += gamma * torch.max(next_q_vals)
            action_idx = action_to_index(action, self.board_size)
            pred_q = q_vals[0, action_idx].item()
            loss = F.mse_loss(q_vals[0, action_idx], torch.tensor(target_q, dtype=torch.float32, device=self.device))
            print(f"train_step: pred_q={pred_q:.4f}, target_q={target_q:.4f}, reward={reward}, done={done}")
            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=10.0)  # Gradient clipping
            self.optimizer.step()
            losses.append(loss.item())
            self.train_steps += 1
            if self.train_steps % self.target_update_freq == 0:
                self.update_target_network()
        self.transitions.clear()
        if losses:
            avg_loss = sum(losses) / len(losses)
            print(f"train_step: Trained on {len(losses)} transitions. Avg loss: {avg_loss}")
            return avg_loss
        else:
            print("train_step: No valid transitions (all had action=None)")
            return None
