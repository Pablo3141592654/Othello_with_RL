import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
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
import random
from tqdm import tqdm  # For progress bars (optional, but common in RL)
from typing import Any, Tuple, List, Optional

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
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Train RL agent for Othello with curriculum learning.")
    parser.add_argument('--resume', type=str, default=None, help='Path to run folder to resume training from')
    parser.add_argument('--episodes', type=int, default=500, help='Number of episodes to train (default: 500)')
    return parser.parse_args()

args = parse_args()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# Use episodes from argument
NUM_EPISODES = args.episodes
MODEL_DIR = "rl_agent/models"

from datetime import datetime
TRAINING_PHILOSOPHY = "SR-PMO"  # SR = shaped reward, PMO = progressive more difficult opponents
if args.resume:
    RUN_DIR = args.resume
    print(f"Resuming training in {RUN_DIR}")
    # Ensure run dir exists
    os.makedirs(RUN_DIR, exist_ok=True)
    # Try to load previous metadata for wandb resume and stats
    summary_path = os.path.join(RUN_DIR, 'summary.meta.json')
    prev_wandb_id = None
    prev_wandb_config = None
    # --- NEW: running stats ---
    prev_stats = {}
    if os.path.exists(summary_path):
        with open(summary_path, 'r') as f:
            summary = json.load(f)
            prev_wandb_id = summary.get('wandb_id', None)
            prev_wandb_config = summary.get('wandb_config', None)
            # Load running stats if present
            prev_stats = summary.get('running_stats', {})
else:
    run_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    run_folder_name = f"run_{run_timestamp}_{TRAINING_PHILOSOPHY}"
    RUN_DIR = os.path.join(MODEL_DIR, run_folder_name)
    os.makedirs(RUN_DIR, exist_ok=True)
    prev_wandb_id = None
    prev_wandb_config = None

# Detect if resuming from a previous model
existing_model = None
existing_episodes = 0
opponent_name = None
# Find latest model for this opponent (optional: could be improved to pick latest by date)
for fname in os.listdir(MODEL_DIR):
    if fname.startswith("opp") and fname.endswith(".pth"):
        # Extract opponent name from filename
        match = re.match(r'opp([A-Za-z0-9_]+)_', fname)
        if match:
            name = match.group(1)
            episodes = parse_episode_count_from_filename(fname)
            if episodes > existing_episodes:
                existing_model = fname
                existing_episodes = episodes
                opponent_name = name

total_episodes = existing_episodes + NUM_EPISODES
MODEL_NAME = build_model_filename(opponent_name, total_episodes, device.type)
MODEL_PATH = os.path.join(MODEL_DIR, MODEL_NAME)

os.makedirs(MODEL_DIR, exist_ok=True)

agent = RLAgent(1, epsilon=0.1, device=device)  # Lower epsilon to 0.1

# --- wandb setup ---
wandb_kwargs = {
    'project': "othello-rl",
    'config': {
        "episodes": NUM_EPISODES,
        "epsilon": 0.1,
        "lr": 1e-3,
        # Add any other hyperparameters you want to track
    }
}
if prev_wandb_id:
    wandb_kwargs['id'] = prev_wandb_id
    wandb_kwargs['resume'] = 'must'
    if prev_wandb_config:
        wandb_kwargs['config'] = prev_wandb_config
wandb_run = wandb.init(**wandb_kwargs)

def calculate_shaped_reward(prev_board, new_board, move, player):
    if move is None:
        return 0
    # --- DEBUG: Only win/loss reward, no shaping ---
    # row, col = move
    # prev_pieces = np.sum(prev_board == -player)
    # new_pieces = np.sum(new_board == -player)
    # flipped = prev_pieces - new_pieces
    # reward = 0.1 * flipped  # Much smaller shaped reward
    # corners = [(0,0), (0,7), (7,0), (7,7)]
    # if (row, col) in corners:
    #     if prev_board[row, col] != player and new_board[row, col] == player:
    #         reward += 0.5  # Reduced corner bonus
    #     elif prev_board[row, col] == player and new_board[row, col] == -player:
    #         reward -= 0.5
    # if (row in [0,7] or col in [0,7]) and (row, col) not in corners:
    #     if prev_board[row, col] != player and new_board[row, col] == player:
    #         reward += 0.05  # Reduced edge bonus
    #     elif prev_board[row, col] == player and new_board[row, col] == -player:
    #         reward -= 0.05
    # return reward
    return 0  # Only win/loss reward

def play_game(agent_black, agent_red, train=True, log_rewards=None):
    board = Board()
    state = np.copy(board.state)
    current_player = agent_black
    other_player = agent_red
    color = 1
    total_reward = 0
    while True:
        valid_moves = board.get_valid_moves(color)
        if valid_moves:
            move = current_player.get_move(board)
            if move is not None:
                prev_state = np.copy(board.state)
                board.apply_move(color, *move)
                next_state = np.copy(board.state)
                reward = calculate_shaped_reward(prev_state, next_state, move, color)
                total_reward += reward
                done = not (board.has_valid_move(1) or board.has_valid_move(-1))
                if train and isinstance(current_player, RLAgent):
                    current_player.store_transition(prev_state, move, reward, next_state, done)
        # Switch player
        color = -color
        current_player, other_player = other_player, current_player

        # Game over check
        if not board.has_valid_move(1) and not board.has_valid_move(-1):
            black_count, red_count = board.count_pieces()
            # Final reward for win/loss/draw (skewed)
            if train and isinstance(agent_black, RLAgent):
                if black_count > red_count:
                    final_reward = 1  # CLIPPED REWARD
                elif black_count < red_count:
                    final_reward = -1  # CLIPPED REWARD
                else:
                    final_reward = 0
                agent_black.store_transition(board.state, None, final_reward, board.state, True)
                total_reward += final_reward
            if train and isinstance(agent_red, RLAgent):
                if red_count > black_count:
                    final_reward = 1  # CLIPPED REWARD
                elif red_count < black_count:
                    final_reward = -1  # CLIPPED REWARD
                else:
                    final_reward = 0
                agent_red.store_transition(board.state, None, final_reward, board.state, True)
            if log_rewards is not None:
                log_rewards.append(total_reward)
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
    return wins, losses, draws

def select_opponent(win_rate, phase):
    # Curriculum: 0=GreedyGreta, 1=RLRandomRiley, 2=MinimaxMax, 3=Self-play
    if phase == 0:
        return GreedyGreta(-1), 'GreedyGreta'
    elif phase == 1:
        return RLRandomRiley(-1), 'RLRandomRiley'
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

class PureRandomPlayer:
    def __init__(self, color):
        self.color = color
    def get_move(self, board):
        valid_moves = board.get_valid_moves(self.color)
        if not valid_moves:
            return None
        return random.choice(valid_moves)

if __name__ == "__main__":
    # Ensure prev_stats is always defined
    prev_stats = {}  # <-- Fix: always define prev_stats
    # --- Restore running stats if resuming ---
    win_window = deque(prev_stats.get('win_window', []), maxlen=100)
    total_wins = prev_stats.get('total_wins', 0)
    phase = prev_stats.get('phase', 0)
    phase_episode_counter = prev_stats.get('phase_episode_counter', 0)
    cumulative_score_diff = prev_stats.get('cumulative_score_diff', 0)
    cumulative_episodes = prev_stats.get('cumulative_episodes', 0)
    # If not resuming, use defaults
    if not args.resume:
        win_window = deque(maxlen=100)
        total_wins = 0
        phase = 0
        phase_episode_counter = 0
        cumulative_score_diff = 0
        cumulative_episodes = 0
    win_thresholds = [0.9, 0.5, 0.5]  # thresholds to move to next phase
    min_episodes_per_phase = [10, 10, 1, 1]  # Minimum episodes per phase (10 for GreedyGreta, 10 for RandomRiley)
    opponent, opponent_name = select_opponent(0, phase)

    # Parse previous episode count if resuming
    prev_episodes = 0
    base_model_name = None
    if args.resume and os.path.exists(RUN_DIR):
        # Resume from metadata file if available
        summary_path = os.path.join(RUN_DIR, 'summary.meta.json')
        if os.path.exists(summary_path):
            with open(summary_path, 'r') as f:
                summary = json.load(f)
                last_model = summary.get('last_model', None)
                prev_episodes = summary.get('total_episodes', 0)
                base_model_name = None
                if last_model:
                    agent.model.load_state_dict(torch.load(last_model, map_location=device))
                    print(f"Loaded existing model from {last_model}")
                    # Extract base_model_name from last_model path
                    last_model_filename = os.path.basename(last_model)
                    base_model_name = re.sub(r'_\d+Episodes\.pth$', '', last_model_filename)
                else:
                    base_model_name = f"opp{opponent_name}_{TRAINING_PHILOSOPHY}"
        else:
            # Fallback to filename-based resume if no metadata
            model_files = [f for f in os.listdir(RUN_DIR) if f.endswith('.pth')]
            if model_files:
                latest_model = sorted(model_files)[-1]
                agent.model.load_state_dict(torch.load(os.path.join(RUN_DIR, latest_model), map_location=device))
                print(f"Loaded existing model from {os.path.join(RUN_DIR, latest_model)}")
                prev_episodes = parse_episode_count_from_filename(latest_model)
                base_model_name = re.sub(r'_\d+Episodes\.pth$', '', latest_model)
            else:
                base_model_name = f"opp{opponent_name}_{TRAINING_PHILOSOPHY}"
    else:
        # Remove _{n}Episodes.pth if present, else strip .pth
        base_model_name = f"opp{opponent_name}_{TRAINING_PHILOSOPHY}"

    # --- Training loop ---
    phase_episode_counter = 0
    cumulative_score_diff = 0
    cumulative_episodes = 0
    episode_rewards = []  # For logging average reward
    episode_losses = []   # For logging average loss
    for episode in range(NUM_EPISODES):
        log_rewards = []
        q_values_list = []
        target_q_values_list = []
        loss_values = []
        # Print replay buffer size before training
        if hasattr(agent, 'replay_buffer'):
            print(f"Replay buffer size before episode {episode+1}: {len(agent.replay_buffer) if hasattr(agent.replay_buffer, '__len__') else 'unknown'}")
        black_score, red_score = play_game(agent, opponent, train=True, log_rewards=log_rewards)
        # --- Q-value and loss monitoring ---
        if hasattr(agent, 'replay_buffer') and len(agent.replay_buffer) >= agent.batch_size:
            batch = random.sample(agent.replay_buffer, agent.batch_size)
            for state, action, reward, next_state, done in batch:
                if action is None:
                    continue
                state_tensor = agent._to_tensor(state)
                next_state_tensor = agent._to_tensor(next_state)
                q_vals = agent.model(state_tensor).detach().cpu().numpy().flatten()
                q_values_list.append(q_vals.tolist())
                target_q = reward
                if not done:
                    with torch.no_grad():
                        next_q_vals = agent.target_model(next_state_tensor)
                        target_q += agent.train_step.__defaults__[0] * torch.max(next_q_vals).item()  # gamma
                target_q_values_list.append(target_q)
        loss = agent.train_step()  # Assume this returns the loss value
        if loss is not None:
            loss_values.append(loss)
        print(f"Episode {episode+1} loss: {loss}")
        win = 1 if black_score > red_score else 0
        win_window.append(win)
        score_diff = black_score - red_score
        cumulative_score_diff += score_diff
        cumulative_episodes += 1
        episode_rewards.append(np.sum(log_rewards))
        if loss is not None:
            episode_losses.append(loss)
        win_rate = sum(win_window) / len(win_window) if len(win_window) > 0 else 0
        avg_score_diff = cumulative_score_diff / cumulative_episodes if cumulative_episodes > 0 else 0
        avg_reward = np.mean(episode_rewards[-100:]) if len(episode_rewards) >= 1 else 0
        avg_loss = np.mean(episode_losses[-100:]) if len(episode_losses) >= 1 else 0
        global_episode = prev_episodes + episode + 1
        # --- Q-value/loss stats logging ---
        flat_qs = [q for sublist in q_values_list for q in sublist]
        q_stats = {
            'q_mean': float(np.mean(flat_qs)) if flat_qs else 0,
            'q_min': float(np.min(flat_qs)) if flat_qs else 0,
            'q_max': float(np.max(flat_qs)) if flat_qs else 0,
            'target_q_mean': float(np.mean(target_q_values_list)) if target_q_values_list else 0,
            'target_q_min': float(np.min(target_q_values_list)) if target_q_values_list else 0,
            'target_q_max': float(np.max(target_q_values_list)) if target_q_values_list else 0,
            'loss_mean': float(np.mean(loss_values)) if loss_values else 0,
            'loss_min': float(np.min(loss_values)) if loss_values else 0,
            'loss_max': float(np.max(loss_values)) if loss_values else 0,
        }
        wandb.log({
            "episode": global_episode,
            "win_rate": win_rate,
            "epsilon": agent.epsilon,
            "score_diff": score_diff,
            "avg_score_diff": avg_score_diff,
            "phase": phase,
            "opponent": opponent_name,
            "avg_reward": avg_reward,
            "avg_loss": avg_loss,
            **q_stats
        })
        print(f"Q-stats: mean={q_stats['q_mean']:.2f}, min={q_stats['q_min']:.2f}, max={q_stats['q_max']:.2f}, target_mean={q_stats['target_q_mean']:.2f}, loss_mean={q_stats['loss_mean']:.2f}")
        phase_episode_counter += 1
        # Curriculum switch: require minimum episodes per phase
        if phase < len(win_thresholds) and win_rate >= win_thresholds[phase] and phase_episode_counter >= min_episodes_per_phase[phase]:
            phase += 1
            opponent, opponent_name = select_opponent(win_rate, phase)
            phase_episode_counter = 0
            print(f"Switching to phase {phase}: Opponent {opponent_name}")
        # Save running stats for resume
        running_stats = {
            'win_window': [int(x) for x in win_window],
            'total_wins': int(total_wins),
            'phase': int(phase),
            'phase_episode_counter': int(phase_episode_counter),
            'cumulative_score_diff': float(cumulative_score_diff),
            'cumulative_episodes': int(cumulative_episodes)
        }
        # Periodic checkpoint saving every 1000 episodes
        if (episode + 1) % 1000 == 0:
            checkpoint_dir = os.path.join(RUN_DIR, f"checkpoint_{prev_episodes + episode + 1}")
            os.makedirs(checkpoint_dir, exist_ok=True)
            # Always use the original base_model_name for checkpoints as well
            checkpoint_base_model_name = re.sub(r'(_\d+Episodes)?$', '', base_model_name) if base_model_name is not None else base_model_name
            checkpoint_model_name = get_new_model_filename(checkpoint_base_model_name, prev_episodes + episode + 1)
            checkpoint_model_path = os.path.join(checkpoint_dir, checkpoint_model_name)
            torch.save(agent.model.state_dict(), checkpoint_model_path)
            print(f"Checkpoint saved to {checkpoint_model_path}")
            # Save metadata for checkpoint
            save_metadata(checkpoint_model_path, prev_episodes + episode + 1, dict(wandb.config))
            # Save running stats in summary
            summary = {
                'wandb_id': wandb_run.id,
                'wandb_config': dict(wandb.config),
                'last_model': checkpoint_model_path,
                'total_episodes': prev_episodes + episode + 1,
                'running_stats': running_stats
            }
            with open(os.path.join(RUN_DIR, 'summary.meta.json'), 'w') as f:
                json.dump(summary, f, indent=2)
                print(f"Updated summary.meta.json in {RUN_DIR}")
    # Save model with updated episode count
    total_episodes = prev_episodes + NUM_EPISODES
    # Always use the original base_model_name (no suffixes from previous runs)
    if args.resume and os.path.exists(RUN_DIR):
        # If resuming, ensure base_model_name is stripped of any _nEpisodes.pth
        if base_model_name is not None:
            base_model_name = re.sub(r'(_\d+Episodes)?$', '', base_model_name)
    new_model_name = get_new_model_filename(base_model_name, total_episodes)
    new_model_path = os.path.join(RUN_DIR, new_model_name)
    torch.save(agent.model.state_dict(), new_model_path)
    print(f"Model saved to {new_model_path}")
    # Save metadata
    save_metadata(new_model_path, total_episodes, dict(wandb.config))
    # Save running stats in summary
    summary = {
        'wandb_id': wandb_run.id,
        'wandb_config': dict(wandb.config),
        'last_model': new_model_path,
        'total_episodes': total_episodes,
        'running_stats': running_stats
    }
    with open(os.path.join(RUN_DIR, 'summary.meta.json'), 'w') as f:
        json.dump(summary, f, indent=2)
        print(f"Updated summary.meta.json in {RUN_DIR}")

    # Load the trained model for testing (optional, but good practice)
    test_agent_instance = RLAgent(1, epsilon=0.0, device=device)
    test_agent_instance.model.load_state_dict(torch.load(new_model_path, map_location=device))
    test_agent_instance.model.eval()

    # Test against RLRandomRiley
    print("Testing trained agent vs RLRandomRiley...")
    test_agent(test_agent_instance, RLRandomRiley(-1), episodes=48)
    # Test against PureRandomPlayer
    print("Testing trained agent vs PureRandomPlayer...")
    test_agent(test_agent_instance, PureRandomPlayer(-1), episodes=48)