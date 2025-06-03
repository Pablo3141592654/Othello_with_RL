import streamlit as st
import numpy as np
import copy
import time
# import firebase_admin # TODO
# from firebase_admin import credentials, db
# # Initialize Firebase Admin SDK
# cred = credentials.Certificate("path/to/your/serviceAccountKey.json")  # TODO Path to your Firebase service account key
# firebase_admin.initialize_app(cred, {
#     'databaseURL': 'https://YOUR_PROJECT_ID.firebaseio.com/'  # TODO Your database URL
# })

# Define a function to render the Othello board
def render_board(board):
    st.write("### Othello Board")
    if "chat_log" not in st.session_state:
        st.session_state.chat_log = []
        st.session_state.chat_log.append("Welcome to Othello, make your move!")

    # Display chat assistant in the sidebar
    with st.sidebar.expander("💬 Chat Assistant", expanded=True):
        for msg in st.session_state.chat_log:
            st.write(f"**Chat Assistant:** {msg}")

    for i, row in enumerate(board):
        cols = st.columns(len(row))
        for j, col in enumerate(cols):
            key = f'{i}-{j}'

            # Choose symbol based on board value
            if row[j] == 1:
                symbol = '⚫'
            elif row[j] == -1:
                symbol = '🔴'
            else:
                symbol = '⬜'

            if col.button(symbol, key=key):
                st.session_state.clicked_cell = (i, j)
                st.rerun()  # Rerun the app to update the board
                

# Initial empty board setup
def initialize_board():
    # Set up the initial 8x8 board with 0s
    board = np.zeros((8, 8), dtype=int)
    # Set up initial 4 pieces in the center
    board[3][3], board[4][4] = 1, 1  # Player 1's pieces (black)
    board[3][4], board[4][3] = -1, -1  # Player 2's pieces (white)
    return board

def is_legal_move(board, player, row, col):
    """Check if placing a piece at (row, col) is a legal move for the player."""
    if board[row][col] != 0:
        return False

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    legal = False
    modified_board = copy.deepcopy(board) # Work with a copy to avoid modifying the original board
    helper = copy.deepcopy(board) # Helper to reset the modified board if needed
    for dr, dc in directions:
        found_opponent = False
        r, c = row + dr, col + dc
        while 0 <= r < 8 and 0 <= c < 8:
            if board[r][c] == -player:
                found_opponent = True
                if 0 <= r + dr < 8 and 0 <= c + dc < 8:  # Check if the next cell is within center
                    modified_board[r][c] = player # Temporarily mark opponent's piece as player's
                else:
                    modified_board = copy.deepcopy(helper) # Reset to original board if out of bounds
            elif board[r][c] == player:
                if found_opponent:
                    helper = copy.deepcopy(modified_board)  # Modify the real board to reflect the changes
                    legal = True
                break
            else:
                modified_board = copy.deepcopy(helper)
                break
            r += dr
            c += dc
    if legal:
        modified_board[row][col] = player # Place the player's piece on the copy
        return modified_board
    else:
        return False


def count_pieces(board):
    """Count the number of pieces for each player."""
    black_count = np.sum(board == 1)
    red_count = np.sum(board == -1)
    return black_count, red_count

def chat_assistant(message, ai_ignore):
    """Display a message in the chat assistant area."""
    if 'chat_log' not in st.session_state:
        st.session_state.chat_log = []
    if not st.session_state.ai or ai_ignore == True: # no need to display, if AI made a valid move except exceptions
        st.session_state.chat_log.append(message)
        st.session_state.chat_log = st.session_state.chat_log[-2:]  # Keep only the last 1 message



def has_valid_move(board, player):
    """Check if the player has any valid moves."""
    for row in range(8):
        for col in range(8):
            if is_legal_move(board, player, row, col) is not False:
                return True
    return False

def change_board(board):
    # Initialize session state if not already done
    if "clicked_cell" not in st.session_state:
        st.session_state.clicked_cell = None
    if 'count' not in st.session_state:
        st.session_state.count = 1
    if 'board' not in st.session_state:
        st.session_state.board = initialize_board()
    if "rerun" not in st.session_state:
        st.session_state.rerun = False
    
    board = st.session_state.board
    current_player = 1 if st.session_state.count % 2 == 1 else -1
    st.write(f"### Current Turn: {'⚫' if current_player == 1 else '🔴'}")

    # Display player scores
    black_count, red_count = count_pieces(board)
    st.write(f"**⚫ Black: {black_count}** | **🔴 Red: {red_count}**")

    # if st.session_state.rerun == False: # should check only once a turn  PROBLEM if Ai ends the game
    # Check if neither player has a valid move
    if not has_valid_move(board, 1) and not has_valid_move(board, -1):
        if black_count > red_count:
            chat_assistant("Game ended. ⚫ Black won!", True)
        elif red_count > black_count:
            chat_assistant("Game ended. 🔴 Red won!", True)
        else:
            chat_assistant("Game ended. It's a draw!", True)
        st.session_state.game_over = True
        return board


    # Check if the current player has a valid move
    if not has_valid_move(board, current_player):
        chat_assistant(f"No valid moves for {'⚫' if current_player == 1 else '🔴'}. Turn skipped.", True) # needs fix for ai
        st.session_state.count += 1
        change_s_state_ai(not st.session_state.ai) # Player or AI has to move twice now, so the bool has to change
        st.rerun()


    if st.session_state.clicked_cell:
        i, j = st.session_state.clicked_cell
        st.session_state.clicked_cell = None # next rerun (while rendering) this loop wont run
        st.write(f"Clicked on cell ({i}, {j})")
        modified_board = is_legal_move(board, current_player, i, j)
        if modified_board is not False:
            st.session_state.board = copy.deepcopy(modified_board)
            st.session_state.count += 1  # Update turn count
            chat_assistant("valid move", False)
            st.session_state.rerun = True
            st.rerun() # rerun for rendering the board
        else:
            chat_assistant("Invalid move. You need to outflank an opponent's piece.", False)
            # No rerun, cause board wasn't changed
            return False


def restart_game():
    """Restart the game and clear chat history."""
    st.session_state.clear()  # Clear all session state variables
    st.rerun()  # Rerun the app to reset the game

def ai_move(board, player):
    for row in range(8):
        for col in range(8):
            if is_legal_move(board, player, row, col) is not False:
                st.session_state.clicked_cell = (row, col)
                st.session_state.rerun = True
                change_s_state_ai(True)
                st.rerun()
                return
            
def select_buttons():
    st.title("Select Game Mode")
    if st.button("online"):
        st.session_state.mode = 4
        if "player" not in st.session_state:
            st.session_state.mode = [player_id, 1/-1] # TODO (from firestore maybe)# replace with actual values
        if "game_id" not in st.session_state:
            st.session_state.game_id = "game_id"  # TODO Replace with a unique identifier for the game
    if st.button("Player vs. Player"):
        st.session_state.clear()  # Clear all session state variables
        st.session_state.mode = 3
        st.session_state.page = "game"
    if st.button("Player vs. AI"):
        st.session_state.clear()
        st.session_state.mode = 2
        st.session_state.page = "game"
    if st.button("AI vs. Player"):
        st.session_state.clear()
        st.session_state.mode = 1
        st.session_state.page = "game"
    if st.button("AI vs. AI"):
        st.session_state.clear()
        st.session_state.mode = 0
        st.session_state.page = "game"


def change_s_state_ai(bool):
    if st.session_state.mode == 1 or st.session_state.mode == 2: # rerun depends if AI moved just now or not
        st.session_state.ai = bool
        st.write(f"test3{st.session_state.mode}")
    elif st.session_state.mode == 0: # always rerun
        st.session_state.ai = False
    else: # No need for rerun
        st.session_state.ai = True


def save_game_state(board, current_player, game_id):
    game_data = {
        'board': board.tolist(),  # Convert numpy array to list
        'current_player': current_player,
        'status': 'ongoing'
    }
    db.reference(f'games/{game_id}').set(game_data)

def load_game_state(game_id):
    game_data = db.reference(f'games/{game_id}').get()
    if game_data:
        board = np.array(game_data['board'])  # Convert list back to numpy array
        current_player = game_data['current_player']
        return board, current_player
    return initialize_board(), 1  # Default to initial board and player 1


def main():

    if "current_player" not in st.session_state:
        st.session_state.current_player = 1 # black begins always

    if "page" not in st.session_state:
        st.session_state.page = "select"
    if st.session_state.page == "select": # render select screen
        select_buttons()
    else: # render normal screen
        # Set up the title and layout for Streamlit app
        st.title("Othello Game")
        
        # Add a restart button
        if st.button("Restart Game"):
            restart_game()
        
        if 'board' in st.session_state:  
            board = st.session_state.board
        else:
            board = initialize_board()
        if "count" not in st.session_state:
            st.session_state.count = 1
        if "rerun" not in st.session_state:
            st.session_state.rerun = False
        if "game_over" not in st.session_state:
            st.session_state.game_over = False
        if "ai" not in st.session_state:
            change_s_state_ai(True)   
        elif st.session_state.rerun == False: # No turn for rendering
            change_s_state_ai(False)


        if not st.session_state.rerun and not st.session_state.game_over and st.session_state.mode < 3:
            # Add ai - red
            if st.session_state.count % 2 == 0 and st.session_state.mode != 1:
                time.sleep(1)
                ai_move(board, -1)

            # Add ai - black
            if st.session_state.count % 2 == 1 and st.session_state.mode < 2:
                time.sleep(1)
                ai_move(board, 1)

        if st.session_state.mode == 4: # online
            if st.session_state.current_player != st.session_state.player[1]: # if not players turn, program wont pass this step
                st.session_state.board, st.session_state.current_player = load_game_state(st.session_state.game_id)
                if st.session_state.current_player == st.session_state.player[1]:
                    render_board(st.session_state.board)
                else:    
                    st.write("It's not your turn yet. Please wait for your opponent to make a move.")
                st.rerun()


        
        bool = change_board(board)



        board = st.session_state.board  # Get the updated board from session state

        if st.session_state.mode == 4: # online
            save_game_state(board=board, current_player=st.session_state.current_player, game_id=st.session_state.game_id)
        st.session_state.rerun = False  # Reset rerun flag
        render_board(board)  # Render the board
        if bool is False: # Invalid move, no need to rerun
            return
        if not st.session_state.ai and not st.session_state.game_over: # If AI didn't move, it means that it will move next turn
            st.rerun()


# Run the app
if __name__ == "__main__":
    # st.title("Othellllo Game")

    main()
