import numpy as np
from game.board import Board
from rl_agent.rl_agent import RLAgent
from game.player import GreedyGreta
import torch

NUM_EPISODES = 1000

def play_game(agent_black, agent_red, train=True):
    board = Board()
    state = np.copy(board.state)
    current_player = agent_black
    other_player = agent_red
    color = 1

    while True:
        valid_moves = board.get_valid_moves(color)
        if valid_moves:
            move = current_player.get_move(board)
            if move is not None:
                prev_state = np.copy(board.state)
                board.apply_move(color, *move)
                reward = 0  # You can design a better reward function
                done = not (board.has_valid_move(1) or board.has_valid_move(-1))
                next_state = np.copy(board.state)
                if train and isinstance(current_player, RLAgent):
                    current_player.store_transition(prev_state, move, reward, next_state, done)
        # Switch player
        color = -color
        current_player, other_player = other_player, current_player

        # Game over check
        if not board.has_valid_move(1) and not board.has_valid_move(-1):
            black_count, red_count = board.count_pieces()
            if train and isinstance(agent_black, RLAgent):
                final_reward = 1 if black_count > red_count else -1 if black_count < red_count else 0
                agent_black.store_transition(board.state, None, final_reward, board.state, True)
            if train and isinstance(agent_red, RLAgent):
                final_reward = 1 if red_count > black_count else -1 if red_count < black_count else 0
                agent_red.store_transition(board.state, None, final_reward, board.state, True)
            return black_count, red_count

if __name__ == "__main__":
    agent = RLAgent(1, epsilon=0.2)
    opponent = GreedyGreta(-1)  # Or RLAgent(-1) for self-play

    for episode in range(NUM_EPISODES):
        black_score, red_score = play_game(agent, opponent, train=True)
        agent.train_step()
        print(f"Episode {episode+1}: Black {black_score}, Red {red_score}")

    # Save model if you want
    torch.save(agent.model.state_dict(), "rl_agent.pth")