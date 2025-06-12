# Othello_with_RL

A modern, interactive Othello/Reversi game built with [Streamlit](https://streamlit.io/) for the web, featuring multiple play modes and a roadmap for advanced AI opponents—including a reinforcement learning (RL) agent.

It is also online accessible under https://othellowithrl-uv9hqcazqfofjwnsfbnrzx.streamlit.app/

---

## 🎮 Features

- **Play Othello in your browser**: No installation required for users—just run and play!
- **Game Modes**:
  - Player vs Player (local)
  - Player vs AI (basic AI, more coming soon)
  - AI vs Player
  - AI vs AI
  - Online Multiplayer (planned)
- **Interactive UI**: Clickable board, real-time updates, and a sidebar chat assistant.
- **Score Tracking**: Live piece counts and turn indicators.
- **Restart & State Management**: Easily restart games and manage session state.
- **(Planned) Save/Load Online Games**: Firebase integration for online multiplayer.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- [pip](https://pip.pypa.io/en/stable/)

### Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/yourusername/Othello_with_RL.git
   cd Othello_with_RL
   ```

2. **Install dependencies:**
   ```sh
   pip install streamlit numpy
   ```

   *(For online mode: `firebase_admin` will be required in the future.)*

3. **Run the app:**
   ```sh
   streamlit run app.py
   ```

4. **Open your browser:**  
   Visit the local URL provided by Streamlit (usually http://localhost:8501).

---

## 🛠️ Tech Stack

- **Frontend/UI**: [Streamlit](https://streamlit.io/)
- **Backend/Game Logic**: Python (NumPy for board state)
- **State Management**: Streamlit session state
- **(Planned) Online Multiplayer**: Firebase Realtime Database

---

## 🤖 AI & Future Plans

- **Current AI**: Simple rule-based agent (chooses the first valid move).
- **Planned AI Agents**:
  - **Jonas**: Reinforcement Learning (RL) agent using modern RL techniques.
  - **Pablo**: Classic AI agent (e.g., Minimax, Alpha-Beta pruning, or heuristic-based).
- **Online Multiplayer**: Firebase integration for real-time games.
- **Improved UI/UX**: Enhanced chat assistant, move hints, and more.

---

## 📝 To-Do

- [ ] Jonas: Implement RL-based Othello agent.
- [ ] Pablo: Implement classic AI agent (Minimax/Alpha-Beta).
- [ ] Complete Firebase integration for online play.
- [ ] Add move suggestions and hints.
- [ ] Improve chat assistant with more interactivity.
- [ ] Add tests and modularize game logic into [`game/`](game/).

---

## 👥 Contributing

Contributions are welcome!  
If you'd like to add features, fix bugs, or write your own AI agent, please open an issue or submit a pull request.

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.

---

## 🙋 Authors

- **Pablo Petersen**: Game logic, multiplayer interface, classic AI (planned)
- **Jonas Petersen**: RL agent (planned)

---

## 📢 Acknowledgements

- CS50 Final Project
- Streamlit for rapid prototyping

---

## 🧩 Code Structure & Logic

The project is organized for clarity and extensibility:

```
Othello_with_RL/
│
├── app.py                # Main Streamlit app: UI, game loop, and session state
├── cache.py              # (Legacy) Streamlit cache clearing
├── game/
│   ├── __init__.py
│   ├── board.py          # (Planned) Board logic and utilities
│   ├── player.py         # (Planned) Player and AI agent classes
│   └── utils.py          # (Planned) Helper functions
├── README.md
├── LICENSE
└── .gitignore
```

### Main Logic (`app.py`)

- **UI & Game Loop:**  
  Handles the Streamlit interface, game state, and user interactions.  
  - `render_board`: Draws the board and handles cell clicks.
  - `initialize_board`: Sets up the initial Othello board.
  - `is_legal_move`: Checks and applies legal moves.
  - `ai_move`: Simple AI (currently picks the first valid move).
  - `select_buttons`: Lets users pick the game mode.
  - `main`: Orchestrates the game flow, including AI turns and session state.

- **Session State:**  
  Used to track the board, turn count, chat log, and game mode across reruns.

- **Chat Assistant:**  
  Sidebar chat log for move feedback and game status.

- **Online Multiplayer (Planned):**  
  Placeholder functions for saving/loading game state with Firebase.

### Modular Game Logic (`game/`)

- **`game/board.py`**  
  *Planned*: Move board-related logic (e.g., move validation, board updates) here for better separation.

- **`game/player.py`**  
  *Planned*: Implement player classes, including:
    - Human player
    - Classic AI (Minimax/Alpha-Beta, heuristics) — *Pablo's task*
    - RL agent — *Jonas's task*

- **`game/utils.py`**  
  *Planned*: Utility functions (e.g., move generation, scoring, serialization).

### Where to Add New Features

- **Advanced AI Agents:**  
  - RL agent: Implement in `game/player.py` (Jonas).
  - Classic AI: Implement in `game/player.py` (Pablo).
  - Integrate these into `app.py`'s AI move logic.

- **Online Multiplayer:**  
  - Complete Firebase integration in `app.py` (see commented code).
  - Add user authentication and real-time updates.

- **UI/UX Improvements:**  
  - Enhance chat assistant in `app.py`.
  - Add move suggestions/hints (could use `game/utils.py`).

- **Testing & Modularization:**  
  - Move board and player logic from `app.py` to `game/`.
  - Add unit tests for core logic (suggested: `tests/` folder).

---

## 💡 Future Improvement Ideas

- **AI Difficulty Levels:**  
  Allow users to select between different AI strategies and difficulties.

- **Game Analysis:**  
  Add move history, undo/redo, and post-game analysis.

- **Mobile-Friendly UI:**  
  Improve layout for smaller screens.

- **User Profiles & Leaderboards:**  
  Track stats and rankings for online play.

---

*See the code comments and [`game/`](game/) folder for more details and extension points!*

---

Enjoy playing Othello, and feel free to contribute or suggest features!
