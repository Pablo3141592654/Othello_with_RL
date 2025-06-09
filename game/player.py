class Player:
    def __init__(self, color):
        self.color = color  # 1 for black, -1 for red

    def get_move(self, board):
        raise NotImplementedError

class HumanPlayer(Player):
    def get_move(self, board):
        # In Streamlit, moves are handled by UI, so this can be a placeholder
        pass

class ClassicAIPlayer(Player):
    def get_move(self, board):
        # Implement Minimax/Alpha-Beta here
        pass

class RLAgentPlayer(Player):
    def get_move(self, board):
        # Implement RL logic here
        pass