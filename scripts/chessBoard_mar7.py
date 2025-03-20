
import chess
import chess.pgn

from game_logic import gameLogic

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
from kivy.clock import Clock


# --- Settings ---


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
    def __init__(self, chess_square, piece_symbol, game_logic, square_size, board_origin, **kwargs):
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
        self.game_logic = game_logic
        self.selected = False
        self.size = (square_size, square_size)
        self.allow_stretch = True
        self.keep_ratio = True
        self.update_position()

    def update_position(self):
        """Set this widget’s pos based on its chess_square.
           (Files 0-7 from left to right; ranks 0-7 from bottom to top.)
        """
        file = self.game_logic.square_file(self.chess_square)
        rank = self.game_logic.square_rank(self.chess_square)
        x = self.board_origin[0] + file * self.square_size
        y = self.board_origin[1] + rank * self.square_size
        self.pos = (x, y)


# ------------------------------------------------------------
# ChessBoard: the widget that draws the board, pieces, and handles touches.
# ------------------------------------------------------------
class ChessBoard(Widget):
    def __init__(self, bottom_colour_white=True, game_logic=None, **kwargs):
        super(ChessBoard, self).__init__(**kwargs)
        # Let the parent control size/position via size_hint, but our widget will compute its own internal layout.
        self.size_hint = (1, 1)
        self.bottom_colour_white = bottom_colour_white
        self.game_logic = game_logic if game_logic is not None else gameLogic()
        self.game_board = self.game_logic.game_board
        self.game_logic.register_observer(self.update_board)

        # Chess pieces and highlights.
        self.selected_piece = None
        self.legal_moves = []
        self.highlight_rects = []

        # These will be computed in on_size.
        self.board_origin = (0, 0)  # Bottom-left of the chessboard (after label area)
        self.board_size = 0         # Size of the 8x8 area (in pixels)
        self.square_size = 0        # Size of one chess square (in pixels)

        # Bind our on_size so that all internal sizing logic is triggered whenever the widget is resized or repositioned.
        self.bind(size=self.on_size, pos=self.on_size)

    def on_size(self, *args):
        """
        Recalculate all internal geometry when the widget size changes.
        We reserve one extra row and column for labels by dividing the smallest dimension by 9.
        """
        cell_size = min(self.width, self.height) / 9.0
        # The chessboard (8x8 area) starts one cell to the right and one cell up.
        self.board_origin = (self.x + cell_size, self.y + cell_size)
        self.square_size = cell_size
        self.board_size = 8 * cell_size

        # Redraw the board background.
        self.canvas.before.clear()
        self.draw_board_background()

        # Remove any existing labels and then re-add them.
        labels_to_remove = [child for child in self.children if isinstance(child, Label)]
        for label in labels_to_remove:
            self.remove_widget(label)
        self.add_labels()

        # Update all chess piece widgets with the new geometry.
        for child in self.children:
            if isinstance(child, ChessPiece):
                child.square_size = self.square_size
                child.board_origin = self.board_origin
                child.size = (self.square_size, self.square_size)
                child.update_position()

    def draw_board_background(self):
        """
        Draw the 8x8 chess squares within the computed chessboard area.
        """
        with self.canvas.before:
            for file in range(8):
                for rank in range(8):
                    # Get canonical square index and its UI position.
                    sq = self.game_logic.square(file, rank)
                    pos = self.chess_square_to_ui_pos(sq)
                    # Alternate colors based on file and rank.
                    if (file + rank) % 2 == 0:
                        color = (189/255, 100/255, 6/255, 1) if self.bottom_colour_white else (247/255, 182/255, 114/255, 1)
                    else:
                        color = (247/255, 182/255, 114/255, 1) if self.bottom_colour_white else (189/255, 100/255, 6/255, 1)
                    Color(*color)
                    Rectangle(pos=pos, size=(self.square_size, self.square_size))

    def add_labels(self):
        """
        Add labels for columns (a–h) in the bottom row and rows (1–8) in the left column.
        These labels occupy the extra cell row/column of the 9x9 grid.
        """
        cell_size = self.square_size  # Each grid cell is of uniform size.
        
        # Column labels (a–h) along the bottom.
        file_order = list(range(8)) if self.bottom_colour_white else list(reversed(range(8)))
        for file in file_order:
            label_text = chr(ord('a') + file)
            # Center the label within the bottom cell.
            label_x = self.board_origin[0] + file * cell_size + (cell_size - cell_size * 0.8) / 2
            label_y = self.y + (cell_size - cell_size * 0.8) / 2
            label = Label(text=label_text,
                          size_hint=(None, None),
                          size=(cell_size * 0.8, cell_size * 0.8),
                          pos=(label_x, label_y),
                          font_size=cell_size * 0.5)
            self.add_widget(label)
        
        # Row labels (1–8) along the left.
        rank_order = list(range(8)) if self.bottom_colour_white else list(reversed(range(8)))
        for rank in rank_order:
            label_text = str(rank + 1)
            # Center the label within the left cell.
            label_x = self.x + (cell_size - cell_size * 0.8) / 2
            label_y = self.board_origin[1] + rank * cell_size + (cell_size - cell_size * 0.8) / 2
            label = Label(text=label_text,
                          size_hint=(None, None),
                          size=(cell_size * 0.8, cell_size * 0.8),
                          pos=(label_x, label_y),
                          font_size=cell_size * 0.5)
            self.add_widget(label)

    def chess_square_to_ui_pos(self, sq):
        """
        Convert a chess square index (0–63) into UI coordinates within the chessboard area.
        """
        file = self.game_logic.square_file(sq)
        rank = self.game_logic.square_rank(sq)
        if not self.bottom_colour_white:
            file = 7 - file
            rank = 7 - rank
        x = self.board_origin[0] + file * self.square_size
        y = self.board_origin[1] + rank * self.square_size
        return (x, y)

    def add_piece_widgets(self):
        """
        Remove any existing ChessPiece widgets and add one for every piece on the board.
        """
        for child in list(self.children):
            if isinstance(child, ChessPiece):
                self.remove_widget(child)
        for sq in self.game_logic.SQUARES:
            piece = self.game_board.piece_at(sq)
            if piece is not None:
                symbol = piece.symbol()
                if symbol in piece_images:
                    source = piece_images[symbol]
                    piece_widget = ChessPiece(
                        game_logic=self.game_logic,
                        chess_square=sq,
                        piece_symbol=symbol,
                        square_size=self.square_size,
                        board_origin=self.board_origin,
                        source=source
                    )
                    piece_widget.pos = self.chess_square_to_ui_pos(sq)
                    self.add_widget(piece_widget)

    def clear_highlights(self):
        """Remove any highlighted rectangles from the board."""
        for rect in self.highlight_rects:
            self.canvas.remove(rect)
        self.highlight_rects = []

    def update_board(self):
        """
        Called by the game logic when the board state changes.
        Refreshes the piece widgets and clears any highlights.
        """
        self.clear_highlights()
        self.add_piece_widgets()
    


# ------------------------------------------------------------
# ChessGameWidget: the root widget that arranges the board, move list, and captured pieces.
# ------------------------------------------------------------
class ChessGameWidget(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.panel_width = 200  # Fixed width for the side panels

        # --- Create the captured pieces panel (left side) ---
        self.captured_panel = BoxLayout(
            orientation='vertical',
            size_hint=(None, 1),
            width=self.panel_width
        )
        self.captured_panel.add_widget(Label(text="Captured", size_hint_y=None, height=40, font_size=FONT_SIZE))
        self.add_widget(self.captured_panel)

        # --- Create the move list panel (right side) ---
        self.move_list_container = BoxLayout(orientation='vertical', size_hint_y=None)
        self.move_list_container.bind(minimum_height=self.move_list_container.setter('height'))
        self.move_list_scroll = ScrollView(
            size_hint=(None, 1),
            width=self.panel_width
        )
        self.move_list_scroll.add_widget(self.move_list_container)
        self.add_widget(self.move_list_scroll)

        # --- Create the chessboard (center) ---
        self.chess_board = ChessBoard()
        self.chess_board.captured_panel = self.captured_panel
        self.chess_board.move_list_container = self.move_list_container
        self.add_widget(self.chess_board)

        # --- Create the move input box ---
        self.move_input = TextInput(
            size_hint=(None, None),
            size=(self.panel_width, 40),
            multiline=False
        )
        self.move_input.bind(on_text_validate=self.on_move_entered)
        self.add_widget(self.move_input)

        # Bind to size changes so that layout updates dynamically.
        self.bind(size=self.update_layout)

    def update_layout(self, *args):
        screen_width = self.width
        screen_height = self.height
        # Compute the board size as the maximum square that fits in the central area.
        board_size = min(screen_height, screen_width - 2 * self.panel_width)
        square_size = board_size / 8.0

        # Center the board horizontally between the side panels and vertically centered.
        board_origin_x = self.panel_width + ((screen_width - 2 * self.panel_width - board_size) / 2)
        board_origin_y = (screen_height - board_size) / 2

        # Update the chess_board's position and size.
        self.chess_board.pos = (board_origin_x, board_origin_y)
        self.chess_board.size = (board_size, board_size)
        # Trigger the ChessBoard on_size update.
        self.chess_board.on_size()

        # Update the captured panel (left side).
        self.captured_panel.pos = (0, 0)
        self.captured_panel.size = (self.panel_width, screen_height)

        # Update the move list scroll view (right side).
        self.move_list_scroll.pos = (screen_width - self.panel_width, 0)
        self.move_list_scroll.size = (self.panel_width, screen_height)

        # Position the move input box (for example, at the bottom of the move list).
        self.move_input.pos = (screen_width - self.panel_width, 0)

    def on_move_entered(self, instance):
        move_str = instance.text
        try:
            # Try to interpret the move as a UCI move.
            move = chess.Move.from_uci(move_str)
            if move not in self.chess_board.game_board.legal_moves:
                # If not legal in UCI format, try SAN.
                move = self.chess_board.game_board.parse_san(move_str)

            if move in self.chess_board.game_board.legal_moves:
                # Find and select the piece at the move's starting square.
                from_square = move.from_square
                self.chess_board.selected_piece = None
                for child in self.chess_board.children:
                    if isinstance(child, ChessPiece) and child.chess_square == from_square:
                        self.chess_board.selected_piece = child
                        break

                if self.chess_board.selected_piece:
                    self.chess_board.make_move(move)
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