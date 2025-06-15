import os
import numpy as np
from game.board import Board
from rl_agent.rl_agent import RLAgent
from game.player import GreedyGreta
import torch
import wandb
from collections import deque

NUM_EPISODES = 115
MODEL_NAME = "oppGreedyGreta_115Episodes.pth"  # <-- Set your model name here !!
MODEL_DIR = "rl_agent/models"
MODEL_PATH = os.path.join(MODEL_DIR, MODEL_NAME)

os.makedirs(MODEL_DIR, exist_ok=True)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

agent = RLAgent(1, epsilon=0.2, device=device)  # Pass device to RLAgent
opponent = GreedyGreta(-1)       # Or RLAgent(-1, device=device) for self-play

wandb.init(project="othello-rl", config={
    "episodes": NUM_EPISODES,
    "epsilon": agent.epsilon,
    "lr": 1e-3,
    # Add any other hyperparameters you want to track
})

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

def test_agent(agent, opponent, episodes=20):
    wins, losses, draws = 0, 0, 0
    for ep in range(episodes):
        black_score, red_score = play_game(agent, opponent, train=False)
        if black_score > red_score:
            wins += 1
        elif black_score < red_score:
            losses += 1
        else:
            draws += 1
    print(f"Test results over {episodes} games: Wins: {wins}, Losses: {losses}, Draws: {draws}")

if __name__ == "__main__":
    win_window = deque(maxlen=100)
    total_wins = 0
    avg_score_diff = 0

    for episode in range(NUM_EPISODES):
        black_score, red_score = play_game(agent, opponent, train=True)
        agent.train_step()
        win = 1 if black_score > red_score else 0
        total_wins += win
        win_rate = total_wins / (episode + 1)
        score_diff = black_score - red_score
        avg_score_diff = (avg_score_diff * episode + score_diff) / (episode + 1)
        wandb.log({
            "episode": episode,
            "win_rate": win_rate,
            "epsilon": agent.epsilon,
            "score_diff": score_diff,
            "avg_score_diff": avg_score_diff
            # ...other metrics...
        })
        print(f"Episode {episode+1}: Black {black_score}, Red {red_score}")

    # Save model to the specified folder and name
    torch.save(agent.model.state_dict(), MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

    # Load the trained model for testing (optional, but good practice)
    test_agent_instance = RLAgent(1, epsilon=0.0, device=device)
    test_agent_instance.model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    test_agent_instance.model.eval()

    # Test against GreedyGreta
    print("Testing trained agent vs GreedyGreta...")
    test_agent(test_agent_instance, GreedyGreta(-1), episodes=48)