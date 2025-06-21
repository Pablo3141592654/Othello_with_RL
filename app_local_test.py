import time
import streamlit as st
import firebase_admin
from firebase_admin import credentials, db, firestore
import numpy as np
from IPython.display import display
import streamlit.components.v1 as components
from game.board import Board
from game.player import HumanPlayer, GreedyGreta, MinimaxMax, RLRandomRiley, EdgesEdgar


# Initialize the app
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred)

# Get Firestore client
db = firestore.client()


PLAYER_FACTORIES = {
    "Human": lambda color: HumanPlayer(color),
    "Greedy Greta (simple AI)": lambda color: GreedyGreta(color),
    "Minimax Max (lookahead AI)": lambda color: MinimaxMax(color, depths=[
        st.session_state.get("black_depth", 2),
        st.session_state.get("red_depth", 2)
    ]),
    "RL Random Riley (random RL)": lambda color: RLRandomRiley(color),
    "Edges Edgar (edge control AI)": lambda color: EdgesEdgar(color, depths=[
        st.session_state.get("black_depth", 2),
        st.session_state.get("red_depth", 2)
    ], edge_value=st.session_state.get("edge_value", 2)),
}

def render_board(board):
    board_html = ""
    for i in range(8):
        for j in range(8):
            cell = board[i][j]
            label = "⚫" if cell == 1 else "🔴" if cell == -1 else "⠀"
            if not st.session_state.get("rerun", False):
                interaction_attr = f'onclick="sendClick({i}, {j})"'
            else:
                interaction_attr = ""
            board_html += f'<div class="othello-cell" {interaction_attr}>{label}</div>'

    clicked_id = st.session_state.clicked_id
    
    full_html = f"""
    <script src="https://www.gstatic.com/firebasejs/9.22.1/firebase-app-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/9.22.1/firebase-firestore-compat.js"></script>
    
    <div style="width: 100%; overflow-x: auto;">
        <div class="othello-grid">
            {board_html}
        </div>
    </div>
    
    <style>
        .othello-wrapper {{
            width: 100%;
            overflow-x: auto;
            display: flex;
            justify-content: center;
        }}
        .othello-grid {{
            display: grid;
            grid-template-columns: repeat(8, minmax(8vmin, 40px));
            gap: 2px;
        }}
        .othello-cell {{
            background: #116611;
            color: white;
            font-size: min(6vmin, 28px);
            border: 1px solid #222;
            display: flex;
            justify-content: center;
            align-items: center;
            aspect-ratio: 1 / 1;
            cursor: pointer;
            padding: 0;
            margin: 0;
        }}
    </style>


    <script>
        const clicked_id = "{clicked_id}"
        const firebaseConfig = {{
            apiKey: "AIzaSyAMKrO-E0kK4FgzBNNbAkbtH8Vdg4Ryx_U",
            authDomain: "othello-with-rl.firebaseapp.com",
            projectId: "othello-with-rl",
            storageBucket: "othello-with-rl.appspot.com",
            messagingSenderId: "988286445200",
            appId: "1:988286445200:web:76357a2280480fe6c81a15"
        }};

        if (!firebase.apps.length) {{
            firebase.initializeApp(firebaseConfig);
        }} else {{
            firebase.app();
        }}

        const db = firebase.firestore();

        function sendClick(i, j) {{
            console.log("Clicked cell:", i, j);
            db.collection("clicked_cell").doc("{clicked_id}").set({{
                cell: `${{i}},${{j}}`
            }})
            .then(() => {{
                console.log("Cell click recorded.");
                console.log("Clicked ID:", clicked_id);
            }})
            .catch((error) => {{
                console.error("Error writing document: ", error);
            }});
        }}
    </script>
    """
    components.html(full_html, height=400, scrolling=False)

    doc_ref = db.collection("clicked_cell").document(f"{st.session_state.clicked_id}")
    clicked = doc_ref.get() 
    data = clicked.to_dict() if clicked.exists else None
    if data["cell"] is not None:
        st.session_state.clicked_cell = data["cell"]
        reset_clicked_cell(False)
    else:
        st.write("No cell clicked yet.")
    return


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
        st.session_state.clicked_id = load_clicked_id()
        st.write("st.session_state.clicked_id: ", st.session_state.clicked_id)
        st.rerun()
    if st.button("Online"):
        board = Board().reset()
        occupied = load_occupied() # load how many games/players are occupied/online # occupied[1] alternates between -1 and 1!! # load_occupied creates a new game if needed
        st.session_state.game_id = occupied[0] # Get the first free game ID
        game_data = load_game_state(st.session_state.game_id)
        st.session_state.online_color = occupied[1] # if first in game, black, else red
        st.session_state.online = True
        st.session_state.page = "game"
        save_occupied(occupied[1], None)
        occupied = load_occupied() # Refresh occupied (changed one line ago)

        st.session_state.clicked_id = load_clicked_id() # before opponent joins to prevent issues
        shown = False # to show warning only once
        while occupied[1] == -1:
            if not shown == True:    
                st.warning("Waiting for an opponent to join...")
                shown = True
            occupied = load_occupied()
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

def save_occupied(player, game_id): # (change, remove)
    doc_ref = db.collection("occupied").document("1")
    occupied_data = doc_ref.get()
    occupied_data = occupied_data.to_dict()

    games = occupied_data["games"]
    if player == -1:
        games.append(st.session_state.game_id)
    try:
        games.remove(game_id)
    except ValueError:
        pass  # game_id wasn't in the list; that's okay
    doc_ref.set({
        'games': games
    }, merge=True)
    if player:
        doc_ref.set({
                'player': player
            }, merge=True) # merge=True to update only the player field
    return
        
    

def load_occupied():
    board_obj = Board()
    board_obj.reset()

    doc_ref = db.collection("occupied").document("1")
    occupied_data = doc_ref.get()
    occupied_data = occupied_data.to_dict()
    counter = 1
    game_id = 0
    while game_id == 0:
        if counter not in occupied_data["games"]: # if game_id is not occupied
            game_id = counter
        counter += 1

    player = occupied_data["player"] * (-1) # chose not occupied player

    game_doc_ref = db.collection("games").document(f"{game_id}") # check if game(game_id) exists
    game_doc = game_doc_ref.get()

    if not game_doc.exists: # if not create it
        # Create a new game document if it doesn't exist
        board_flat = np.zeros((8, 8), dtype=int).flatten().tolist()

        game_doc_ref.set({
            'board': board_flat,       # Now a flat array (list of 64 ints)
            'current_player': 1,
            'board_shape': [8, 8]      # Still store shape to rebuild
        })
        board_obj.reset() # initialize the new game - board
        save_game_state(board_obj.state, 1, game_id)
    return game_id, player

def load_clicked_id():
    doc_ref = db.collection("occupied").document("1")
    occupied_data = doc_ref.get()
    occupied_data = occupied_data.to_dict()
    clicked_array = occupied_data["clicked_id"]
    counter = 1
    clicked_id = 0
    while clicked_id == 0:
        if counter not in clicked_array: # if game_id is not occupied
            clicked_id = counter
        counter += 1

    clicked_doc_ref = db.collection("clicked_cell").document(f"{clicked_id}") # check if game(game_id) exists
    clicked_doc = clicked_doc_ref.get()

    if not clicked_doc.exists: # if not create it
        clicked_doc_ref.set({
            'cell': None
        })

    clicked_array.append(clicked_id) # add clicked_id to occupied
    doc_ref.set({
        'clicked_id': clicked_array
    }, merge=True) # set the clicked_id in the occupied document

    return clicked_id

def reset_clicked_cell(game_over):
    doc_ref = db.collection("clicked_cell").document(f"{st.session_state.clicked_id}")
    doc_ref.set({
        "cell": None
    })

    if game_over == True: # if game is over, remove clicked_id from occupied
        occupied_ref = db.collection("occupied").document("1")
        occupied_data = occupied_ref.get()
        occupied_data = occupied_data.to_dict()
        clicked = occupied_data["clicked_id"]
        clicked.remove(st.session_state.clicked_id) # remove clicked_id from occupied
        occupied_ref.set({
            "clicked_id": clicked
        }, merge=True)
    return

def end_game():
    board_obj = Board()
    board_obj.reset()

    board_obj.reset()  # Reset the board state
    if st.session_state.online:
        save_game_state(board_obj.state, 1, st.session_state.game_id)  # resets game(game_id)
        save_occupied(None, st.session_state.game_id)  # Reset occupied state
    reset_clicked_cell(True)
    st.session_state.clear()
    st.rerun()

def autoreset():
    if "time" not in st.session_state or st.session_state.time is None:
        st.session_state.time = time.time()  # initialize it
    if time.time() - st.session_state.time > 300:  # Reset after 5min
        st.warning("Game has been reset due to inactivity.")
        end_game()


def main():
    if "rerun" not in st.session_state:
            st.session_state.rerun = False
    

    # Add this at the top of main()
    ai_think_time = st.sidebar.slider(
        "AI thinking time (seconds)", min_value=0.0, max_value=3.0, value=0.5, step=0.1
    )
    st.session_state.ai_think_time = ai_think_time

    black_depth = st.sidebar.slider(
        "Black AI depth", min_value=1, max_value=5, value=2)
    st.session_state.black_depth = black_depth

    red_depth = st.sidebar.slider(
        "Red AI depth", min_value=1, max_value=5, value=2)
    st.session_state.red_depth = red_depth

    edge_value = st.sidebar.slider(
        "Edge value for Edges Edgar", min_value=0, max_value=6, value=2)
    st.session_state.edge_value = edge_value

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

    if "clicked_id" not in st.session_state:
        st.session_state.clicked_id = 0


    current_player = st.session_state.players[st.session_state.current_player_idx]
    board = board_obj.state

    st.title("Othello Game")
    if st.button("Restart/Exit Game"):
        end_game() # session_state, firebase, etc.

    black_count, red_count = board_obj.count_pieces()
    st.write(f"**⚫ Black: {black_count}** | **🔴 Red: {red_count}**")
    st.write(f"### Current Turn: {'⚫' if current_player.color == 1 else '🔴'}")
    if st.session_state.online:
        st.write("Online mode, you are playing as " + ("⚫" if st.session_state.online_color == 1 else "🔴"))
        board_obj.state = load_game_state(st.session_state.game_id)[0]  # Load game state from Firestore
    render_board(board_obj.state)

    if not st.session_state.rerun:
        # --- GAME OVER CHECK: If neither player can move, announce winner and stop ---
        if not board_obj.has_valid_move(current_player.color):
            if not board_obj.has_valid_move(-current_player.color):
                if black_count > red_count:
                    st.success("Game ended. ⚫ Black won!")
                elif red_count > black_count:
                    st.success("Game ended. 🔴 Red won!")
                else:
                    st.info("Game ended. It's a draw!")
                time.sleep(50)
                end_game()
            else:
                st.info(f"No valid moves for {'⚫' if current_player.color == 1 else '🔴'}. Passing turn.")
                st.session_state.current_player_idx = 1 - st.session_state.current_player_idx
                st.rerun()

        if not st.session_state.online and (
            not isinstance(st.session_state.players[0], HumanPlayer) or
            not isinstance(st.session_state.players[1], HumanPlayer)
        ):           # AI move handling
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

        if not st.session_state.online or current_player.color == st.session_state.online_color:
            if "clicked_cell" in st.session_state and st.session_state.clicked_cell:
                i_str, j_str = st.session_state.clicked_cell.split(",")
                i, j = int(i_str), int(j_str)
                st.session_state.clicked_cell = None # reset clicked cell after processing
                if board_obj.apply_move(current_player.color, i, j):
                    st.session_state.current_player_idx = 1 - st.session_state.current_player_idx
                    current_player = st.session_state.players[st.session_state.current_player_idx] # update before saving the color in firebase
                    if st.session_state.online:
                        save_game_state(board_obj.state, current_player.color, st.session_state.game_id)
                    st.session_state.time = None # reset time to avoid autoreset
                    st.rerun()
                else:
                    if st.session_state != None:
                        st.warning("Invalid move. You need to outflank an opponent's piece.")
                        st.rerun()
                    autoreset()
                    st.rerun()
            else:
                st.rerun() # get the clicked cell from firebase
        if st.session_state.online and current_player.color != st.session_state.online_color:
            st.session_state.rerun = True
            st.rerun()
    else:
        st.warning("Waiting for opponent's move...")
        autoreset()
        game_data = load_game_state(st.session_state.game_id)
        if game_data[1] == st.session_state.online_color:
            st.session_state.board_obj.state = game_data[0] # needs to be session_state cause board_obj is defined in if clause
            st.session_state.current_player_idx = 1 - st.session_state.current_player_idx
            st.session_state.rerun = False
            st.rerun()
        st.session_state.rerun = True
        st.rerun()

if __name__ == "__main__":
    main()
