import random
from rl_agent.rl_agent import RLAgent

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
    def __init__(self, color, depths):
        super().__init__(color)
        index = 0 if color == 1 else 1
        self.depth = depths[index]

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
    
class EdgesEdgar(Player):
    """Looks ahead a few moves, tries to maximize own pieces/specializes in edge control."""
    def __init__(self, color, depths, edge_value, border_value):
        super().__init__(color)
        index = 0 if color == 1 else 1
        self.depth = depths[index]
        self.edge_value = edge_value[index]
        self.border_value = border_value[index]

    def get_move(self, board_obj):
        def edgesedgar(board, player, depth, edge_value, border_value):
            if depth == 0 or not board.has_valid_move(player):
                black, red = board.count_edges(edge_value, border_value)
                return (black - red) * player, None
            best_score = float('-inf')
            best_move = None
            for move in board.get_valid_moves(player):
                new_board = board.copy()
                new_board.apply_move(player, *move)
                score, _ = edgesedgar(new_board, -player, depth - 1, edge_value, border_value)
                score = -score
                if score > best_score:
                    best_score = score
                    best_move = move
            return best_score, best_move
        _, move = edgesedgar(board_obj, self.color, self.depth, self.edge_value, self.border_value)
        return move

class RLRandomRiley(Player):
    """Placeholder RL agent: picks a random valid move."""
    def get_move(self, board_obj):
        moves = board_obj.get_valid_moves(self.color)
        return random.choice(moves) if moves else None

class RLJonas(Player):
    """Deep RL agent using a neural network (DQN)."""
    def __init__(self, color, model_path=None, epsilon=0.1):
        super().__init__(color)
        self.agent = RLAgent(color, epsilon=epsilon)
        if model_path:
            import torch
            self.agent.model.load_state_dict(torch.load(model_path, map_location="cpu"))
            self.agent.model.eval()

    def get_move(self, board_obj):
        return self.agent.get_move(board_obj)
