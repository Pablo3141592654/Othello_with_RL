import time
import streamlit as st
from game.board import Board
from game.player import HumanPlayer, GreedyGreta, MinimaxMax, RLRandomRiley

PLAYER_TYPES = {
    "Human": HumanPlayer,
    "Greedy Greta (simple AI)": GreedyGreta,
    "Minimax Max (lookahead AI)": MinimaxMax,
    "RL Random Riley (random RL)": RLRandomRiley,
}

def render_board(board):
    st.markdown("""
        <style>
        .othello-board-bg {
            background: #116611;
            padding: 8px;
            border-radius: 8px;
            display: inline-block;
        }
        div[data-testid="stHorizontalBlock"] {
            gap: 0 !important;
        }
        div[data-testid="column"] {
            padding: 0 !important;
            margin: 0 !important;
        }
        button[kind="secondary"] {
            min-width: 56px !important;
            min-height: 56px !important;
            width: 56px !important;
            height: 56px !important;
            font-size: 3.2rem !important;
            margin: 0 !important;
            padding: 0 !important;
            border-radius: 0 !important;
            border: 1.5px solid #222 !important;
            background: transparent !important;
            line-height: 1 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="othello-board-bg">', unsafe_allow_html=True)
    for i in range(8):
        cols = st.columns(8, gap="small")  # gap will be overridden by CSS
        for j in range(8):
            cell = board[i][j]
            if cell == 1:
                label = "⚫"
            elif cell == -1:
                label = "🔴"
            else:
                label = ""
            if cols[j].button(label, key=f"{i}-{j}"):
                st.session_state.clicked_cell = (i, j)
    st.markdown('</div>', unsafe_allow_html=True)

def select_buttons():
    st.title("Othello with RL")
    st.write("Choose a player for each color:")

    black_choice = st.selectbox("Black (⚫)", list(PLAYER_TYPES.keys()), key="black_player")
    red_choice = st.selectbox("Red (🔴)", list(PLAYER_TYPES.keys()), key="red_player")

    if st.button("Start Game"):
        st.session_state.page = "game"
        st.session_state.players = [
            PLAYER_TYPES[black_choice](1),
            PLAYER_TYPES[red_choice](-1)
        ]
        st.session_state.current_player_idx = 0
        st.session_state.board_obj = Board()
        st.rerun()

def main():
    # Add this at the top of main()
    ai_think_time = st.sidebar.slider(
        "AI thinking time (seconds)", min_value=0.0, max_value=3.0, value=0.5, step=0.1
    )
    st.session_state.ai_think_time = ai_think_time

    if "page" not in st.session_state:
        st.session_state.page = "select"
    if st.session_state.page == "select":
        select_buttons()
        return

    if "board_obj" not in st.session_state:
        st.session_state.board_obj = Board()
    board_obj = st.session_state.board_obj

    if "players" not in st.session_state:
        st.session_state.players = [HumanPlayer(1), HumanPlayer(-1)]

    if "current_player_idx" not in st.session_state:
        st.session_state.current_player_idx = 0

    current_player = st.session_state.players[st.session_state.current_player_idx]
    board = board_obj.state

    st.title("Othello Game")
    if st.button("Restart Game"):
        st.session_state.clear()
        st.rerun()

    black_count, red_count = board_obj.count_pieces()
    st.write(f"**⚫ Black: {black_count}** | **🔴 Red: {red_count}**")
    st.write(f"### Current Turn: {'⚫' if current_player.color == 1 else '🔴'}")

    render_board(board)

    # --- GAME OVER CHECK: If neither player can move, announce winner and stop ---
    if not board_obj.has_valid_move(1) and not board_obj.has_valid_move(-1):
        if black_count > red_count:
            st.success("Game ended. ⚫ Black won!")
        elif red_count > black_count:
            st.success("Game ended. 🔴 Red won!")
        else:
            st.info("Game ended. It's a draw!")
        st.stop()

    # AI move handling
    if not isinstance(current_player, HumanPlayer):
        time.sleep(st.session_state.ai_think_time)
        move = current_player.get_move(board_obj)
        if move:
            board_obj.apply_move(current_player.color, *move)
            st.session_state.current_player_idx = 1 - st.session_state.current_player_idx
            st.rerun()
        else:
            st.warning("No valid moves for AI. Passing turn.")
            st.session_state.current_player_idx = 1 - st.session_state.current_player_idx
            st.rerun()

    if "clicked_cell" in st.session_state and st.session_state.clicked_cell:
        i, j = st.session_state.clicked_cell
        st.session_state.clicked_cell = None
        if board_obj.apply_move(current_player.color, i, j):
            st.session_state.current_player_idx = 1 - st.session_state.current_player_idx
            st.rerun()
        else:
            st.warning("Invalid move. You need to outflank an opponent's piece.")

    # Check for valid moves for current player
    if not board_obj.has_valid_move(current_player.color):
        # If the other player also has no moves, game over
        other_color = -current_player.color
        if not board_obj.has_valid_move(other_color):
            black_count, red_count = board_obj.count_pieces()
            if black_count > red_count:
                st.success("Game ended. ⚫ Black won!")
            elif red_count > black_count:
                st.success("Game ended. 🔴 Red won!")
            else:
                st.info("Game ended. It's a draw!")
            st.stop()
        else:
            st.info(f"No valid moves for {'⚫' if current_player.color == 1 else '🔴'}. Passing turn.")
            st.session_state.current_player_idx = 1 - st.session_state.current_player_idx
            st.rerun()

if __name__ == "__main__":
    main()
