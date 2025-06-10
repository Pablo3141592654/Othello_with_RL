import random

<<<<<<< HEAD


=======
>>>>>>> 593ef772e21a9b6be8b4fc1c42b4fa01be2fa9d1
class Player:
    def __init__(self, color):
        self.color = color  # 1 for black, -1 for red

    def get_move(self, board_obj):
        raise NotImplementedError

class HumanPlayer(Player):
    def get_move(self, board_obj):
        # In Streamlit, moves are handled by UI, so this can be a placeholder
        pass

class GreedyGreta(Player):
    """Picks the first valid move it finds."""
    def get_move(self, board_obj):
        moves = board_obj.get_valid_moves(self.color)
        return moves[0] if moves else None

class MinimaxMax(Player):
    """Looks ahead a few moves, tries to maximize own pieces."""
<<<<<<< HEAD
    def __init__(self, color, depths):
        super().__init__(color)
        index = 0 if color == 1 else 1
        self.depth = depths[index]

    
=======
    def __init__(self, color, depth=2):
        super().__init__(color)
        self.depth = depth

>>>>>>> 593ef772e21a9b6be8b4fc1c42b4fa01be2fa9d1
    def get_move(self, board_obj):
        def minimax(board, player, depth):
            if depth == 0 or not board.has_valid_move(player):
                black, red = board.count_pieces()
                return (black - red) * player, None
            best_score = float('-inf')
            best_move = None
            for move in board.get_valid_moves(player):
                new_board = board.copy()
                new_board.apply_move(player, *move)
                score, _ = minimax(new_board, -player, depth - 1)
                score = -score
                if score > best_score:
                    best_score = score
                    best_move = move
            return best_score, best_move
        _, move = minimax(board_obj, self.color, self.depth)
        return move

class RLRandomRiley(Player):
    """Placeholder RL agent: picks a random valid move."""
    def get_move(self, board_obj):
        moves = board_obj.get_valid_moves(self.color)
        return random.choice(moves) if moves else None