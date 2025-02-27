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
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window

# --- Settings ---
Window.fullscreen = True

FONT_SIZE = 32

# --- Image File Mapping ---
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

        self.captured_panel = None      # widget where captured pieces are displayed (left side)
        self.move_list_container = None # BoxLayout inside the ScrollView for moves

        self.highlight_rects = []
        self.legal_moves = []
        self.selected_piece = None

        self.game_board = chess.Board()

        with self.canvas.before:
            for row in range(8):
                for col in range(8):
                    if (col + row) % 2 == 0:
                        Color(0.2, 0.2, 0.2, 1)
                    else:
                        Color(1, 1, 1, 1)
                    Rectangle(
                        pos=(self.board_origin[0] + col * self.square_size,
                             self.board_origin[1] + row * self.square_size),
                        size=(self.square_size, self.square_size)
                    )

        self.add_piece_widgets()
        self.add_labels()

    def add_labels(self):
        for col in range(8):
            label = Label(
                text=chr(ord('a') + col),
                size_hint=(None, None),
                size=(self.square_size, self.square_size),
                pos=(self.board_origin[0] + col * self.square_size + self.square_size / 2 - self.square_size / 4,
                     self.board_origin[1] - self.square_size)
            )
            self.add_widget(label)

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
        for child in list(self.children):
            if isinstance(child, ChessPiece):
                self.remove_widget(child)

        for sq in chess.SQUARES:
            piece = self.game_board.piece_at(sq)
            if piece is not None:
                symbol = piece.symbol()
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
        bx, by = self.board_origin
        if not (bx <= x <= bx + self.board_size and by <= y <= by + self.board_size):
            return None
        col = int((x - bx) / self.square_size)
        row = int((y - by) / self.square_size)
        return chess.square(col, row)

    def chess_square_to_ui_pos(self, sq):
        file = chess.square_file(sq)
        rank = chess.square_rank(sq)
        x = self.board_origin[0] + file * self.square_size
        y = self.board_origin[1] + rank * self.square_size
        return (x, y)

    def highlight_legal_moves(self, piece_widget):
        self.clear_highlights()
        from_sq = piece_widget.chess_square
        self.legal_moves = [move for move in self.game_board.legal_moves if move.from_square == from_sq]
        with self.canvas:
            for move in self.legal_moves:
                pos = self.chess_square_to_ui_pos(move.to_square)
                if self.game_board.is_capture(move):
                    Color(1, 0, 0, 0.5)
                else:
                    Color(0, 1, 0, 0.5)
                rect = Rectangle(pos=pos, size=(self.square_size, self.square_size))
                self.highlight_rects.append(rect)

    def clear_highlights(self):
        for rect in self.highlight_rects:
            self.canvas.remove(rect)
        self.highlight_rects = []

    def execute_move(self, legal_move):
        san_move = self.game_board.san(legal_move)
        self.game_board.push(legal_move)
        self.selected_piece.chess_square = legal_move.to_square
        self.selected_piece.update_position()

        for child in list(self.children):
            if (isinstance(child, ChessPiece) and child is not self.selected_piece and
                child.chess_square == legal_move.to_square):
                self.remove_widget(child)
                if self.captured_panel:
                    child.size_hint = (None, None)
                    scale = 0.8
                    child.size = (self.square_size * scale, self.square_size * scale)
                    self.captured_panel.add_widget(child)

        self.clear_highlights()
        self.selected_piece.selected = False
        self.selected_piece = None
        self.legal_moves = []
        self.add_piece_widgets()
        if self.move_list_container:
            label = Label(text=san_move, size_hint_y=None, height=30, font_size=24)
            self.move_list_container.add_widget(label)

    def on_touch_down(self, touch):
        bx, by = self.board_origin
        if not (bx <= touch.x <= bx + self.board_size and by <= touch.y <= by + self.board_size):
            return False

        dest_sq = self.ui_to_chess_square(touch.x, touch.y)

        if self.selected_piece and dest_sq is not None:
            for move in self.legal_moves:
                if move.to_square == dest_sq:
                    print(f"Executing move: {move}")
                    self.execute_move(move)
                    return True

        touched_piece = None
        for child in self.children:
            if isinstance(child, ChessPiece) and child.collide_point(touch.x, touch.y):
                touched_piece = child
                break

        if touched_piece:
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

        if self.selected_piece:
            self.selected_piece.selected = False
            self.selected_piece = None
            self.clear_highlights()
            return True

        return False

    def reset(self):
        self.game_board.reset()
        self.add_piece_widgets()

    def fen_to_board(self, fen):
        try:
            # Create a new board with the given FEN string.
            self.game_board = chess.Board(fen)
            self.add_piece_widgets()
        except Exception as e:
            raise ValueError("Invalid FEN string") from e


# ------------------------------------------------------------
# ChessGameWidget: the root widget that arranges the board, move list, captured pieces, and FEN controls.
# ------------------------------------------------------------
class ChessGameWidget(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # --- Define panel sizes ---
        panel_width = 200  # for captured pieces (left) and move list (right)
        screen_width = 1920
        screen_height = 1080

        board_size = min(screen_height, screen_width - 2 * panel_width)
        self.square_size = board_size / 8

        board_origin_x = panel_width + ((screen_width - 2 * panel_width - board_size) / 2) + self.square_size
        board_origin_y = ((screen_height - board_size) / 2) + self.square_size
        board_origin = (board_origin_x, board_origin_y)

        # --- Captured pieces panel (left side) ---
        self.captured_panel = BoxLayout(
            orientation='vertical',
            size_hint=(None, 1),
            width=panel_width,
            pos=(0, 0)
        )
        self.captured_panel.add_widget(Label(text="Captured", size_hint_y=None, height=40, font_size=FONT_SIZE))
        self.add_widget(self.captured_panel)

        # --- Move list panel (right side) ---
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

        # --- Chess board ---
        self.chess_board = ChessBoard(board_origin=board_origin, board_size=board_size)
        self.chess_board.captured_panel = self.captured_panel
        self.chess_board.move_list_container = self.move_list_container
        self.add_widget(self.chess_board)

        # --- Move input box ---
        self.move_input = TextInput(
            size_hint=(None, None),
            size=(panel_width, 40),
            pos=(screen_width - panel_width, 0),
            multiline=False
        )
        self.move_input.bind(on_text_validate=self.on_move_entered)
        self.add_widget(self.move_input)

        # --- FEN control panel ---
        self.fen_control_panel = BoxLayout(
            orientation='horizontal',
            size_hint=(None, None),
            size=(screen_width - 2 * panel_width, 60),
            pos=(panel_width, screen_height - 60)
        )
        self.fen_input = TextInput(
            hint_text="Enter FEN string",
            font_size=FONT_SIZE,
            size_hint_x=0.4
        )
        self.load_fen_button = Button(
            text="Load FEN",
            font_size=FONT_SIZE,
            size_hint_x=0.15
        )
        self.export_fen_button = Button(
            text="Export FEN",
            font_size=FONT_SIZE,
            size_hint_x=0.15
        )
        self.reset_board_button = Button(
            text="Reset Board",
            font_size=FONT_SIZE,
            size_hint_x=0.15
        )
        self.fen_output_label = Label(
            text="",
            font_size=FONT_SIZE,
            size_hint_x=0.15,
            pos_hint={'right': 1}
        )
        self.load_fen_button.bind(on_release=self.load_fen)
        self.export_fen_button.bind(on_release=self.export_fen)
        self.reset_board_button.bind(on_release=self.reset_board)

        self.fen_control_panel.add_widget(self.fen_input)
        self.fen_control_panel.add_widget(self.load_fen_button)
        self.fen_control_panel.add_widget(self.export_fen_button)
        self.fen_control_panel.add_widget(self.reset_board_button)
        self.fen_control_panel.add_widget(self.fen_output_label)
        self.add_widget(self.fen_control_panel)

    def on_move_entered(self, instance):
        move_str = instance.text
        try:
            move = chess.Move.from_uci(move_str)
            if move not in self.chess_board.game_board.legal_moves:
                move = self.chess_board.game_board.parse_san(move_str)
            
            if move in self.chess_board.game_board.legal_moves:
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
        label = Label(text=message, size_hint_y=None, height=40)
        self.move_list_container.add_widget(label)

    def load_fen(self, instance):
        fen = self.fen_input.text.strip()
        try:
            self.chess_board.fen_to_board(fen)
        except ValueError:
            self.add_debug_message("Invalid FEN string")
        
    def export_fen(self, instance):
        fen = self.chess_board.game_board.fen()
        self.fen_output_label.text = fen

    def reset_board(self, instance):
        self.chess_board.reset()


# ------------------------------------------------------------
# The App
# ------------------------------------------------------------
class ChessApp(App):
    def build(self):
        return ChessGameWidget()


if __name__ == '__main__':
    ChessApp().run()
