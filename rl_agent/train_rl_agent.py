import os
import numpy as np
from game.board import Board
from rl_agent.rl_agent import RLAgent
from game.player import MinimaxMax, RLRandomRiley, GreedyGreta
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

from datetime import datetime
TRAINING_PHILOSOPHY = "SR-PMO"  # SR = shaped reward, PMO = progressive more difficult opponents
run_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
run_folder_name = f"run_{run_timestamp}_ep{NUM_EPISODES}_{TRAINING_PHILOSOPHY}"
RUN_DIR = os.path.join(MODEL_DIR, run_folder_name)
os.makedirs(RUN_DIR, exist_ok=True)

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

def calculate_shaped_reward(prev_board, new_board, move, player):
    if move is None:
        return 0
    row, col = move
    # Pieces flipped
    prev_pieces = np.sum(prev_board == -player)
    new_pieces = np.sum(new_board == -player)
    flipped = prev_pieces - new_pieces
    reward = flipped
    # Corners
    corners = [(0,0), (0,7), (7,0), (7,7)]
    if (row, col) in corners:
        if prev_board[row, col] != player and new_board[row, col] == player:
            reward += 5  # Just captured a corner
        elif prev_board[row, col] == player and new_board[row, col] == -player:
            reward -= 5  # Just lost a corner
    # Edges (not corners)
    if (row in [0,7] or col in [0,7]) and (row, col) not in corners:
        if prev_board[row, col] != player and new_board[row, col] == player:
            reward += 0.5  # Just captured an edge
        elif prev_board[row, col] == player and new_board[row, col] == -player:
            reward -= 0.5  # Just lost an edge
    return reward

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
                next_state = np.copy(board.state)
                reward = calculate_shaped_reward(prev_state, next_state, move, color)
                done = not (board.has_valid_move(1) or board.has_valid_move(-1))
                if train and isinstance(current_player, RLAgent):
                    current_player.store_transition(prev_state, move, reward, next_state, done)
        # Switch player
        color = -color
        current_player, other_player = other_player, current_player

        # Game over check
        if not board.has_valid_move(1) and not board.has_valid_move(-1):
            black_count, red_count = board.count_pieces()
            # Final shaped reward for win/loss/draw
            if train and isinstance(agent_black, RLAgent):
                if black_count > red_count:
                    final_reward = 50
                elif black_count < red_count:
                    final_reward = -50
                else:
                    final_reward = 0
                agent_black.store_transition(board.state, None, final_reward, board.state, True)
            if train and isinstance(agent_red, RLAgent):
                if red_count > black_count:
                    final_reward = 50
                elif red_count < black_count:
                    final_reward = -50
                else:
                    final_reward = 0
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

def select_opponent(win_rate, phase):
    # Curriculum: 0=Random, 1=GreedyGreta, 2=MinimaxMax, 3=Self-play
    if phase == 0:
        return RLRandomRiley(-1), 'RLRandomRiley'
    elif phase == 1:
        return GreedyGreta(-1), 'GreedyGreta'
    elif phase == 2:
        return MinimaxMax(-1, depths=[2,2]), 'MinimaxMax'
    else:
        # Self-play: agent vs. previous best
        prev_agent = RLAgent(-1, epsilon=0.0, device=device)
        # Load best model so far if available
        model_files = [f for f in os.listdir(MODEL_DIR) if f.endswith('.pth')]
        if model_files:
            best_model = sorted(model_files)[-1]
            prev_agent.model.load_state_dict(torch.load(os.path.join(MODEL_DIR, best_model), map_location=device))
        return prev_agent, 'SelfPlay'

if __name__ == "__main__":
    win_window = deque(maxlen=100)
    total_wins = 0
    avg_score_diff = 0
    phase = 0  # 0: random, 1: greedy, 2: minimax, 3: self-play
    win_thresholds = [0.9, 0.7, 0.5]  # thresholds to move to next phase
    opponent, opponent_name = select_opponent(0, phase)

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
        win_window.append(win)
        win_rate = sum(win_window) / len(win_window)
        score_diff = black_score - red_score
        avg_score_diff = (avg_score_diff * episode + score_diff) / (episode + 1)
        wandb.log({
            "episode": prev_episodes + episode + 1,
            "win_rate": win_rate,
            "epsilon": agent.epsilon,
            "score_diff": score_diff,
            "avg_score_diff": avg_score_diff,
            "phase": phase,
            "opponent": opponent_name
        })
        print(f"Episode {prev_episodes + episode + 1}: Black {black_score}, Red {red_score}, Win rate: {win_rate:.2f}, Phase: {phase}, Opponent: {opponent_name}")
        # Curriculum switch
        if phase < len(win_thresholds) and win_rate >= win_thresholds[phase]:
            phase += 1
            opponent, opponent_name = select_opponent(win_rate, phase)
            print(f"Switching to phase {phase}: Opponent {opponent_name}")
        # Periodic checkpoint saving every 1000 episodes
        if (episode + 1) % 1000 == 0:
            checkpoint_dir = os.path.join(RUN_DIR, f"checkpoint_{prev_episodes + episode + 1}")
            os.makedirs(checkpoint_dir, exist_ok=True)
            checkpoint_model_name = get_new_model_filename(base_model_name, prev_episodes + episode + 1)
            checkpoint_model_path = os.path.join(checkpoint_dir, checkpoint_model_name)
            torch.save(agent.model.state_dict(), checkpoint_model_path)
            print(f"Checkpoint saved to {checkpoint_model_path}")
            # Save metadata for checkpoint
            save_metadata(checkpoint_model_path, prev_episodes + episode + 1, dict(wandb.config))
    # Save model with updated episode count
    total_episodes = prev_episodes + NUM_EPISODES
    new_model_name = get_new_model_filename(base_model_name, total_episodes)
    new_model_path = os.path.join(RUN_DIR, new_model_name)
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