'''
Used to track game state, register moves, check game codition, legal moves etc
'''
import chess
import chess.pgn 

class gameLogic:


    def __init__(self):
        self.game_board = chess.Board()
        self.SQUARES = chess.SQUARES
        self.game_state = "UNFINISHED"
        self.game_history = []
        self.game_pgn = chess.pgn.Game()
        self.observers = []  # Views that need to update when state changes


    def square_file(self, sq):
        return chess.square_file(sq)
    
    def square_rank(self, sq):
        return chess.square_rank(sq)
    
    def create_fen(self, fen):
        return chess.Board(fen)
    
    def square(self, col, row):
        return chess.square(col, row)
    
    def update_board(self):
        return self.game_board
    
    def register_observer(self, observer_callback):
        """Observers (e.g., your board widgets) register a callback to be notified on updates."""
        self.observers.append(observer_callback)

    def notify_observers(self):
        for callback in self.observers:
            callback()
    
    def select_piece(self, square):
        # Find legal moves for the selected piece, update any boards with hgihlighted squares

        legal_moves = [move for move in self.game_board.legal_moves if move.from_square == square]
        self.update_board()
        return legal_moves

    def push(self, move):
        """Push a move onto the board and notify all observers."""
        self.game_board.push(move)
        self.notify_observers()







