import chess
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock

# External game logic (assumed to be defined in game_logic.py)
from game_logic import GameLogic

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
    def __init__(self, chess_square, piece_symbol, game_logic, **kwargs):
        super(ChessPiece, self).__init__(**kwargs)
        self.chess_square = chess_square  # chess square index (0-63)
        self.piece_symbol = piece_symbol
        self.game_logic = game_logic
        self.selected = False
        self.allow_stretch = True
        self.keep_ratio = True
        # We use absolute positioning; size and pos will be set by the parent ChessBoard.
        self.size_hint = (None, None)

# ------------------------------------------------------------
# ChessBoard: a self-contained widget that draws a 10×10 grid.
#
# • The central 8×8 cells form the chessboard.
# • The left column displays row labels.
# • The bottom row displays column labels.
# • The board background is drawn via canvas.before.
# • Chess pieces are added as children and positioned absolutely.
# • Legal move highlights are drawn via canvas.after.
# • Touch handling is built in (and can be disabled via a constructor argument).
# ------------------------------------------------------------
class ChessBoard(Widget):

    def __init__(self, bottom_colour_white=True, game_logic=None, touch_enabled_white=True, touch_enabled_black=True, **kwargs):
        super(ChessBoard, self).__init__(**kwargs)
        self.bottom_colour_white = bottom_colour_white
        self.touch_enabled_white=touch_enabled_white
        self.touch_enabled_black=touch_enabled_black

        # External game logic
        self.game_logic = game_logic if game_logic is not None else GameLogic()
        self.board = self.game_logic.board
        self.game_logic.register_observer(self.update_board)

        # For tracking selected piece and legal moves.
        self.selected_piece = None
        self.legal_moves = []
        self.highlight_rects = []  # to store (Color, Rectangle) tuples

        # We'll store references to label widgets for row and column labels.
        self.row_labels = []
        self.col_labels = []

        # Bind changes so that our canvas (background, labels, pieces, highlights) updates.
        self.bind(pos=self._update_canvas, size=self._update_canvas)

        # Delay initial board update until layout is done.
        Clock.schedule_once(lambda dt: self.update_board(), 0)

    def _update_canvas(self, *args):
        # Clear the background canvas.
        self.canvas.before.clear()

        # Compute cell size using a 10x10 grid.
        cell_size = min(self.width, self.height) / 10.0

        # The central 8x8 chessboard is offset by one cell from the left and bottom.
        board_origin = (self.x + cell_size, self.y + cell_size)
        board_size = cell_size * 8

        # Draw the chessboard squares (the 8x8 area) in canvas.before.
        with self.canvas.before:
            for file in range(8):
                for rank in range(8):
                    # Use alternating colors.
                    if (file + rank) % 2 == 0:
                        col = (189/255, 100/255, 6/255, 1) if self.bottom_colour_white else (247/255, 182/255, 114/255, 1)
                    else:
                        col = (247/255, 182/255, 114/255, 1) if self.bottom_colour_white else (189/255, 100/255, 6/255, 1)
                    Color(*col)
                    # Adjust rank for perspective.
                    if self.bottom_colour_white:
                        pos_y = board_origin[1] + rank * cell_size
                    else:
                        pos_y = board_origin[1] + (7 - rank) * cell_size
                    pos_x = board_origin[0] + file * cell_size
                    Rectangle(pos=(pos_x, pos_y), size=(cell_size, cell_size))

        # Clear and re-add the labels.
        for label in self.row_labels + self.col_labels:
            if label.parent:
                self.remove_widget(label)
        self.row_labels = []
        self.col_labels = []

        # Add row labels in the left margin.
        for i in range(8):
            if self.bottom_colour_white:
                label_text = str(8 - i)
            else:
                label_text = str(i + 1)
            label = Label(text=label_text, halign="center", valign="middle")
            label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
            if self.bottom_colour_white:
                pos_y = board_origin[1] + i * cell_size
            else:
                pos_y = board_origin[1] + (7 - i) * cell_size
            label.pos = (self.x, pos_y)
            label.size = (cell_size, cell_size)
            self.add_widget(label)
            self.row_labels.append(label)

        # Add column labels in the bottom margin.
        for i in range(8):
            label_text = chr(ord('a') + i)
            label = Label(text=label_text, halign="center", valign="middle")
            label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
            label.pos = (board_origin[0] + i * cell_size, self.y)
            label.size = (cell_size, cell_size)
            self.add_widget(label)
            self.col_labels.append(label)

        # Update positions and sizes of chess piece widgets.
        for child in self.children:
            if isinstance(child, ChessPiece):
                sq = child.chess_square
                file = sq % 8
                rank = sq // 8
                if self.bottom_colour_white:
                    pos_y = board_origin[1] + rank * cell_size
                else:
                    pos_y = board_origin[1] + (7 - rank) * cell_size
                pos_x = board_origin[0] + file * cell_size
                child.pos = (pos_x, pos_y)
                child.size = (cell_size, cell_size)

        # Redraw legal move highlights (if any).
        self._redraw_highlights(cell_size, board_origin)

    def _redraw_highlights(self, cell_size, board_origin):
        # Clear existing highlight instructions.
        self.clear_highlights()
        # Draw new highlights for each legal move.
        for move in self.legal_moves:
            file = move.to_square % 8
            rank = move.to_square // 8
            if self.bottom_colour_white:
                pos_y = board_origin[1] + rank * cell_size
            else:
                pos_y = board_origin[1] + (7 - rank) * cell_size
            pos_x = board_origin[0] + file * cell_size
            # Choose color: red if capture, else green.
            if self.board.is_capture(move):
                col = (1, 0, 0, 0.5)
            else:
                col = (0, 1, 0, 0.5)
            # Create highlight instructions in canvas.after.
            col_inst = Color(*col)
            rect_inst = Rectangle(pos=(pos_x, pos_y), size=(cell_size, cell_size))
            self.canvas.after.add(col_inst)
            self.canvas.after.add(rect_inst)
            self.highlight_rects.append((col_inst, rect_inst))

    def clear_highlights(self):
        # Remove previously added highlight instructions.
        for (col_inst, rect_inst) in self.highlight_rects:
            if col_inst in self.canvas.after.children:
                self.canvas.after.remove(col_inst)
            if rect_inst in self.canvas.after.children:
                self.canvas.after.remove(rect_inst)
        self.highlight_rects = []

    def update_board(self, *args):
        # Remove old chess pieces.
        pieces_to_remove = [child for child in self.children if isinstance(child, ChessPiece)]
        for piece in pieces_to_remove:
            self.remove_widget(piece)
        # Add new chess pieces based on external game logic.
        for sq in self.game_logic.SQUARES:
            piece = self.board.piece_at(sq)
            if piece is not None:
                symbol = piece.symbol()
                if symbol in piece_images:
                    source = piece_images[symbol]
                    piece_widget = ChessPiece(chess_square=sq,
                                              piece_symbol=symbol,
                                              game_logic=self.game_logic,
                                              source=source)
                    piece_widget.size_hint = (None, None)
                    self.add_widget(piece_widget)
        # Force a canvas update.
        self._update_canvas()

    def on_touch_down(self, touch):
        # Check overall touch enablement (optional; if you want a global override you could keep this)
        if not (self.touch_enabled_white or self.touch_enabled_black):
            return super(ChessBoard, self).on_touch_down(touch)
        # Compute cell size and board origin.
        cell_size = min(self.width, self.height) / 10.0
        board_origin = (self.x + cell_size, self.y + cell_size)
        board_area = (board_origin[0], board_origin[1], cell_size * 8, cell_size * 8)
        # If touch is outside board, ignore.
        if not (board_area[0] <= touch.x <= board_area[0] + board_area[2] and
                board_area[1] <= touch.y <= board_area[1] + board_area[3]):
            return super(ChessBoard, self).on_touch_down(touch)
        # Map touch to chess square.
        file = int((touch.x - board_origin[0]) / cell_size)
        rank = int((touch.y - board_origin[1]) / cell_size)
        if not self.bottom_colour_white:
            rank = 7 - rank
        sq = file + rank * 8

        # If a piece is already selected and this square is a legal move destination, execute the move.
        if self.selected_piece and self.legal_moves:
            for move in self.legal_moves:
                if move.to_square == sq:
                    move = move.uci()
                    print("Move: ", move)
                    self.game_logic.push_move(move)
                    #self.game_logic.push_move(chess.Move.from_uci(move))
                    self.selected_piece = None
                    self.legal_moves = []
                    self.clear_highlights()
                    self.update_board()
                    return True
        # Otherwise, select a piece if one exists at this square.
        piece_widget = None
        for child in self.children:
            if isinstance(child, ChessPiece) and child.chess_square == sq:
                piece_widget = child
                break
        if piece_widget:
            # Check if selection is allowed based on piece colour.
            # Uppercase -> white; lowercase -> black.
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
                # You might call game_logic.select_piece to update legal moves.
                self.legal_moves = self.game_logic.select_piece(piece_widget.chess_square)
                self.clear_highlights()
                self.highlight_legal_moves(self.legal_moves)
            return True

        return super(ChessBoard, self).on_touch_down(touch)

    def highlight_legal_moves(self, legal_moves):
        # Set our legal moves and trigger a canvas update to draw highlights.
        self.legal_moves = legal_moves
        self._update_canvas()

# ------------------------------------------------------------
# TestChessApp: builds an app with multiple ChessBoard instances to validate scaling.
# ------------------------------------------------------------
class TestChessApp(App):
    def build(self):
        root = BoxLayout(orientation='vertical')
        # Create two chess boards with different settings.
        with open('venv/key.txt', 'r') as f:
            api_key = f.read().strip()  # .strip() removes any extra whitespace or newline characters


        game_instance = GameLogic(token=api_key)        
        board1 = ChessBoard(touch_enabled_black=False, touch_enabled_white=True, bottom_colour_white=True, game_logic=game_instance, size_hint=(1, 0.5))
        board2 = ChessBoard(touch_enabled_black=True, touch_enabled_white=False, bottom_colour_white=False, game_logic=game_instance, size_hint=(1, 0.5))
        root.add_widget(board1)
        root.add_widget(board2)
        return root

if __name__ == '__main__':
    TestChessApp().run()
