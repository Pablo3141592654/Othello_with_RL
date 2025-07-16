import torch
import numpy as np

def board_to_tensor(board, color):
    # board: np.array shape [8,8], color: 1 or -1
    # Returns tensor shape [2,8,8]: [own pieces, opponent pieces]
    own = (board == color).astype(np.float32)
    opp = (board == -color).astype(np.float32)
    tensor = np.stack([own, opp], axis=0)
    return torch.tensor(tensor, dtype=torch.float32)

def action_to_index(action, board_size=8):
    # action: (row, col)
    return action[0] * board_size + action[1]

def index_to_action(idx, board_size=8):
    return (idx // board_size, idx % board_size)