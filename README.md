# Othello\_with\_RL

A modern, interactive Othello/Reversi game built with [Streamlit](https://streamlit.io/) for the web, featuring multiple play modes and a roadmap for advanced AI opponents—including a reinforcement learning (RL) agent.

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
   git clone https://github.com/yourusername/Othello_with_RL.git
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

### AI Agent Code (from `game/player.py`)

```python
# ... (same code block as before)
```

---

### Board Logic (from `game/board.py`)

```python
# ... (same code block as before)
```

---

## 📅 Roadmap / To-Do

-

---

## 📄 Code Structure

```
# ... (same structure block)
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

