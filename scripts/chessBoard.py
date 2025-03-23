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

# External game logic (assumed to be defined in game_logic.py)
#from scripts.game_logic_old import GameLogic

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

        # New: Store last move highlight instructions.
        self.last_move_rects = []

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

        # # Redraw legal move highlights (if any).
        # self._redraw_highlights(cell_size, board_origin)

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
        self.clear_last_move_highlights()
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
            self.canvas.before.add(col_inst)
            self.canvas.before.add(rect_inst)
            self.highlight_rects.append((col_inst, rect_inst))

        if self.game_logic.move_history:
            last_move_str = self.game_logic.move_history[-1]  # e.g., "e2e4"
            # Extract the two squares from the move string.
            squares = [last_move_str[:2], last_move_str[2:4]]
            for square in squares:
                index = self.notation_to_index(square)
                file = index % 8
                rank = index // 8
                if self.bottom_colour_white:
                    pos_y = board_origin[1] + rank * cell_size
                else:
                    pos_y = board_origin[1] + (7 - rank) * cell_size
                pos_x = board_origin[0] + file * cell_size
                # Use blue for last move highlighting.
                col = (191/255, 128/255, 1, 0.5) 
                col_inst = Color(*col)
                rect_inst = Rectangle(pos=(pos_x, pos_y), size=(cell_size, cell_size))
                self.canvas.before.add(col_inst)
                self.canvas.before.add(rect_inst)
                self.last_move_rects.append((col_inst, rect_inst))

    def clear_highlights(self):
        # Remove previously added highlight instructions.
        for (col_inst, rect_inst) in self.highlight_rects:
            if col_inst in self.canvas.after.children:
                self.canvas.before.remove(col_inst)
            if rect_inst in self.canvas.after.children:
                self.canvas.before.remove(rect_inst)
        self.highlight_rects = []

    def clear_last_move_highlights(self):
        for (col_inst, rect_inst) in self.last_move_rects:
            if col_inst in self.canvas.after.children:
                self.canvas.before.remove(col_inst)
            if rect_inst in self.canvas.after.children:
                self.canvas.before.remove(rect_inst)
        self.last_move_rects = []


    def notation_to_index(self, square_str):
        """
        Converts a square in chess notation (e.g. 'e2') into a 0-based board index.
        Assumes 'a1' corresponds to index 0, 'h8' to 63.
        """
        file = ord(square_str[0]) - ord('a')
        rank = int(square_str[1]) - 1
        return file + rank * 8

    # def highlight_last_move(self):
    #     """
    #     Highlights the last move from game_logic.move_list using blue, similar to the legal move highlights.
    #     Expects move_list entries to be in chess notation like 'e2e4'.
    #     """
    #     self.clear_last_move_highlights()
    #     if hasattr(self.game_logic, 'move_list') and self.game_logic.move_list:
    #         last_move_str = self.game_logic.move_list[-1]  # e.g. "e2e4"
    #         from_sq = self.notation_to_index(last_move_str[:2])
    #         to_sq = self.notation_to_index(last_move_str[2:4])
    #         cell_size = min(self.width, self.height) / 10.0
    #         board_origin = (self.x + cell_size, self.y + cell_size)
    #         blue_color = (0, 0, 1, 0.5)  # Semi-transparent blue
    #         for sq in (from_sq, to_sq):
    #             file = sq % 8
    #             rank = sq // 8
    #             if self.bottom_colour_white:
    #                 pos_y = board_origin[1] + rank * cell_size
    #             else:
    #                 pos_y = board_origin[1] + (7 - rank) * cell_size
    #             pos_x = board_origin[0] + file * cell_size
    #             col_inst = Color(*blue_color)
    #             rect_inst = Rectangle(pos=(pos_x, pos_y), size=(cell_size, cell_size))
    #             self.canvas.after.add(col_inst)
    #             self.canvas.after.add(rect_inst)
    #             self.last_move_rects.append((col_inst, rect_inst))

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

        #self.highlight_last_move()


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


class MovesHistory(ScrollView):
    """
    A scrollable view that displays past moves.
    """
    def __init__(self, game_logic, **kwargs):
        super().__init__(**kwargs)
        self.game_logic = game_logic
        # Here we register an observer if needed.
        self.game_logic.register_observer(self.update_moves)

        self.layout = BoxLayout(orientation='vertical')
        self.layout.bind(minimum_height=self.layout.setter('height'))
        self.add_widget(self.layout)

    def update_moves(self, *args):
        self.layout.clear_widgets()
        # Assume game_logic.move_history is a list of UCI move strings.
        for move in self.game_logic.move_history:
            move_label = Label(text=move, size_hint_y=None, height=30)
            self.layout.add_widget(move_label)
        self.scroll_y = 0

class CapturedPieces(Widget):
    def __init__(self, game_logic = None, rows=2, cols=8, **kwargs):
        super(CapturedPieces, self).__init__(**kwargs)
        self.rows = rows
        self.cols = cols
        self.game_logic = game_logic
        self.game_logic.register_observer(self.update_captured)
        # This will hold the list of captured piece symbols.
        self.captured_list = []
        # Redraw the board whenever position/size changes.
        self.bind(pos=self.draw_board, size=self.draw_board)

    def draw_board(self, *args):
        # Draw a simple 2x8 chessboard pattern as background.
        self.canvas.before.clear()
        cell_width = self.width / self.cols
        cell_height = cell_width * 2
        self.offset_y = (self.height - (self.rows * cell_height)) / 2

        #cell_height = self.height / self.rows
        for r in range(self.rows):
            for c in range(self.cols):
                # Alternate colors like a chessboard.
                color=(247/255, 182/255, 114/255, 1)
                with self.canvas.before:
                    Color(*color)
                    Rectangle(
                        pos=(self.x + c * cell_width, self.y + self.offset_y + r * cell_height),
                        size=(cell_width, cell_height)
                    )

    def update_captured(self, *args):
        """
        Update the board with captured pieces.
        :param captured_list: A list of piece symbols (e.g., ['p', 'N', ...])
        """
        self.captured_list = self.game_logic.captured_pieces
        # Remove any previously added piece images.
        self.clear_widgets()
        cell_width = self.width / self.cols
        cell_height = self.height / self.rows
        for idx, piece in enumerate(self.captured_list):
            row = idx // self.cols
            col = idx % self.cols
            source = piece_images.get(piece, '')
            img = Image(source=source, allow_stretch=True, keep_ratio=True)
            img.size = (cell_width, cell_height)
            # Basic positioning: one image per cell.
            # To place pieces between squares, adjust the computed pos below.
            # img.pos = (self.x + col * cell_width, self.y + row * cell_height)
            img.pos=(self.x + col * cell_width, self.y + self.offset_y + row * cell_height)
            self.add_widget(img)


class CapturedPiecesOld(GridLayout):
    """
    A horizontal box that displays icons (or labels) of captured pieces.
    """
    def __init__(self, game_logic, **kwargs):
        kwargs.setdefault('cols', 8)
        super(CapturedPieces, self).__init__(**kwargs)
        self.game_logic = game_logic
        self.game_logic.register_observer(self.update_captured)
        self.captured_list = self.game_logic.captured_pieces

        self.bg_color = (247/255, 182/255, 114/255, 1)

        self.size_hint_y = None
        self.bind(minimum_height=self.setter('height'))

    

        with self.canvas.before:
            Color(*self.bg_color)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


    def update_captured(self, board, game_state, *args):\
    
        Color(247/255, 182/255, 114/255, 1)
        Rectangle()

        self.clear_widgets()
        captured_list = self.game_logic.captured_pieces
        for piece in captured_list:
            piece_image = Image(source=f'{piece_images[piece]}', allow_stretch=True, keep_ratio=True, size_hint=(None, None))
            self.add_widget(piece_image)
            #piece_label = Label(text=piece, size_hint=(None, None), size=(40, 40))
            #self.add_widget(piece_label)

class MaterialBar(BoxLayout):
    """
    A custom widget that displays a horizontal bar.
    The left portion (black) and right portion (white) reflect material percentages.
    """
    def __init__(self, game_logic, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = 0.1
        self.black_percentage = 50
        self.white_percentage = 50
        self.black_score = ""
        self.white_score = ""
        self.game_logic = game_logic
        self.game_logic.register_observer(self.update_percentages)

        self.bind(pos=self.update_canvas, size=self.update_canvas)

        self.black_label = Label(text=f"{self.black_score}", color=(1, 1, 1, 1), font_size='16sp')
        # White's percentage label appears above the bar on the far right;
        # text color is black.
        self.white_label = Label(text=f"{self.white_score}", color=(0, 0, 0, 1), font_size='16sp')
        # Add the labels as children.
        self.add_widget(self.black_label)
        self.add_widget(self.white_label)

    def update_canvas(self, *args):
        # Clear the background canvas.
        self.canvas.before.clear()
        with self.canvas.before:
            # Draw the black portion on the left.
            Color(0, 0, 0, 1)
            black_width = self.width * self.black_percentage / 100.0
            Rectangle(pos=self.pos, size=(black_width, self.height))
            # Draw the white portion on the right.
            Color(1, 1, 1, 1)
            Rectangle(pos=(self.x + black_width, self.y), size=(self.width - black_width, self.height))
            
        # Update label texts.
        self.black_label.text = f"{self.black_score}"
        self.white_label.text = f"{self.white_score}"
        # Force texture update so we can get correct sizes.
        self.black_label.texture_update()
        self.white_label.texture_update()
        
        # Position the black label above the bar at the far left.
        # Use a small vertical offset (e.g., 5 pixels above).
        self.black_label.size = self.black_label.texture_size
        self.black_label.pos = (self.x, self.top + 5)
        
        # Position the white label above the bar at the far right.
        self.white_label.size = self.white_label.texture_size
        self.white_label.pos = (self.right - self.white_label.width, self.top + 5)

    def update_percentages(self, *args):
        self.white_value, self.black_value = self.game_logic.calculate_material(self.game_logic.board)

        if self.white_value < self.black_value:
            self.white_score = ""
            self.black_score = f"+{self.black_value - self.white_value}"

        elif self.black_value < self.white_value:
            self.black_score = ""
            self.white_score = f"+{self.white_value - self.black_value}"

        else:
            self.white_score = ""
            self.black_score = ""

        print(self.white_value, self.black_value)

        total = self.black_value + self.white_value
        self.black_percentage = self.black_value / total * 100
        self.white_percentage = self.white_value / total * 100
        self.update_canvas()


from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock

class PlayerClock(Widget):
    def __init__(self, side="white", clock_instance=None, timer_enabled=True, **kwargs):
        """
        :param side: "white" or "black" indicating which clock this is.
        :param clock_logic: An instance of clock_logic that provides:
                           - player1_time (for white) and player2_time (for black)
                           - active_player (1 for white, 2 for black)
                           - update(dt): updates the active player's time.
                           - format_time(seconds): returns a string formatted as mm:ss.
        :param timer_enabled: If True, display the timer countdown.
                              If False, display an arrow indicating the active side.
        """
        super(PlayerClock, self).__init__(**kwargs)
        self.side = side.lower()
        self.clock_logic = clock_instance
        self.timer_enabled = timer_enabled

        # Create a label to display the time or arrow.
        self.label = Label(text=self.get_initial_text(), font_size="40sp",
                           halign="center", valign="middle")
        self.add_widget(self.label)

        # Bind layout updates.
        self.bind(pos=self.update_layout, size=self.update_layout)

        # Schedule periodic updates.
        Clock.schedule_interval(self.update_clock, 0.5)

    def get_initial_text(self):
        if self.timer_enabled and self.clock_logic:
            if self.side == "white":
                return self.clock_logic.format_time(self.clock_logic.white_time)
            else:
                return self.clock_logic.format_time(self.clock_logic.black_time)
        # When timer is disabled, show no arrow initially.
        return ""

    def update_layout(self, *args):
        # Make the label fill this widget.
        self.label.size = self.size
        self.label.pos = self.pos
        self.label.text_size = self.label.size
        self.update_background()

    def update_background(self):
        # Clear existing background instructions.
        self.label.canvas.before.clear()
        with self.label.canvas.before:
            if self.is_active():
                # Active clock: dark background with light text.
                Color(0, 0, 0, 1)
                self.label.color = (1, 1, 1, 1)
            else:
                # Inactive clock: light background with dark text.
                Color(1, 1, 1, 1)
                self.label.color = (0, 0, 0, 1)
            Rectangle(pos=self.label.pos, size=self.label.size)

    def is_active(self):
        """
        Returns True if this clock is the active clock.
        For clock_logic, active_player==1 means white is active,
        and active_player==2 means black is active.
        """
        if not self.clock_logic:
            return False
        if self.side == "white":
            return self.clock_logic.active_player == 1
        else:
            return self.clock_logic.active_player == 2

    def update_clock(self, dt):
        if not self.clock_logic:
            return

        # Update the clock logic regardless of display mode.
        self.clock_logic.update(dt)

        if self.timer_enabled:
            # Update the label text with the formatted time.
            if self.side == "white":
                time_remaining = self.clock_logic.white_time
            else:
                time_remaining = self.clock_logic.black_time
            self.label.text = self.clock_logic.format_time(time_remaining)
        else:
            # When timer is disabled, display an arrow for the active clock.
            if ((self.side == "white" and self.clock_logic.active_player == 1) or
                (self.side == "black" and self.clock_logic.active_player == 2)):
                self.label.text = "➤"
            else:
                self.label.text = ""
        # Refresh the background to reflect active state.
        self.update_background()


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
