import copy
import numpy as np

class Board:
    def __init__(self):
        self.state = np.zeros((8, 8), dtype=int)
        self.reset()

    def reset(self):
        self.state.fill(0)
        self.state[3][3], self.state[4][4] = 1, 1
        self.state[3][4], self.state[4][3] = -1, -1

    def is_legal_move(self, player, row, col):
        if self.state[row][col] != 0:
            return False

        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        legal = False
        modified_board = copy.deepcopy(self.state)
        helper = copy.deepcopy(self.state)
        for dr, dc in directions:
            found_opponent = False
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                if self.state[r][c] == -player:
                    found_opponent = True
                    if 0 <= r + dr < 8 and 0 <= c + dc < 8:
                        modified_board[r][c] = player
                    else:
                        modified_board = copy.deepcopy(helper)
                elif self.state[r][c] == player:
                    if found_opponent:
                        helper = copy.deepcopy(modified_board)
                        legal = True
                    break
                else:
                    modified_board = copy.deepcopy(helper)
                    break
                r += dr
                c += dc
        if legal:
            modified_board[row][col] = player
            return modified_board
        else:
            return False

    def has_valid_move(self, player):
        for row in range(8):
            for col in range(8):
                if self.is_legal_move(player, row, col) is not False:
                    return True
        return False

    def count_pieces(self):
        black_count = np.sum(self.state == 1)
        red_count = np.sum(self.state == -1)
        return black_count, red_count
    
    def count_edges(self, edge_value, border_value):# WATCH OUT: returns only the right difference, not the actual scores!!
        # Base counts
        black_count = np.sum(self.state == 1)
        red_count = np.sum(self.state == -1)

        # Corners
        corners = [self.state[0, 0], self.state[0, 7], self.state[7, 0], self.state[7, 7]]
        corner_score = sum(corners) * edge_value  # Will be negative if red controls more

        # Borders (edges are excluded)
        top_row = self.state[0, 1:7]
        bottom_row = self.state[7, 1:7]
        left_col = self.state[1:7, 0]
        right_col = self.state[1:7, 7]

        # Combine edge control — each element is -1, 0, or 1
        border_control = np.sum(top_row) + np.sum(bottom_row) + np.sum(left_col) + np.sum(right_col)
        border_score = border_control * border_value

        # Add corner + border influence to black's score - black can be negative, but thats fine for the difference
        black_count += corner_score + border_score

        return black_count, red_count


    def apply_move(self, player, row, col):
        new_state = self.is_legal_move(player, row, col)
        if new_state is not False:
            self.state = new_state
            return True
        return False

    def get_valid_moves(self, player):
        moves = []
        for row in range(8):
            for col in range(8):
                if self.is_legal_move(player, row, col) is not False:
                    moves.append((row, col))
        return moves

    def copy(self):
        new_board = Board()
        new_board.state = self.state.copy()
        return new_board

