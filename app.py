import streamlit as st
from game.board import Board
from game.player import HumanPlayer

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
    st.write("Select a game mode to start:")
    if st.button("Human vs Human"):
        st.session_state.page = "game"
        st.rerun()
    # Add more modes here in the future

def main():
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

    if "clicked_cell" in st.session_state and st.session_state.clicked_cell:
        i, j = st.session_state.clicked_cell
        st.session_state.clicked_cell = None
        if board_obj.apply_move(current_player.color, i, j):
            st.session_state.current_player_idx = 1 - st.session_state.current_player_idx
            st.rerun()
        else:
            st.warning("Invalid move. You need to outflank an opponent's piece.")

    # Game over check
    if not board_obj.has_valid_move(1) and not board_obj.has_valid_move(-1):
        if black_count > red_count:
            st.success("Game ended. ⚫ Black won!")
        elif red_count > black_count:
            st.success("Game ended. 🔴 Red won!")
        else:
            st.info("Game ended. It's a draw!")

if __name__ == "__main__":
    main()
