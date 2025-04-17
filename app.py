import streamlit as st
import numpy as np

# Define a function to render the Othello board
def render_board(board):
    st.write("### Othello Board")
    
    # Create a simple table layout for the board
    for i, row in enumerate(board):  # Enumerate to get both row index (i) and the row itself
        cols = st.columns(len(row))
        for j, col in enumerate(cols):  # Enumerate to get both column index (j) and the column
            if row[j] == 1:
                col.button('⚫', key=f'{i}-{j}')  # Black for player 1
            elif row[j] == -1:
                col.button('⚪', key=f'{i}-{j}')  # White for player 2
            else:
                col.button('⬜', key=f'{i}-{j}')  # Empty space (light grey)

# Initial empty board setup
def initialize_board():
    # Set up the initial 8x8 board with 0s
    board = np.zeros((8, 8), dtype=int)
    # Set up initial 4 pieces in the center
    board[3][3], board[4][4] = 1, 1  # Player 1's pieces (Blue)
    board[3][4], board[4][3] = -1, -1  # Player 2's pieces (Green)
    return board

# Main function to run the app
def main():
    # Set up the title and layout for Streamlit app
    st.title("Othello Game")
    
    # Initialize the board
    board = initialize_board()
    
    # Render the board
    render_board(board)

# Run the app
if __name__ == "__main__":
    main()
