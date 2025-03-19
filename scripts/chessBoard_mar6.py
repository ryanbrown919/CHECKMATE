
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
    def __init__(self, bottom_colour_white=True, game_logic=None, touch_enabled=True, board_origin=100, board_size=100, **kwargs,):
        """
        board_origin: (x, y) bottom‑left corner of the board
        board_size: size in pixels (assumed square)
        """
        super(ChessBoard, self).__init__(**kwargs)
        self.size_hint = (1, 1)

        #board_size = min(self.width, self.height)

        #Clock.schedule_once(self.setup_layout, 0)
        self.bind(pos=self._update_subcomponents, size=self._update_subcomponents)


        # Center the board within this widget:
        self.board_origin = self.pos
        self.board_size = self.size
        self.square_size = board_size / 8.0

        # These will be set later by the parent container:
        self.captured_panel = None      # widget where captured pieces are displayed (left side)
        self.move_list_container = None # BoxLayout inside the ScrollView for moves

        # For highlighting legal moves
        self.highlight_rects = []
        self.legal_moves = []
        self.selected_piece = None
        self.bottom_colour_white = bottom_colour_white


        # Create the python‑chess board with the standard starting

        self.game_logic = game_logic

        if self.game_logic is None:
            print("No game logic provided. Creating a new game logic instance.")
            self.game_logic = gameLogic()
        else:
            print('Game Logic detected')
            pass

        self.game_board = self.game_logic.game_board
        self.game_logic.register_observer(self.update_board)

        self.draw_board_background()

        # Place piece widgets on top.
        self.add_piece_widgets()

        # Add row and column labels
        self.add_labels()

    def _update_subcomponents(self, *args):
        """
        This method is called every time the widget's position or size changes.
        It updates the subcomponent(s) so they know the current geometry.
        """
        # Update the subcomponent to fill the entire widget.
        # In a real application, you might adjust offsets or use more complex layouts.
        self.my_child.pos = self.pos
        self.my_child.size = self.size
        print("Updated subcomponent: pos =", self.my_child.pos, "size =", self.my_child.size)

            



    def draw_board_background(self):
        """
        Draw an 8x8 grid of alternating colored squares using canvas.before.
        The coloring pattern is determined using canonical coordinates;
        if bottom_colour_white is False, the colors flip accordingly.
        """
        with self.canvas.before:
            for file in range(8):
                for rank in range(8):
                    # Get the canonical square index.
                    sq = self.game_logic.square(file, rank)
                    pos = self.chess_square_to_ui_pos(sq)
                    print("debug yo")
                    print(sq, pos)

                    # Decide on color based on canonical (file, rank).
                    # For a white-bottom board: dark if (file+rank) is even; for black-bottom, reverse the colors.
                    if (file + rank) % 2 == 0:
                        color = (189/255, 100/255, 6/255, 1) if self.bottom_colour_white else (247/255, 182/255, 114/255, 1)
                    else:
                        color = (247/255, 182/255, 114/255, 1) if self.bottom_colour_white else (189/255, 100/255, 6/255, 1)
                    Color(*color)
                    Rectangle(pos=pos, size=(self.square_size, self.square_size))

    def add_labels(self):
        """
        Add row (1–8) and column (a–h) labels around the board.
        The labels are placed using the same coordinate transformation so that
        they appear in the correct order for the given perspective.
        """
        # COLUMN LABELS
        # For white's perspective, bottom row is canonical rank 0; for black's, bottom is canonical rank 7.
        bottom_rank = 0 if self.bottom_colour_white else 7

        # Determine the file order for label placement:
        # For white's perspective, files 0-7 map to a-h.
        # For black's perspective, the board is flipped so the leftmost displayed square corresponds to canonical file 7.
        file_order = list(range(8)) if self.bottom_colour_white else list(reversed(range(8)))
        for file in file_order:
            # The label text remains 'a' to 'h'. When the board is flipped, reversing the file order will naturally swap them.
            label_text = chr(ord('a') + file)
            # Compute the position for the square in the bottom row.
            sq = self.game_logic.square(file, bottom_rank)
            pos = self.chess_square_to_ui_pos(sq)
            # Offset the label so it sits centered below the square.
            label_x = pos[0] + self.square_size / 2 - self.square_size / 4
            label_y = pos[1] - self.square_size
            label = Label(text=label_text, size_hint=(None, None),
                          size=(self.square_size, self.square_size),
                          pos=(label_x, label_y))
            self.add_widget(label)

        # ROW LABELS
        # For white's perspective, the leftmost column is canonical file 0; for black's, it's canonical file 7.
        left_file = 0 if self.bottom_colour_white else 7
        # For row labels, iterate over canonical ranks in order or reversed order.
        rank_order = list(range(8)) if self.bottom_colour_white else list(reversed(range(8)))
        for rank in rank_order:
            # The label should be 1-8 based on the canonical rank.
            label_text = str(rank + 1)
            sq = self.game_logic.square(left_file, rank)
            pos = self.chess_square_to_ui_pos(sq)
            # Offset the label so it appears to the left of the board.
            label_x = pos[0] - self.square_size
            label_y = pos[1] + self.square_size / 2 - self.square_size / 4
            label = Label(text=label_text, size_hint=(None, None),
                          size=(self.square_size, self.square_size),
                          pos=(label_x, label_y))
            self.add_widget(label)

    def add_piece_widgets(self):
        """Remove any existing ChessPiece widgets and add one for every piece on the board."""
        for child in list(self.children):
            if isinstance(child, ChessPiece):
                self.remove_widget(child)

        for sq in self.game_logic.SQUARES:
            piece = self.game_board.piece_at(sq)
            if piece is not None:
                symbol = piece.symbol()  # e.g., 'P' or 'k'
                # if not self.bottom_colour_white and symbol.islower():
                #     # White on the bottom
                #     symbol = symbol.upper()
                #     # If the piece is black, convert to lowercase
                # elif not self.bottom_colour_white and symbol.isupper():
                #     symbol = symbol.lower()
                if symbol in piece_images:
                    source = piece_images[symbol]
                    pos = self.chess_square_to_ui_pos(sq)
                    piece_widget = ChessPiece(
                        game_logic=self.game_logic,
                        chess_square=sq,
                        piece_symbol=symbol,
                        square_size=self.square_size,
                        board_origin=self.board_origin,
                        source=source
                    )
                    piece_widget.pos = pos
                    self.add_widget(piece_widget)

    def ui_to_chess_square(self, x, y):
        """Convert a UI (x, y) coordinate to a canonical chess square index (0-63)."""
        bx, by = self.board_origin
        if not (bx <= x <= bx + self.board_size and by <= y <= by + self.board_size):
            return None

        # Compute file and rank based on the UI coordinate.
        if self.bottom_colour_white:
            file = int((x - bx) / self.square_size)
            rank = int((y - by) / self.square_size)
        else:
            # If the board is flipped, invert the calculation.
            file = 7 - int((x - bx) / self.square_size)
            rank = 7 - int((y - by) / self.square_size)
            
        return self.game_logic.square(file, rank)

    def chess_square_to_ui_pos(self, sq):
        """Convert a chess square index to a UI (x, y) position.
        Applies a transformation if the board is rendered with black at the bottom.
        """
        # Get canonical file and rank (0-7)
        file = self.game_logic.square_file(sq)
        rank = self.game_logic.square_rank(sq)
        
        # If black is at the bottom, flip the coordinates.
        if not self.bottom_colour_white:
            file = 7 - file
            rank = 7 - rank

        x = self.board_origin[0] + file * self.square_size
        y = self.board_origin[1] + rank * self.square_size
        return (x, y)


    def highlight_legal_moves(self, square_list):

        self.clear_highlights()
        with self.canvas:
            for move in square_list:
                pos = self.chess_square_to_ui_pos(move.to_square)
                if self.game_board.is_capture(move):
                    Color(1, 0, 0, 0.5)  # red for captures
                else:
                    Color(0, 1, 0, 0.5)  # green for non-captures
                rect = Rectangle(pos=pos, size=(self.square_size, self.square_size))
                self.highlight_rects.append(rect)



    # Need to abstract this out to game_logic but keep all canvas manipulations here
    # def highlight_legal_moves(self, piece_widget):
    #     """Highlight all legal moves for the given piece using python‑chess.
    #        Capture moves are highlighted in red; non-captures in green.
    #     """
    #     self.clear_highlights()
    #     from_sq = piece_widget.chess_square
    #     self.legal_moves = [move for move in self.game_board.legal_moves if move.from_square == from_sq]
    #     with self.canvas:
    #         for move in self.legal_moves:
    #             pos = self.chess_square_to_ui_pos(move.to_square)
    #             if self.game_board.is_capture(move):
    #                 Color(1, 0, 0, 0.5)  # red for captures
    #             else:
    #                 Color(0, 1, 0, 0.5)  # green for non-captures
    #             rect = Rectangle(pos=pos, size=(self.square_size, self.square_size))
    #             self.highlight_rects.append(rect)

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
        # Check that the touch is within the board.
        if not (bx <= touch.x <= bx + self.board_size and by <= touch.y <= by + self.board_size):
            return False

        dest_sq = self.ui_to_chess_square(touch.x, touch.y)
        # If a piece is already selected and the destination is a legal move:
        if self.selected_piece and dest_sq is not None:
            for move in self.legal_moves:
                if move.to_square == dest_sq:
                    # Delegate the move execution to the game logic.
                    self.game_logic.make_move(move)
                    self.selected_piece.selected = False
                    self.selected_piece = None
                    self.legal_moves = []
                    self.clear_highlights()
                    return True

        # Check if a ChessPiece widget was touched.
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
                # Select this piece and fetch its legal moves from the game logic.
                if self.selected_piece:
                    self.selected_piece.selected = False
                self.selected_piece = touched_piece
                touched_piece.selected = True
                self.legal_moves = self.game_logic.select_piece(touched_piece.chess_square)
                self.clear_highlights()
                self.highlight_legal_moves(self.legal_moves)
            return True

        # If no piece was touched but one was selected, then clear the selection.
        if self.selected_piece:
            self.selected_piece.selected = False
            self.selected_piece = None
            self.clear_highlights()
            return True

        return False

    # def on_touch_down(self, touch):
    #     bx, by = self.board_origin
    #     # Only consider touches inside the board area.
    #     if not (bx <= touch.x <= bx + self.board_size and by <= touch.y <= by + self.board_size):
    #         return False

    #     # First, get the destination square regardless of widgets.
    #     dest_sq = self.ui_to_chess_square(touch.x, touch.y)

    #     # If a piece is already selected and the touched square is one of its legal move destinations, execute the move.
    #     if self.selected_piece and dest_sq is not None:
    #         for move in self.legal_moves:
    #             if move.to_square == dest_sq:
    #                 print(f"Executing move: {move}")
    #                 self.execute_move(move)
    #                 return True

    #     # Otherwise, check if a piece was touched.
    #     touched_piece = None
    #     for child in self.children:
    #         if isinstance(child, ChessPiece) and child.collide_point(touch.x, touch.y):
    #             touched_piece = child
    #             break

    #     if touched_piece:
    #         # If the same piece is touched twice, deselect it.
    #         if self.selected_piece == touched_piece:
    #             self.selected_piece.selected = False
    #             self.selected_piece = None
    #             self.clear_highlights()
    #         else:
    #             move_list = self.select_piece(touched_piece.chess_square)
    #             #self.selected_piece = touched_piece
    #             touched_piece.selected = True
    #             self.clear_highlights()

    #             self.highlight_legal_moves(move_list)
    #         return True

    #     # If no piece is touched and a piece is selected, deselect it.
    #     if self.selected_piece:
    #         self.selected_piece.selected = False
    #         self.selected_piece = None
    #         self.clear_highlights()
    #         return True

    #     return False
    
    def select_piece(self, square):
        legal_moves = self.game_logic.select_piece(square)
        self.highlight_legal_moves(legal_moves)
    
    def reset(self):
        self.game_board.reset()
        self.add_piece_widgets()
    
    def fen_to_board(self, fen):
        self.game_board.reset()
        self.game_board = self.game_logic.create_fen(fen)
        self.add_piece_widgets()
    
    def update_board(self):
        """Called by the game logic when the state changes."""
        self.clear_highlights()
        # Clear existing piece widgets, then re-add them based on game_logic.board state.
        #self.remove_piece_widgets()  # Assume you implement this method
        self.add_piece_widgets()



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