import chess
import chess.pgn

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window

# --- Settings ---
Window.fullscreen = True

FONT_SIZE=32

# --- Image File Mapping ---
# Map chess piece symbols (as returned by chess.Piece.symbol()) to image file paths.
piece_images = {
    'P': 'figures/white_pawn.png',
    'R': 'figures/white_rook.png',
    'N': 'figures/white_knight.png',
    'B': 'figures/white_bishop.png',
    'Q': 'figures/white_queen.png',
    'K': 'figures/white_king.png',
    'p': 'figures/black_pawn.png',
    'r': 'figures/black_rook.png',
    'n': 'figures/black_knight.png',
    'b': 'figures/black_bishop.png',
    'q': 'figures/black_queen.png',
    'k': 'figures/black_king.png',
}

# ------------------------------------------------------------
# ChessPiece: a widget representing one chess piece.
# ------------------------------------------------------------
class ChessPiece(Image):
    def __init__(self, chess_square, piece_symbol, square_size, board_origin, **kwargs):
        """
        chess_square: a python‑chess square (0‑63)
        piece_symbol: a one‑character string (e.g., 'P' for white pawn)
        square_size: size in pixels of one square on the board
        board_origin: (x, y) position of the bottom‑left corner of the board
        """
        super().__init__(**kwargs)
        self.chess_square = chess_square
        self.piece_symbol = piece_symbol
        self.square_size = square_size
        self.board_origin = board_origin
        self.selected = False
        self.size = (square_size, square_size)
        self.allow_stretch = True
        self.keep_ratio = True
        self.update_position()

    def update_position(self):
        """Set this widget’s pos based on its chess_square.
           (Files 0-7 from left to right; ranks 0-7 from bottom to top.)
        """
        file = chess.square_file(self.chess_square)
        rank = chess.square_rank(self.chess_square)
        x = self.board_origin[0] + file * self.square_size
        y = self.board_origin[1] + rank * self.square_size
        self.pos = (x, y)


# ------------------------------------------------------------
# ChessBoard: the widget that draws the board, pieces, and handles touches.
# ------------------------------------------------------------
class ChessBoard(Widget):
    def __init__(self, board_origin=(1920/2, 1080/2), board_size=1000, **kwargs):
        """
        board_origin: (x, y) bottom‑left corner of the board
        board_size: size in pixels (assumed square)
        """
        super().__init__(**kwargs)

        self.board_origin = board_origin
        self.board_size = board_size
        self.square_size = board_size / 8.0

        # These will be set later by the parent container:
        self.captured_panel = None      # widget where captured pieces are displayed (left side)
        self.move_list_container = None # BoxLayout inside the ScrollView for moves

        # For highlighting legal moves
        self.highlight_rects = []
        self.legal_moves = []
        self.selected_piece = None

        # Create the python‑chess board with the standard starting position.
        self.game_board = chess.Board()

        # Draw the board background (use canvas.before so it appears behind pieces)
        with self.canvas.before:
            for row in range(8):
                for col in range(8):
                    # Standard chessboard coloring: dark and light squares.
                    if (col + row) % 2 == 0:
                        Color(0.2, 0.2, 0.2, 1)
                    else:
                        Color(1, 1, 1, 1)
                    Rectangle(
                        pos=(self.board_origin[0] + col * self.square_size,
                             self.board_origin[1] + row * self.square_size),
                        size=(self.square_size, self.square_size)
                    )

        # Place piece widgets on top.
        self.add_piece_widgets()

        # Add row and column labels
        self.add_labels()

    def add_labels(self):
        """Add labels for rows and columns around the board."""
        # Column labels (a-h)
        for col in range(8):
            label = Label(
                text=chr(ord('a') + col),
                size_hint=(None, None),
                size=(self.square_size, self.square_size),
                pos=(self.board_origin[0] + col * self.square_size + self.square_size / 2 - self.square_size / 4,
                     self.board_origin[1] - self.square_size)
            )
            self.add_widget(label)

        # Row labels (1-8)
        for row in range(8):
            label = Label(
                text=str(row + 1),
                size_hint=(None, None),
                size=(self.square_size, self.square_size),
                pos=(self.board_origin[0] - self.square_size,
                     self.board_origin[1] + row * self.square_size + self.square_size / 2 - self.square_size / 4)
            )
            self.add_widget(label)

    def add_piece_widgets(self):
        """Remove any existing ChessPiece widgets and add one for every piece on the board."""
        for child in list(self.children):
            if isinstance(child, ChessPiece):
                self.remove_widget(child)

        for sq in chess.SQUARES:
            piece = self.game_board.piece_at(sq)
            if piece is not None:
                symbol = piece.symbol()  # e.g., 'P' or 'k'
                if symbol in piece_images:
                    source = piece_images[symbol]
                    piece_widget = ChessPiece(
                        chess_square=sq,
                        piece_symbol=symbol,
                        square_size=self.square_size,
                        board_origin=self.board_origin,
                        source=source
                    )
                    self.add_widget(piece_widget)

    def ui_to_chess_square(self, x, y):
        """Convert a UI (x, y) coordinate to a chess square (0‑63) if inside the board."""
        bx, by = self.board_origin
        if not (bx <= x <= bx + self.board_size and by <= y <= by + self.board_size):
            return None
        col = int((x - bx) / self.square_size)
        row = int((y - by) / self.square_size)
        return chess.square(col, row)

    def chess_square_to_ui_pos(self, sq):
        """Convert a chess square to a UI (x, y) position."""
        file = chess.square_file(sq)
        rank = chess.square_rank(sq)
        x = self.board_origin[0] + file * self.square_size
        y = self.board_origin[1] + rank * self.square_size
        return (x, y)

    def highlight_legal_moves(self, piece_widget):
        """Highlight all legal moves for the given piece using python‑chess.
           Capture moves are highlighted in red; non-captures in green.
        """
        self.clear_highlights()
        from_sq = piece_widget.chess_square
        self.legal_moves = [move for move in self.game_board.legal_moves if move.from_square == from_sq]
        with self.canvas:
            for move in self.legal_moves:
                pos = self.chess_square_to_ui_pos(move.to_square)
                if self.game_board.is_capture(move):
                    Color(1, 0, 0, 0.5)  # red for captures
                else:
                    Color(0, 1, 0, 0.5)  # green for non-captures
                rect = Rectangle(pos=pos, size=(self.square_size, self.square_size))
                self.highlight_rects.append(rect)

    def clear_highlights(self):
        """Remove any highlighted rectangles from the board."""
        for rect in self.highlight_rects:
            self.canvas.remove(rect)
        self.highlight_rects = []

    def execute_move(self, legal_move):
        """Push the move, update piece positions, handle captures, and update the move list."""
        san_move = self.game_board.san(legal_move)
        self.game_board.push(legal_move)
        # Update the moving piece’s square and position.
        self.selected_piece.chess_square = legal_move.to_square
        self.selected_piece.update_position()

        # If a capture occurred, remove the captured piece widget.
        for child in list(self.children):
            if (isinstance(child, ChessPiece) and child is not self.selected_piece and
                child.chess_square == legal_move.to_square):
                self.remove_widget(child)
                if self.captured_panel:
                    # Optionally, scale the captured piece down.
                    child.size_hint = (None, None)
                    scale = 0.8
                    child.size = (self.square_size * scale, self.square_size * scale)
                    self.captured_panel.add_widget(child)

        self.clear_highlights()
        self.selected_piece.selected = False
        self.selected_piece = None
        self.legal_moves = []
        # Refresh piece widgets (in case of promotions, etc.).
        self.add_piece_widgets()
        if self.move_list_container:
            label = Label(text=san_move, size_hint_y=None, height=30, font_size=24)
            self.move_list_container.add_widget(label)

    def on_touch_down(self, touch):
        bx, by = self.board_origin
        # Only consider touches inside the board area.
        if not (bx <= touch.x <= bx + self.board_size and by <= touch.y <= by + self.board_size):
            return False

        # First, get the destination square regardless of widgets.
        dest_sq = self.ui_to_chess_square(touch.x, touch.y)

        # If a piece is already selected and the touched square is one of its legal move destinations, execute the move.
        if self.selected_piece and dest_sq is not None:
            for move in self.legal_moves:
                if move.to_square == dest_sq:
                    print(f"Executing move: {move}")
                    self.execute_move(move)
                    return True

        # Otherwise, check if a piece was touched.
        touched_piece = None
        for child in self.children:
            if isinstance(child, ChessPiece) and child.collide_point(touch.x, touch.y):
                touched_piece = child
                break

        if touched_piece:
            # If the same piece is touched twice, deselect it.
            if self.selected_piece == touched_piece:
                self.selected_piece.selected = False
                self.selected_piece = None
                self.clear_highlights()
            else:
                self.selected_piece = touched_piece
                touched_piece.selected = True
                self.clear_highlights()
                self.highlight_legal_moves(touched_piece)
            return True

        # If no piece is touched and a piece is selected, deselect it.
        if self.selected_piece:
            self.selected_piece.selected = False
            self.selected_piece = None
            self.clear_highlights()
            return True

        return False


# ------------------------------------------------------------
# ChessGameWidget: the root widget that arranges the board, move list, and captured pieces.
# ------------------------------------------------------------
class ChessGameWidget(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # --- Define panel sizes ---
        panel_width = 200  # width (in pixels) for left (captured pieces) and right (move list) panels
        screen_width = 1920
        screen_height = 1080

        # The board size will be the maximum square that fits in the central area.
        board_size = min(screen_height, screen_width - 2 * panel_width)
        self.square_size = board_size / 8

        # Center the board in the area between the panels, leaving space for labels.
        board_origin_x = panel_width + ((screen_width - 2 * panel_width - board_size) / 2) + self.square_size
        board_origin_y = ((screen_height - board_size) / 2) + self.square_size
        board_origin = (board_origin_x, board_origin_y)

        # --- Create the captured pieces panel (left side) ---
        self.captured_panel = BoxLayout(
            orientation='vertical',
            size_hint=(None, 1),
            width=panel_width,
            pos=(0, 0)
        )
        self.captured_panel.add_widget(Label(text="Captured", size_hint_y=None, height=40, font_size=FONT_SIZE))
        self.add_widget(self.captured_panel)

        # --- Create the move list panel (right side) ---
        move_list_scroll = ScrollView(
            size_hint=(None, 1),
            width=panel_width,
            pos=(screen_width - panel_width, 0)
        )
        self.move_list_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None
        )
        self.move_list_container.bind(minimum_height=self.move_list_container.setter('height'))
        move_list_scroll.add_widget(self.move_list_container)
        self.add_widget(move_list_scroll)

        # --- Create the chessboard ---
        self.chess_board = ChessBoard(board_origin=board_origin, board_size=board_size)
        self.chess_board.captured_panel = self.captured_panel
        self.chess_board.move_list_container = self.move_list_container
        self.add_widget(self.chess_board)

        # --- Create the move input box ---
        self.move_input = TextInput(
            size_hint=(None, None),
            size=(panel_width, 40),
            pos=(screen_width - panel_width, 0),
            multiline=False
        )
        self.move_input.bind(on_text_validate=self.on_move_entered)
        self.add_widget(self.move_input)

    def on_move_entered(self, instance):
        move_str = instance.text
        try:
            # Try to interpret the move as a UCI move
            move = chess.Move.from_uci(move_str)
            if move not in self.chess_board.game_board.legal_moves:
                # If the move is not legal in UCI format, try interpreting it as a SAN move
                move = self.chess_board.game_board.parse_san(move_str)
            
            if move in self.chess_board.game_board.legal_moves:
                # Select the piece at the starting square
                from_square = move.from_square
                self.chess_board.selected_piece = None
                for child in self.chess_board.children:
                    if isinstance(child, ChessPiece) and child.chess_square == from_square:
                        self.chess_board.selected_piece = child
                        break

                if self.chess_board.selected_piece:
                    self.chess_board.execute_move(move)
                    instance.text = ""
                else:
                    self.add_debug_message(f"No piece at starting square: {move_str}")
                    instance.text = ""
            else:
                self.add_debug_message(f"Illegal move: {move_str}")
                instance.text = ""
        except ValueError:
            self.add_debug_message(f"Invalid move format: {move_str}")
            instance.text = ""

    def add_debug_message(self, message):
        """Add a debug message to the move list container."""
        label = Label(text=message, size_hint_y=None, height=40)
        self.move_list_container.add_widget(label)


# ------------------------------------------------------------
# The App
# ------------------------------------------------------------
class ChessApp(App):
    def build(self):
        return ChessGameWidget()


if __name__ == '__main__':
    ChessApp().run()