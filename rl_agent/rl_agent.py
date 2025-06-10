"""
RLAgent is a reinforcement learning agent for Othello, based on the Q-learning algorithm.
It inherits from the Player base class and uses a neural network to estimate Q-values
for board positions, choosing moves using an ε-greedy strategy.
"""

import torch
import torch.nn.functional as F
import numpy as np
import random

from player import Player
from rl_agent.q_network import QNetwork
from rl_agent.utils import board_to_tensor, action_to_index, index_to_action

class RLAgent(Player):
    def __init__(self, color, board_size=8, epsilon=0.1, lr=1e-3):
        super().__init__(color)
        self.board_size = board_size
        self.epsilon = epsilon
        self.model = QNetwork(board_size)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        self.transitions = []  # List of (state, action, reward, next_state, done)

    def get_move(self, board_obj):
        board_tensor = board_to_tensor(board_obj.state, self.color).unsqueeze(0)  # shape [1, 2, 8, 8]
        q_values = self.model(board_tensor).detach().numpy().flatten()

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

    def train_step(self, gamma=0.99):
        if not self.transitions:
            return

        for state, action, reward, next_state, done in self.transitions:
            state_tensor = board_to_tensor(state, self.color).unsqueeze(0)
            next_state_tensor = board_to_tensor(next_state, self.color).unsqueeze(0)

            q_vals = self.model(state_tensor)
            target_q = reward

            if not done:
                next_q_vals = self.model(next_state_tensor).detach()
                target_q += gamma * torch.max(next_q_vals)

            action_idx = action_to_index(action, self.board_size)
            loss = F.mse_loss(q_vals[0, action_idx], torch.tensor(target_q))

            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

        self.transitions.clear()
