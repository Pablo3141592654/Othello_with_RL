import time
import streamlit as st
import firebase_admin
from firebase_admin import credentials, db, firestore
import numpy as np
from game.board import Board
from game.player import HumanPlayer, GreedyGreta, MinimaxMax, RLRandomRiley

# Load credentials
cred = credentials.Certificate("firebase_key.json")

# Initialize the app
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

# Get Firestore client
db = firestore.client()

# Example: Access your data
doc_ref = db.collection("games").document("1")
doc = doc_ref.get()
if doc.exists:
    print(doc.to_dict())

PLAYER_FACTORIES = {
    "Human": lambda color: HumanPlayer(color),
    "Greedy Greta (simple AI)": lambda color: GreedyGreta(color),
    "Minimax Max (lookahead AI)": lambda color: MinimaxMax(color, depths=[
        st.session_state.get("black_depth", 2),
        st.session_state.get("red_depth", 2)
    ]),
    "RL Random Riley (random RL)": lambda color: RLRandomRiley(color),
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

    black_choice = st.selectbox("Black (⚫)", list(PLAYER_FACTORIES.keys()), key="black_player")
    red_choice = st.selectbox("Red (🔴)", list(PLAYER_FACTORIES.keys()), key="red_player")

    if st.button("Start Game"):
        st.session_state.page = "game"
        st.session_state.players = [
            PLAYER_FACTORIES[black_choice](1),
            PLAYER_FACTORIES[red_choice](-1)
        ]
        st.session_state.current_player_idx = 0
        st.session_state.board_obj = Board()
        st.rerun()
    if st.button("Online"):
        board = Board().reset()
        game_data = load_game_state(1)
        st.session_state.online_color = game_data[1]  # Set online color based on loaded game state
        st.session_state.online = True
        st.session_state.page = "game"
        st.session_state.players = [
            HumanPlayer(game_data[1]),  # Player color based on loaded game state
            HumanPlayer(-game_data[1])  # Opponent color is the opposite
        ]
        st.rerun()

def save_game_state(board, current_player, game_id):
    # Flatten 2D board into a list of lists (Firestore doesn't support nested arrays beyond 1 level)
    board_list = board.tolist()
    if isinstance(board_list[0], list):
        board_list = [cell for row in board_list for cell in row]  # Flatten to 1D list

    game_data = {
    'board': board_list,
    'current_player': current_player,
    'board_shape': board.shape  # Save shape to reconstruct later
    }


    doc_ref = db.collection("games").document(str(game_id))
    doc_ref.set(game_data)
    print(f"Saved game_data: {game_data}")

def load_game_state(game_id):
    doc_ref = db.collection("games").document(str(game_id))
    game_data = doc_ref.get()
    if game_data.exists:
        data = game_data.to_dict()
        shape = tuple(data.get('board_shape', (8, 8)))  # Default to 8x8 if shape is missing
        board = np.array(data['board']).reshape(shape)
        current_player = data['current_player']
        return board, current_player

    # Fallback: return a fresh board and default player
    board = Board().reset()
    return board, 1

def main():
    # Add this at the top of main()
    ai_think_time = st.sidebar.slider(
        "AI thinking time (seconds)", min_value=0.0, max_value=3.0, value=0.5, step=0.1
    )
    st.session_state.ai_think_time = ai_think_time

    black_depth= st.sidebar.slider(
        "Black AI depth", min_value=1, max_value=5, value=2)
    st.session_state.black_depth = black_depth

    red_depth = st.sidebar.slider(
        "Red AI depth", min_value=1, max_value=5, value=2)
    st.session_state.red_depth = red_depth

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
    
    if "online" not in st.session_state:
        st.session_state.online = False

    if "rerun" not in st.session_state:
        st.session_state.rerun = False

    if not st.session_state.rerun:
        current_player = st.session_state.players[st.session_state.current_player_idx]
        board = board_obj.state

        st.title("Othello Game")
        if st.button("Restart Game"):
            board_obj.reset()  # Reset the board state
            save_game_state(board_obj.state, 1, 1)  # TODO Replace with actual game ID logic
            st.session_state.clear()
            st.rerun()

        black_count, red_count = board_obj.count_pieces()
        st.write(f"**⚫ Black: {black_count}** | **🔴 Red: {red_count}**")
        st.write(f"### Current Turn: {'⚫' if current_player.color == 1 else '🔴'}")
        if st.session_state.online:
            st.write("Online mode, you are playing as " + ("⚫" if st.session_state.online_color == 1 else "🔴"))
            board_obj.state = load_game_state(1)[0]  # Load game state from Firestore
        render_board(board_obj.state)

        # --- GAME OVER CHECK: If neither player can move, announce winner and stop ---
        if not board_obj.has_valid_move(current_player.color):
            if not board_obj.has_valid_move(-current_player.color):
                if black_count > red_count:
                    st.success("Game ended. ⚫ Black won!")
                elif red_count > black_count:
                    st.success("Game ended. 🔴 Red won!")
                else:
                    st.info("Game ended. It's a draw!")
                st.write("Game ended. Please close the tab or restart the game.")
                st.session_state.clear()
                board_obj.reset()  # Reset the board state
                save_game_state(board_obj.state, 1, 1)  # Replace with actual game ID logic
                st.stop()
            else:
                st.info(f"No valid moves for {'⚫' if current_player.color == 1 else '🔴'}. Passing turn.")
                st.session_state.current_player_idx = 1 - st.session_state.current_player_idx
                st.rerun()

        if not st.session_state.online:  # Only handle AI moves if not online
            # AI move handling
            if not isinstance(current_player, HumanPlayer): # And not online
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

        if not st.session_state.online or current_player.color == st.session_state.online_color:
            if "clicked_cell" in st.session_state and st.session_state.clicked_cell:
                i, j = st.session_state.clicked_cell
                st.session_state.clicked_cell = None
                if board_obj.apply_move(current_player.color, i, j):
                    st.session_state.current_player_idx = 1 - st.session_state.current_player_idx
                    current_player = st.session_state.players[st.session_state.current_player_idx] # update before saving the color in firebase
                    if st.session_state.online:
                        save_game_state(board_obj.state, current_player.color, 1)  # Replace with actual game ID logic
                    st.rerun()
                else:
                    st.warning("Invalid move. You need to outflank an opponent's piece.")
        if st.session_state.online and current_player.color != st.session_state.online_color:
            st.warning("Waiting for your opponent to make a move...")
            st.session_state.rerun = True
            st.rerun()
    else:
        st.warning("Waiting for opponent's move...")
        time.sleep(5)  # wait for opponent
        game_data = load_game_state(1) # Id is only 1 for testing now
        if game_data[1] == st.session_state.online_color:
            board_obj.state = game_data[0]
            st.session_state.current_player_idx = 1 - st.session_state.current_player_idx
            st.session_state.rerun = False
            st.rerun()
        st.session_state.rerun = True
        st.rerun()

if __name__ == "__main__":
    main()