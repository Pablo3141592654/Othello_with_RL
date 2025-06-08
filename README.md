# Othello_with_RL

A modern, interactive Othello/Reversi game built with [Streamlit](https://streamlit.io/) for the web, featuring multiple play modes and a roadmap for advanced AI opponents—including a reinforcement learning (RL) agent.

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

Enjoy playing Othello, and feel free to contribute or suggest features!
