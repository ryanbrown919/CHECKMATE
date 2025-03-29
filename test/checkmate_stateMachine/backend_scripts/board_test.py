import chess
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, Rectangle
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock

# Map chess piece symbols to image file paths.
piece_images = {
    'P': 'assets/white_pawn.png',
    'R': 'assets/white_rook.png',
    'N': 'assets/white_knight.png',
    'B': 'assets/white_bishop.png',
    'Q': 'assets/white_queen.png',
    'K': 'assets/white_king.png',
    'p': 'assets/black_pawn.png',
    'r': 'assets/black_rook.png',
    'n': 'assets/black_knight.png',
    'b': 'assets/black_bishop.png',
    'q': 'assets/black_queen.png',
    'k': 'assets/black_king.png',
}

# ------------------------------------------------------------
# ChessPiece: widget representing one chess piece.
# ------------------------------------------------------------
class ChessPiece(Image):
    def __init__(self, chess_square, piece_symbol, backend, **kwargs):
        super(ChessPiece, self).__init__(**kwargs)
        self.chess_square = chess_square  # chess square index (0-63)
        self.piece_symbol = piece_symbol
        self.backend = backend
        self.selected = False
        self.allow_stretch = True
        self.keep_ratio = True
        # We use absolute positioning; size and pos will be set by the parent ChessBoard.
        self.size_hint = (None, None)

# ------------------------------------------------------------
# ChessBoard: a self-contained widget that draws a 10×10 grid.
#
# This version now uses the backend instance to:
# • Access the board state.
# • Register for updates.
# • Call push_move() when a legal move is selected.
# ------------------------------------------------------------
class ChessBoard(Widget):

    def __init__(self, bottom_colour_white=True, backend=None, touch_enabled_white=True, touch_enabled_black=True, **kwargs):
        super(ChessBoard, self).__init__(**kwargs)
        self.bottom_colour_white = bottom_colour_white
        self.touch_enabled_white = touch_enabled_white
        self.touch_enabled_black = touch_enabled_black

        # Use the provided backend (an instance of your ChessBackend).
        if backend is None:
            raise ValueError("A backend instance must be provided.")
        self.backend = backend
        self.board = self.backend.board
        self.backend.register_observer(self.update_board)

        # For tracking selected piece and legal moves.
        self.selected_piece = None
        self.legal_moves = []
        self.highlight_rects = []  # to store (Color, Rectangle) tuples
        self.last_move_rects = []

        self.row_labels = []
        self.col_labels = []

        # Bind changes so that our canvas updates.
        self.bind(pos=self._update_canvas, size=self._update_canvas)
        Clock.schedule_once(lambda dt: self.update_board(), 0)

    def _update_canvas(self, *args):
        self.canvas.before.clear()
        cell_size = min(self.width, self.height) / 10.0
        board_origin = (self.x + cell_size, self.y + cell_size)

        # Draw the chessboard squares.
        with self.canvas.before:
            for file in range(8):
                for rank in range(8):
                    if (file + rank) % 2 == 0:
                        col = (189/255, 100/255, 6/255, 1) if self.bottom_colour_white else (247/255, 182/255, 114/255, 1)
                    else:
                        col = (247/255, 182/255, 114/255, 1) if self.bottom_colour_white else (189/255, 100/255, 6/255, 1)
                    Color(*col)
                    pos_y = board_origin[1] + rank * cell_size if self.bottom_colour_white else board_origin[1] + (7 - rank) * cell_size
                    pos_x = board_origin[0] + file * cell_size
                    Rectangle(pos=(pos_x, pos_y), size=(cell_size, cell_size))

        # Remove and re-add labels.
        for label in self.row_labels + self.col_labels:
            if label.parent:
                self.remove_widget(label)
        self.row_labels = []
        self.col_labels = []
        for i in range(8):
            label_text = str(8 - i) if self.bottom_colour_white else str(i + 1)
            label = Label(text=label_text, halign="center", valign="middle")
            label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
            pos_y = board_origin[1] + i * cell_size if self.bottom_colour_white else board_origin[1] + (7 - i) * cell_size
            label.pos = (self.x, pos_y)
            label.size = (cell_size, cell_size)
            self.add_widget(label)
            self.row_labels.append(label)
        for i in range(8):
            label_text = chr(ord('a') + i)
            label = Label(text=label_text, halign="center", valign="middle")
            label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
            label.pos = (board_origin[0] + i * cell_size, self.y)
            label.size = (cell_size, cell_size)
            self.add_widget(label)
            self.col_labels.append(label)

        # Update chess piece positions.
        for child in self.children:
            if isinstance(child, ChessPiece):
                sq = child.chess_square
                file = sq % 8
                rank = sq // 8
                pos_y = board_origin[1] + rank * cell_size if self.bottom_colour_white else board_origin[1] + (7 - rank) * cell_size
                pos_x = board_origin[0] + file * cell_size
                child.pos = (pos_x, pos_y)
                child.size = (cell_size, cell_size)

        self._redraw_highlights(cell_size, board_origin)

    def _redraw_highlights(self, cell_size, board_origin):
        self.clear_highlights()
        self.clear_last_move_highlights()
        for move in self.legal_moves:
            file = move.to_square % 8
            rank = move.to_square // 8
            pos_y = board_origin[1] + rank * cell_size if self.bottom_colour_white else board_origin[1] + (7 - rank) * cell_size
            pos_x = board_origin[0] + file * cell_size
            col = (1, 0, 0, 0.5) if self.board.is_capture(move) else (0, 1, 0, 0.5)
            col_inst = Color(*col)
            rect_inst = Rectangle(pos=(pos_x, pos_y), size=(cell_size, cell_size))
            self.canvas.before.add(col_inst)
            self.canvas.before.add(rect_inst)
            self.highlight_rects.append((col_inst, rect_inst))
        if self.backend.move_history:
            last_move_str = self.backend.move_history[-1]
            squares = [last_move_str[:2], last_move_str[2:4]]
            for square in squares:
                index = self.notation_to_index(square)
                file = index % 8
                rank = index // 8
                pos_y = board_origin[1] + rank * cell_size if self.bottom_colour_white else board_origin[1] + (7 - rank) * cell_size
                pos_x = board_origin[0] + file * cell_size
                col_inst = Color(191/255, 128/255, 1, 0.5)
                rect_inst = Rectangle(pos=(pos_x, pos_y), size=(cell_size, cell_size))
                self.canvas.before.add(col_inst)
                self.canvas.before.add(rect_inst)
                self.last_move_rects.append((col_inst, rect_inst))

    def clear_highlights(self):
        for (col_inst, rect_inst) in self.highlight_rects:
            if col_inst in self.canvas.before.children:
                self.canvas.before.remove(col_inst)
            if rect_inst in self.canvas.before.children:
                self.canvas.before.remove(rect_inst)
        self.highlight_rects = []

    def clear_last_move_highlights(self):
        for (col_inst, rect_inst) in self.last_move_rects:
            if col_inst in self.canvas.before.children:
                self.canvas.before.remove(col_inst)
            if rect_inst in self.canvas.before.children:
                self.canvas.before.remove(rect_inst)
        self.last_move_rects = []

    def notation_to_index(self, square_str):
        file = ord(square_str[0]) - ord('a')
        rank = int(square_str[1]) - 1
        return file + rank * 8

    def update_board(self, *args):
        # Remove old chess pieces.
        pieces_to_remove = [child for child in self.children if isinstance(child, ChessPiece)]
        for piece in pieces_to_remove:
            self.remove_widget(piece)
        # Add new chess pieces based on the backend board state.
        for sq in chess.SQUARES:
            piece = self.backend.board.piece_at(sq)
            if piece is not None:
                symbol = piece.symbol()
                if symbol in piece_images:
                    source = piece_images[symbol]
                    piece_widget = ChessPiece(chess_square=sq, piece_symbol=symbol, backend=self.backend, source=source)
                    piece_widget.size_hint = (None, None)
                    self.add_widget(piece_widget)
        self._update_canvas()

    def on_touch_down(self, touch):
        cell_size = min(self.width, self.height) / 10.0
        board_origin = (self.x + cell_size, self.y + cell_size)
        board_area = (board_origin[0], board_origin[1], cell_size * 8, cell_size * 8)
        if not (board_area[0] <= touch.x <= board_area[0] + board_area[2] and
                board_area[1] <= touch.y <= board_origin[1] + cell_size * 8):
            return super(ChessBoard, self).on_touch_down(touch)
        file = int((touch.x - board_origin[0]) / cell_size)
        rank = int((touch.y - board_origin[1]) / cell_size)
        if not self.bottom_colour_white:
            rank = 7 - rank
        sq = file + rank * 8

        # If a piece is selected and this square is a legal move destination, execute it.
        if self.selected_piece and self.legal_moves:
            for move in self.legal_moves:
                if move.to_square == sq:
                    move_uci = move.uci()
                    print("Move: ", move_uci)
                    self.backend.push_move(move_uci)
                    self.selected_piece = None
                    self.legal_moves = []
                    self.clear_highlights()
                    self.update_board()
                    return True

        # Otherwise, select a piece.
        piece_widget = None
        for child in self.children:
            if isinstance(child, ChessPiece) and child.chess_square == sq:
                piece_widget = child
                break
        if piece_widget:
            # Allow selection only if the correct color is enabled.
            if piece_widget.piece_symbol.isupper() and not self.touch_enabled_white:
                return True
            if piece_widget.piece_symbol.islower() and not self.touch_enabled_black:
                return True
            if self.selected_piece == piece_widget:
                self.selected_piece = None
                self.legal_moves = []
                self.clear_highlights()
            else:
                self.selected_piece = piece_widget
                self.legal_moves = self.backend.select_piece(piece_widget.chess_square)
                self.clear_highlights()
                self.highlight_legal_moves(self.legal_moves)
            return True

        return super(ChessBoard, self).on_touch_down(touch)

    def highlight_legal_moves(self, legal_moves):
        self.legal_moves = legal_moves
        self._update_canvas()

# ------------------------------------------------------------
# MovesHistory: a scrollable view that displays past moves.
# ------------------------------------------------------------
class MovesHistory(ScrollView):
    def __init__(self, backend, **kwargs):
        super().__init__(**kwargs)
        self.backend = backend
        self.backend.register_observer(self.update_moves)
        self.layout = BoxLayout(orientation='vertical')
        self.layout.bind(minimum_height=self.layout.setter('height'))
        self.add_widget(self.layout)

    def update_moves(self, *args):
        self.layout.clear_widgets()
        for move in self.backend.move_history:
            move_label = Label(text=move, size_hint_y=None, height=30)
            self.layout.add_widget(move_label)
        self.scroll_y = 0

# ------------------------------------------------------------
# CapturedPieces: displays captured piece images.
# ------------------------------------------------------------
class CapturedPieces(Widget):
    def __init__(self, backend, rows=2, cols=8, **kwargs):
        super(CapturedPieces, self).__init__(**kwargs)
        self.rows = rows
        self.cols = cols
        self.backend = backend
        self.backend.register_observer(self.update_captured)
        self.captured_list = []
        self.bind(pos=self.draw_board, size=self.draw_board)

    def draw_board(self, *args):
        self.canvas.before.clear()
        cell_width = self.width / self.cols
        cell_height = cell_width * 2
        self.offset_y = (self.height - (self.rows * cell_height)) / 2
        for r in range(self.rows):
            for c in range(self.cols):
                color = (247/255, 182/255, 114/255, 1)
                with self.canvas.before:
                    Color(*color)
                    Rectangle(
                        pos=(self.x + c * cell_width, self.y + self.offset_y + r * cell_height),
                        size=(cell_width, cell_height)
                    )

    def update_captured(self, *args):
        self.captured_list = self.backend.captured_pieces
        self.clear_widgets()
        cell_width = self.width / self.cols
        cell_height = self.height / self.rows
        for idx, piece in enumerate(self.captured_list):
            row = idx // self.cols
            col = idx % self.cols
            source = piece_images.get(piece, '')
            img = Image(source=source, allow_stretch=True, keep_ratio=True)
            img.size = (cell_width, cell_height)
            img.pos = (self.x + col * cell_width, self.y + self.offset_y + row * cell_height)
            self.add_widget(img)

# ------------------------------------------------------------
# MaterialBar: displays material advantage as a horizontal bar.
# ------------------------------------------------------------
class MaterialBar(BoxLayout):
    def __init__(self, backend, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = 0.1
        self.backend = backend
        self.backend.register_observer(self.update_percentages)
        self.black_percentage = 50
        self.white_percentage = 50
        self.black_score = ""
        self.white_score = ""
        self.bind(pos=self.update_canvas, size=self.update_canvas)
        self.black_label = Label(text=f"{self.black_score}", color=(1, 1, 1, 1), font_size='16sp')
        self.white_label = Label(text=f"{self.white_score}", color=(0, 0, 0, 1), font_size='16sp')
        self.add_widget(self.black_label)
        self.add_widget(self.white_label)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0, 0, 0, 1)
            black_width = self.width * self.black_percentage / 100.0
            Rectangle(pos=self.pos, size=(black_width, self.height))
            Color(1, 1, 1, 1)
            Rectangle(pos=(self.x + black_width, self.y), size=(self.width - black_width, self.height))
        self.black_label.text = f"{self.black_score}"
        self.white_label.text = f"{self.white_score}"
        self.black_label.texture_update()
        self.white_label.texture_update()
        self.black_label.size = self.black_label.texture_size
        self.black_label.pos = (self.x, self.top + 5)
        self.white_label.size = self.white_label.texture_size
        self.white_label.pos = (self.right - self.white_label.width, self.top + 5)

    def update_percentages(self, *args):
        self.white_value, self.black_value = self.backend.calculate_material(self.backend.board)
        if self.white_value < self.black_value:
            self.white_score = ""
            self.black_score = f"+{self.black_value - self.white_value}"
        elif self.black_value < self.white_value:
            self.black_score = ""
            self.white_score = f"+{self.white_value - self.black_value}"
        else:
            self.white_score = ""
            self.black_score = ""
        total = self.black_value + self.white_value
        self.black_percentage = self.black_value / total * 100
        self.white_percentage = self.white_value / total * 100
        self.update_canvas()

# ------------------------------------------------------------
# PlayerClock: displays a clock using a clock_logic instance.
# ------------------------------------------------------------
class PlayerClock(Widget):
    def __init__(self, side="white", clock_instance=None, **kwargs):
        super(PlayerClock, self).__init__(**kwargs)
        self.side = side.lower()
        self.clock_logic = clock_instance
        # self.timer_enabled = self.clock_logic.timer_enabled
        self.timer_enabled = False
        self.label = Label(text=self.get_initial_text(), font_size="40sp",
                           halign="center", valign="middle")
        self.add_widget(self.label)
        arrow_source = "assets/left_arrow.png" if self.side == "black" else "assets/right_arrow.png"
        self.arrow = Image(source=arrow_source, allow_stretch=True, keep_ratio=True, size_hint=(1,1))
        self.arrow.opacity = 0
        self.add_widget(self.arrow)
        self.bind(pos=self.update_layout, size=self.update_layout)
        Clock.schedule_interval(self.update_clock, 0.1)

    def get_initial_text(self):
        if self.timer_enabled and self.clock_logic:
            return self.clock_logic.format_time(self.clock_logic.white_time) if self.side == "white" else self.clock_logic.format_time(self.clock_logic.black_time)
        return ""

    def update_layout(self, *args):
        self.label.size = self.size
        self.label.pos = self.pos
        self.label.text_size = self.label.size
        arrow_size = (50, 50)
        self.arrow.size = arrow_size
        self.arrow.pos = (self.center_x - arrow_size[0] / 2, self.center_y - arrow_size[1] / 2)
        self.update_background()

    def update_background(self):
        self.label.canvas.before.clear()
        with self.label.canvas.before:
            if self.is_active():
                Color(1, 1, 1, 1)
                self.label.color = (0, 0, 0, 1)
            else:
                Color(0, 0, 0, 1)
                self.label.color = (1, 1, 1, 1)
            Rectangle(pos=self.label.pos, size=self.label.size)

    def is_active(self):
        if not self.clock_logic:
            return False
        return self.clock_logic.active_player == 1 if self.side == "white" else self.clock_logic.active_player == 2

    def update_clock(self, dt):
        if not self.clock_logic:
            return
        self.clock_logic.update(dt)
        if self.timer_enabled:
            self.arrow.opacity = 0
            time_remaining = self.clock_logic.white_time if self.side == "white" else self.clock_logic.black_time
            self.label.text = self.clock_logic.format_time(time_remaining)
        else:
            self.label.text = ""
            self.arrow.opacity = 1 if self.is_active() else 0
        self.update_background()

# ------------------------------------------------------------
# TestChessApp: builds an app using the backend.
# ------------------------------------------------------------
class TestChessApp(App):
    def build(self):
        root = BoxLayout(orientation='vertical')
        # Read API token from file.
        with open('venv/key.txt', 'r') as f:
            api_key = f.read().strip()

        # Import your updated backend.
        from game_control import ChessBackend  # Ensure your backend is accessible.
        # Create an instance of your backend.
        backend_instance = ChessBackend(
            lichess_token=api_key,
            ui_move_callback=lambda move: print("UI update with move:", move),
            mode="offline",
            engine_path="./bin/stockfish-macos-m1-apple-silicon",  # Adjust as needed.
            engine_time_limit=0.1,
            difficulty_level=5
        )
        backend_instance.start()

        board1 = ChessBoard(touch_enabled_black=False, touch_enabled_white=True, bottom_colour_white=True, backend=backend_instance, size_hint=(1, 0.5))
        board2 = ChessBoard(touch_enabled_black=True, touch_enabled_white=False, bottom_colour_white=False, backend=backend_instance, size_hint=(1, 0.5))
        moves_history = MovesHistory(backend=backend_instance, size_hint=(1, 0.3))
        material_bar = MaterialBar(backend=backend_instance, size_hint=(1, 0.1))
        # Assuming you have a clock_logic instance set up in your backend.
        player_clock_white = PlayerClock(side="white", clock_instance=backend_instance.clock_logic, size_hint=(1, 0.2))
        player_clock_black = PlayerClock(side="black", clock_instance=backend_instance.clock_logic, size_hint=(1, 0.2))
        
        root.add_widget(board1)
        root.add_widget(board2)
        root.add_widget(moves_history)
        root.add_widget(material_bar)
        root.add_widget(player_clock_white)
        root.add_widget(player_clock_black)
        return root

if __name__ == '__main__':
    TestChessApp().run()
