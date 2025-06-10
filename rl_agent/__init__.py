"""
Reinforcement Learning Agent for Othello.

This package implements a simple Q-learning agent from scratch using PyTorch. It is designed to train
against other agents (including itself) in the game of Othello, using the `Board` class from the main project.

Modules:
- q_network.py: Defines a small feedforward neural network for estimating Q-values.
- rl_agent.py: Implements the RLAgent class as a subclass of Player.
- train_rl_agent.py: Entry point for training the agent via self-play or vs. scripted opponents.
- utils.py: Helper functions (e.g., board encoding, action masking).
- replay_buffer.py (optional): For experience replay if needed.

Design:
The agent observes board states, selects legal actions using an ε-greedy policy, and updates Q-values
using a temporal difference (TD) target after each episode.

Goal:
Train an agent that learns effective Othello strategies through reinforcement learning.

Author: Jonas Petersen
"""
