# Othello\_with\_RL

A modern, interactive Othello/Reversi game built with [Streamlit](https://streamlit.io/) for the web, featuring multiple AI opponents and a roadmap for a reinforcement learning (RL) agent.

It is also online accessible under [https://othellowithrl-uv9hqcazqfofjwnsfbnrzx.streamlit.app/](https://othellowithrl-uv9hqcazqfofjwnsfbnrzx.streamlit.app/)

---

## 🎮 Features

- **Play Othello in your browser or on mobile**: Fully responsive and touch-compatible.
- **Game Modes**:
  - Choose any combination of AI or Player for each side (via selectboxes)
  - Fully working Online Multiplayer with real-time sync (via Firebase)
- **Interactive UI**: Clickable board, real-time updates, and fully mobile-compatible via JS+Firebase integration.
- **Score Tracking**: Live piece counts and turn indicators.
- **Restart & State Management**: Easily restart games and manage session state.
- **Flexible AI Support**: Mix-and-match any agent types—including custom edge strategies, Minimax, and RL placeholder.
- **Sidebar Controls**: Adjust AI difficulty, edge/border values, and AI thinking time.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- [pip](https://pip.pypa.io/en/stable/)

### Installation (for Development Only)

If you want to develop or test the app locally:

1. **Clone the repository:**

   ```sh
   git clone https://github.com/Pablo3141592654/Othello_with_RL.git
   cd Othello_with_RL
   ```

2. **Install dependencies:**

   ```sh
   pip install -r requirements.txt
   ```

3. **Create **``

   If you're running in **Production Mode (not Streamlit Cloud)**, you must:

   - Set up your own Firebase project.
   - Download the private key from Firebase.
   - Save it as `firebase_key.json` and load it manually.
   - Modify the Firebase config in `render_board()` (JavaScript block) to use your Firebase project.

4. **Run the app (Development mode):**

   ```sh
   streamlit run app_local_test.py
   ```

5. **Visit the app:** Open the local URL provided by Streamlit (usually [http://localhost:8501](http://localhost:8501)).

---

## 🧪 Local Development with `app_local_test.py`

If you're running the app **locally from a terminal (e.g., VS Code)** and can't access `st.secrets` (like on Streamlit Cloud), use the fallback script:

```sh
streamlit run app_local_test.py
```

This lets you test all game features, AI, and Firebase logic without needing cloud secrets.

---

## 🛠️ Tech Stack

- **Frontend/UI**: [Streamlit](https://streamlit.io/) + JavaScript integration via Firebase for interactivity
- **Backend/Game Logic**: Python (NumPy, modular design)
- **AI Agents**: Classic heuristics (Minimax, Greedy, Edge-based), and placeholder RL agent
- **Realtime Online Sync**: Firebase Firestore + Firestore JS SDK
- **State Management**: Streamlit session state, Firebase for multiplayer sync
- **Mobile Compatibility**: Fully functional on mobile via JS+Streamlit-Firebase communication

---

## 🤖 AI & Future Plans

- **Current Agents**:
  - `HumanPlayer`: Local user via UI
  - `GreedyGreta`: Picks the first available move
  - `MinimaxMax`: Classical Minimax algorithm with lookahead
  - `EdgesEdgar`: Minimax variant that prioritizes edge/border control
  - `RLRandomRiley`: Picks a random legal move (RL placeholder)


---

## 📅 Roadmap / To-Do

-

---

## 📄 Code Structure

```
# ... 📁 Othello_with_RL/
│
├── app.py                   # Main Streamlit app for production/deployment
├── app_local_test.py        # Local dev version (bypasses streamlit secrets)
│
├── game/
│   ├── __init__.py
│   ├── board.py             # Core game logic (valid moves, scoring, etc.)
│   └── player.py            # Player base class + AI bots (Minimax, Edge, etc.)
│
├── requirements.txt         # Python dependencies
├── README.md                # Project documentation
└── .streamlit/
    └── secrets.toml         # (Used on Streamlit Cloud for Firebase config)
```

---

## 📑 Main App Logic Overview (`app.py`)

- **UI Rendering:** `render_board` builds an interactive grid with Firebase-based JS listeners.
- **Firebase Integration:** Read/write board state and clicks via Firestore.
- **Game Flow:**
  - Game setup via `select_buttons()` (Selectboxes for each side)
  - Real-time turn handling with online/offline modes
  - Win condition detection, auto-reset on timeout
- **Session Management:**
  - Track clicked cell, board state, active player
  - `st.session_state` used for local logic and caching

---

## 🤖 RL Agent Architecture & Implementation

**Overview:**
The RL agent uses Deep Q-Network (DQN) reinforcement learning to learn Othello strategy through self-play and curriculum learning. The agent learns by estimating Q-values (action-values) for each possible move given a board state.

**Architecture:**
- **Neural Network**: Convolutional neural network with 2 conv layers (64→128 channels) + fully connected layers
- **Input**: 8×8×2 tensor (2 channels: current player's pieces + opponent's pieces)  
- **Output**: 64 Q-values (one for each board position)
- **Target Network**: Separate target network updated periodically for stable training

**Design Choices & Process:**
- **2-Channel Input**: Uses player-relative encoding (own pieces, opponent pieces) rather than absolute colors. This makes the agent color-agnostic and improves generalization.
- **CNN Architecture**: Convolutional layers capture spatial patterns (like edge control, clustering) crucial in Othello strategy.
- **Hyperparameters**: Learning rate 1e-4, batch size 32, replay buffer 10k experiences, target network update every 100 steps, ε=0.1 exploration.
- **Reward Design**: Experimented with reward shaping (piece differential, corner bonuses) vs pure win/loss rewards. Currently uses minimal shaping to avoid bias.
- **Training Philosophy**: Curriculum learning from simple (random) to complex (self-play) opponents to build robust strategies progressively.

**Training Process:**
1. **Curriculum Learning**: Progressive difficulty opponents
   - Phase 1: Random moves (RLRandomRiley) - learn basic rules
   - Phase 2: Minimax AI (depth 2) - learn strategic play  
   - Phase 3: Self-play - refine strategy against itself
2. **Experience Replay**: Store and sample past experiences for training stability
3. **ε-greedy Exploration**: Balance exploration vs exploitation during training
4. **Reward Shaping**: Immediate rewards for piece differential, large rewards for wins/losses

**Key Components:**
- `rl_agent/rl_agent.py` - Main DQN agent implementation
- `rl_agent/q_network.py` - Neural network architecture  
- `rl_agent/train_rl_agent.py` - Training script with curriculum learning
- `rl_agent/utils.py` - Board state preprocessing utilities
- **Monitoring**: Weights & Biases integration for training metrics and visualization

**Usage:**
```bash
python rl_agent/train_rl_agent.py --episodes 1000
```

---

## ⚠️ RL Agent: Known Issues & Next Steps

**Current Status:**
- The DQN-based RL agent for Othello is implemented and trains with detailed diagnostics (see `rl_agent/train_rl_agent.py`).
- Training is tracked with Weights & Biases (wandb).

**Known Issues:**
- Q-values and losses explode after ~200 episodes in long training runs (see wandb charts).
- This leads to instability and poor agent performance (does not outperform random/heuristic baselines).

**Suspected Causes:**
- Learning rate may still be too high.
- Overestimation bias in vanilla DQN (Double DQN may help).
- Lack of reward normalization (reward clipping is used).
- Target network update frequency or batch size may be suboptimal.
- Network architecture or initialization may contribute.

**Next Steps:**
- Lower the learning rate further.
- Implement Double DQN.
- Consider Q-value clipping or reward normalization.
- Review target network update frequency and batch size.
- Explore architectural changes if needed.

See `rl_agent/DQN_issues_and_next_steps.md` for a detailed summary and action plan.

---

## 👥 Authors

- **Pablo Petersen**: Game logic, UI, Firebase integration, classic AI (Minimax, Edges)
- **Jonas Petersen**: Reinforcement Learning agent (planned)

---

## 📃 License

MIT License. See [LICENSE](LICENSE) for details.

---

## 📢 Acknowledgements

- Harvard CS50 Final Project
- Streamlit for rapid prototyping
- JS for cleaner UI
- Firebase for simple real-time sync

---

## 🤔 Why Othello?

Othello provides a compact yet rich domain for AI experimentation:

- Fast to simulate
- Balanced randomness vs determinism
- Clear win/loss condition
- Strategic yet intuitive for users

This project aims to bring together usability (via Streamlit) and AI learning (RL + heuristics) in an accessible way.

Enjoy playing, exploring, and contributing!

