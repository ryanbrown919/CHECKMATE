import kivy
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
import chess  # pip install python-chess

# Set this flag depending on your platform.
# For testing on a Mac/PC, leave as False.
RUNNING_ON_PI = False
if RUNNING_ON_PI:
    try:
        import RPi.GPIO as GPIO
        # Set up your GPIO pins and multiplexer reading here.
    except ImportError:
        print("RPi.GPIO not available; falling back to simulation mode.")
        RUNNING_ON_PI = False

# Convert a (row, col) position to chess algebraic notation.
def square_notation(pos):
    row, col = pos
    file = chr(ord('a') + col)
    rank = str(8 - row)
    return file + rank

# A chess square that simulates a hall effect sensor.
class ChessSquare(ToggleButton):
    def __init__(self, row, col, **kwargs):
        super(ChessSquare, self).__init__(**kwargs)
        self.row = row
        self.col = col
        self.text = ""
        self.default_color = self.get_color()
        self.background_color = self.default_color

    def get_color(self):
        # Light and dark square pattern.
        if (self.row + self.col) % 2 == 0:
            return (1, 1, 1, 1)  # light square
        else:
            return (0.5, 0.5, 0.5, 1)  # dark square

    def highlight(self, color=(0, 0, 1, 0.5)):
        self.background_color = color

    def reset_color(self):
        self.background_color = self.get_color()

# A chessboard widget composed of 64 ChessSquare widgets.
class ChessBoard(GridLayout):
    def __init__(self, interactive=True, **kwargs):
        super(ChessBoard, self).__init__(**kwargs)
        self.cols = 8
        self.rows = 8
        self.interactive = interactive
        self.squares = {}
        for row in range(8):
            for col in range(8):
                square = ChessSquare(row, col)
                if not interactive:
                    square.disabled = True
                self.add_widget(square)
                self.squares[(row, col)] = square

    def get_state(self):
        # Returns a dict mapping (row, col) to state (1 for active, 0 for inactive)
        state = {}
        for (row, col), square in self.squares.items():
            state[(row, col)] = 1 if square.state == 'down' else 0
        return state

    def set_state(self, state):
        # Update each square based on the given state dict.
        for (row, col), value in state.items():
            square = self.squares.get((row, col))
            if square:
                square.state = 'down' if value == 1 else 'normal'
                square.reset_color()

    def highlight_squares(self, positions, color=(0, 0, 1, 0.5)):
        # Highlight the squares given by the list of positions.
        for pos in positions:
            if pos in self.squares:
                self.squares[pos].highlight(color)

    def clear_highlights(self):
        for square in self.squares.values():
            square.reset_color()

# Main app that integrates sensor polling, lifted mode move detection, and game reset.
class ChessApp(App):
    def build(self):
        # Create a python-chess engine (starting position).
        self.chess_engine = chess.Board()

        # Which digital value means "occupied" (simulate with toggle down).
        self.occupied_value = 1

        # Flags for detecting a piece being lifted.
        self.lifted_mode = False
        self.lifted_square = None

        # Polling intervals.
        self.normal_poll_interval = 0.5
        self.fast_poll_interval = 0.1

        # Root layout with two panels: left for sensor board, right for chessboard & controls.
        root = BoxLayout(orientation='horizontal')

        # Left panel: interactive board simulating hall effect sensors.
        self.left_board = ChessBoard(interactive=True)

        # Right panel: display board and control buttons.
        self.right_panel = BoxLayout(orientation='vertical', size_hint=(0.4, 1))
        
        # Reset button.
        self.reset_button = Button(text="Reset", size_hint=(1, 0.1))
        self.reset_button.bind(on_press=self.reset_game)
        self.right_panel.add_widget(self.reset_button)
        
        # Label to show move messages.
        self.move_label = Label(text="Last move: None", size_hint=(1, 0.1))
        self.right_panel.add_widget(self.move_label)
        
        # Display chessboard reflecting the chess engine state.
        self.display_board = ChessBoard(interactive=False)
        self.right_panel.add_widget(self.display_board)

        root.add_widget(self.left_board)
        root.add_widget(self.right_panel)

        # Initialize the boards to the engine's starting state.
        self.sync_boards_with_engine()
        self.poll_event = Clock.schedule_interval(self.poll_sensors, self.normal_poll_interval)
        return root

    def sync_boards_with_engine(self):
        # Synchronize both the interactive board and display board with the engine state.
        state = {}
        for row in range(8):
            for col in range(8):
                sq = square_notation((row, col))
                piece = self.chess_engine.piece_at(chess.parse_square(sq))
                state[(row, col)] = 1 if piece is not None else 0
        self.left_board.set_state(state)
        self.display_board.set_state(state)

    def reset_game(self, instance=None):
        # Reset the chess engine and clear any lifted mode/highlights.
        self.chess_engine.reset()
        self.lifted_mode = False
        self.lifted_square = None
        self.left_board.clear_highlights()
        self.move_label.text = "Game reset."
        self.sync_boards_with_engine()

    def read_hall_effects(self):
        # If running on Pi, replace this with your GPIO multiplexer/hall effect code.
        if RUNNING_ON_PI:
            # Return a dict {(row, col): state, ...}
            return {}  # Implement your hardware reading here.
        else:
            return self.left_board.get_state()

    def poll_sensors(self, dt):
        current_state = self.read_hall_effects()
        if not self.lifted_mode:
            self.process_normal_mode(current_state)
        else:
            self.process_lifted_mode(current_state)

    def process_normal_mode(self, current_state):
        # Check expected board state from the chess engine.
        board_state = {}
        for row in range(8):
            for col in range(8):
                sq = square_notation((row, col))
                piece = self.chess_engine.piece_at(chess.parse_square(sq))
                board_state[(row, col)] = 1 if piece is not None else 0

        # Look for a square where a piece is expected but its sensor is off.
        for pos, expected in board_state.items():
            current = current_state.get(pos, 0)
            if expected == self.occupied_value and current != self.occupied_value:
                # A piece has been lifted.
                self.lifted_mode = True
                self.lifted_square = pos
                self.move_label.text = f"Piece lifted from {square_notation(pos)}"
                self.start_fast_polling()
                self.highlight_legal_moves(pos)
                return

    def process_lifted_mode(self, current_state):
        lifted_pos = self.lifted_square
        legal_destinations = self.get_legal_destinations(lifted_pos)
        destination_chosen = None

        # Check if one of the highlighted legal squares is activated.
        for pos in legal_destinations:
            if current_state.get(pos, 0) == self.occupied_value:
                destination_chosen = pos
                break

        # If the piece is returned to its original square, cancel lifted mode.
        if current_state.get(lifted_pos, self.occupied_value) == self.occupied_value:
            self.move_label.text = f"Move cancelled. Piece returned to {square_notation(lifted_pos)}"
            self.lifted_mode = False
            self.lifted_square = None
            self.clear_fast_polling()
            self.left_board.clear_highlights()
            return

        if destination_chosen:
            move_str = f"{square_notation(lifted_pos)} -> {square_notation(destination_chosen)}"
            move = chess.Move.from_uci(f"{square_notation(lifted_pos)}{square_notation(destination_chosen)}")
            if move in self.chess_engine.legal_moves:
                self.chess_engine.push(move)
                self.move_label.text = f"Detected move: {move_str}"
                self.sync_boards_with_engine()
            else:
                self.move_label.text = f"Illegal move: {move_str}"
            self.lifted_mode = False
            self.lifted_square = None
            self.clear_fast_polling()
            self.left_board.clear_highlights()

    def get_legal_destinations(self, from_pos):
        # Get a list of legal destination squares (as (row, col) tuples) for the piece on from_pos.
        from_square = chess.parse_square(square_notation(from_pos))
        legal_dests = []
        for move in self.chess_engine.legal_moves:
            if move.from_square == from_square:
                dest_alg = chess.square_name(move.to_square)
                col = ord(dest_alg[0]) - ord('a')
                row = 8 - int(dest_alg[1])
                legal_dests.append((row, col))
        return legal_dests

    def highlight_legal_moves(self, from_pos):
        legal_destinations = self.get_legal_destinations(from_pos)
        self.left_board.highlight_squares(legal_destinations, color=(0, 0, 1, 0.5))
        legal_str = ", ".join([square_notation(pos) for pos in legal_destinations])
        self.move_label.text += f" | Possible moves: {legal_str}"

    def start_fast_polling(self):
        if self.poll_event:
            self.poll_event.cancel()
        self.poll_event = Clock.schedule_interval(self.poll_sensors, self.fast_poll_interval)

    def clear_fast_polling(self):
        if self.poll_event:
            self.poll_event.cancel()
        self.poll_event = Clock.schedule_interval(self.poll_sensors, self.normal_poll_interval)

if __name__ == '__main__':
    ChessApp().run()
