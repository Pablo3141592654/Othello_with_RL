import os
import numpy as np
from game.board import Board
from rl_agent.rl_agent import RLAgent
from game.player import MinimaxMax, RLRandomRiley
import torch
import wandb
from collections import deque
import re
from datetime import datetime
import json

# --- Helper functions for model filename convention ---
def parse_episode_count_from_filename(filename):
    match = re.search(r'_(\\d+)Episodes', filename)
    if match:
        return int(match.group(1))
    return 0

def build_model_filename(opponent_name, total_episodes, device, date=None):
    if date is None:
        date = datetime.now().strftime('%Y%m%d')
    return f"opp{opponent_name}_{total_episodes}Episodes_{device}_{date}.pth"

def get_new_model_filename(base_name, total_episodes):
    return f"{base_name}_{total_episodes}Episodes.pth"

def save_metadata(model_path, total_episodes, config):
    meta = {
        "model_path": model_path,
        "total_episodes": total_episodes,
        "config": config,
    }
    meta_path = model_path.replace('.pth', '.meta.json')
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=2)
    print(f"Metadata saved to {meta_path}")

# --- Setup ---
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
NUM_EPISODES = 50
MODEL_DIR = "rl_agent/models"

opponent = RLRandomRiley(-1)
opponent_name = type(opponent).__name__  # For filename

# Detect if resuming from a previous model
existing_model = None
existing_episodes = 0

# Find latest model for this opponent (optional: could be improved to pick latest by date)
for fname in os.listdir(MODEL_DIR):
    if fname.startswith(f"opp{opponent_name}_") and fname.endswith(".pth"):
        if parse_episode_count_from_filename(fname) > existing_episodes:
            existing_model = fname
            existing_episodes = parse_episode_count_from_filename(fname)

total_episodes = existing_episodes + NUM_EPISODES
MODEL_NAME = build_model_filename(opponent_name, total_episodes, device.type)
MODEL_PATH = os.path.join(MODEL_DIR, MODEL_NAME)

os.makedirs(MODEL_DIR, exist_ok=True)

agent = RLAgent(1, epsilon=0.2, device=device)

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

    # Parse previous episode count if resuming
    prev_episodes = 0
    base_model_name = None
    if os.path.exists(MODEL_PATH):
        agent.model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
        print(f"Loaded existing model from {MODEL_PATH}")
        prev_episodes = parse_episode_count_from_filename(MODEL_NAME)
        # Remove _{n}Episodes.pth to get base name
        base_model_name = re.sub(r'_\\d+Episodes\\.pth$', '', MODEL_NAME)
    else:
        # Remove _{n}Episodes.pth if present, else strip .pth
        base_model_name = re.sub(r'_\\d+Episodes\\.pth$', '', MODEL_NAME)
        base_model_name = base_model_name.replace('.pth', '')

    for episode in range(NUM_EPISODES):
        black_score, red_score = play_game(agent, opponent, train=True)
        agent.train_step()
        win = 1 if black_score > red_score else 0
        total_wins += win
        win_rate = total_wins / (episode + 1)
        score_diff = black_score - red_score
        avg_score_diff = (avg_score_diff * episode + score_diff) / (episode + 1)
        wandb.log({
            "episode": prev_episodes + episode + 1,
            "win_rate": win_rate,
            "epsilon": agent.epsilon,
            "score_diff": score_diff,
            "avg_score_diff": avg_score_diff
            # ...other metrics...
        })
        print(f"Episode {prev_episodes + episode + 1}: Black {black_score}, Red {red_score}")

    # Save model with updated episode count
    total_episodes = prev_episodes + NUM_EPISODES
    new_model_name = get_new_model_filename(base_model_name, total_episodes)
    new_model_path = os.path.join(MODEL_DIR, new_model_name)
    torch.save(agent.model.state_dict(), new_model_path)
    print(f"Model saved to {new_model_path}")

    # Save metadata
    save_metadata(new_model_path, total_episodes, dict(wandb.config))

    # Load the trained model for testing (optional, but good practice)
    test_agent_instance = RLAgent(1, epsilon=0.0, device=device)
    test_agent_instance.model.load_state_dict(torch.load(new_model_path, map_location=device))
    test_agent_instance.model.eval()

    # Test against RLRandomRiley
    print("Testing trained agent vs RLRandomRiley...")
    test_agent(test_agent_instance, RLRandomRiley(-1), episodes=48)