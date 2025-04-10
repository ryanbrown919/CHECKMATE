
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.uix.togglebutton import ToggleButton

import chess
import math



from kivy.lang import Builder

kv="""
<RoundedButton@Button>:
    background_color: 0,0,0,0  # the last zero is the critical on, make invisible
    canvas.before:
        Color:
            rgba: (.4,.4,.4,1) if self.state=='normal' else (0,.7,.7,1)  # visual feedback of press
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [25,]
"""
class RoundedButton(Button):
    pass

Builder.load_string(kv)


class IconButton(ButtonBehavior, Image):
    pass


class HorizontalLine(Widget):
    def __init__(self, **kwargs):
        super(HorizontalLine, self).__init__(**kwargs)
        # Disable automatic sizing on the y-axis and set a fixed height (e.g., 2 pixels)
        self.size_hint_y = None
        self.height = 2
        with self.canvas:
            # Set the line color (black in this example)
            Color(255, 255, 255, 1)
            # Draw a rectangle that will act as the horizontal line
            self.rect = Rectangle(pos=self.pos, size=self.size)
        # Bind updates so the rectangle resizes/repositions with the widget
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class VerticalLine(Widget):
    def __init__(self, **kwargs):
        super(VerticalLine, self).__init__(**kwargs)
        # Disable automatic sizing on the y-axis and set a fixed height (e.g., 2 pixels)
        self.size_hint_x = None
        self.width = 2
        with self.canvas:
            # Set the line color (black in this example)
            Color(255, 255, 255, 1)
            # Draw a rectangle that will act as the horizontal line
            self.rect = Rectangle(pos=self.pos, size=self.size)
        # Bind updates so the rectangle resizes/repositions with the widget
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class headerLayout(BoxLayout):
    def __init__(self, control_system, menu=False, **kwargs):
        # You can set orientation, size_hint, padding, etc.
        super(headerLayout, self).__init__(**kwargs)
        self.control_system = control_system
        self.font_size = self.control_system.title_font

        self.orientation='horizontal'
        self.padding=10
        self.spacing=0
        self.size_hint=(1, 0.2)
        icon = Image(source='assets/logo.png', allow_stretch=True, keep_ratio=True, size_hint=(0.1, 1))

        if not menu:
            self.add_widget(Label(text="CheckMATE", font_size=self.font_size, size_hint=(0.4, 1)))

            self.add_widget(Widget(size_hint_x=0.3))
            back_btn = IconButton(source="assets/back_arrow.png", 
                                                size_hint=(0.1, 0.8),  # Disable relative sizing
                                                        # Set explicit dimensions
                                                allow_stretch=True,      # Allow the image to stretch to fill the widget
                                                keep_ratio=True          # Maintain the image's aspect ratio
                                                )
            back_btn.bind(on_release = lambda instance: self.control_system.go_to_mainscreen())
            self.add_widget(back_btn)
            icon = Image(source='assets/logo.png', allow_stretch=True, keep_ratio=True, size_hint=(0.1, 1))

            self.add_widget(icon)

        else:
            self.add_widget(Label(text="Check-M.A.T.E", font_size=self.font_size, size_hint=(0.4, 1)))
            self.add_widget(Widget(size_hint_x=0.5))
            icon = Image(source='assets/logo.png', allow_stretch=True, keep_ratio=True, size_hint=(0.1, 1))
            self.add_widget(icon)



class ChessBoardWidget(Widget):
    def __init__(self, control_system, orientation='N', **kwargs):
        """
        orientation is kept for future extension, but here we always use white at the bottom (north up).
        """
        super(ChessBoardWidget, self).__init__(**kwargs)
        self.orientation = orientation  # reserved for future rotations if needed
        self.control_system = control_system
        self.selected_square = None  # e.g. "e4"
        self.row_labels = []
        self.col_labels = []
        self.bind(pos=self.update_canvas, size=self.update_canvas)
        Clock.schedule_once(lambda dt: self.update_canvas(), 0)

    def update_canvas(self, *args):
        # Clear previous canvas instructions and labels.
        self.canvas.before.clear()
        self.canvas.after.clear()
        for label in self.row_labels + self.col_labels:
            if label.parent:
                self.remove_widget(label)
        self.row_labels = []
        self.col_labels = []

        # Use a 10x10 grid to reserve a one-cell margin for labels.
        cell_size = min(self.width, self.height) / 10.0
        board_origin = (self.x + cell_size, self.y + cell_size)
        
        # Draw the 8x8 chessboard squares.
        with self.canvas.before:
            for file in range(8):
                for rank in range(8):
                    # Alternate colors.
                    if (file + rank) % 2 == 0:
                        col = (189/255, 100/255, 6/255, 1)
                    else:
                        col = (247/255, 182/255, 114/255, 1)
                    Color(*col)
                    pos_x = board_origin[0] + file * cell_size
                    pos_y = board_origin[1] + rank * cell_size
                    Rectangle(pos=(pos_x, pos_y), size=(cell_size, cell_size))
        
        # Add row labels (ranks 1 to 8, bottom to top).
        for i in range(8):
            label = Label(text=str(i + 1), halign="center", valign="middle")
            label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
            pos_y = board_origin[1] + i * cell_size
            label.pos = (self.x, pos_y)
            label.size = (cell_size, cell_size)
            self.add_widget(label)
            self.row_labels.append(label)
        
        # Add column labels (files a-h, left to right).
        for i in range(8):
            label = Label(text=chr(ord('a') + i), halign="center", valign="middle")
            label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
            pos_x = board_origin[0] + i * cell_size
            label.pos = (pos_x, self.y)
            label.size = (cell_size, cell_size)
            self.add_widget(label)
            self.col_labels.append(label)
        
        # Draw the highlight for the selected square (if any) in canvas.after.
        if self.selected_square:
            file, rank = self.square_to_indices(self.selected_square)
            pos_x = board_origin[0] + file * cell_size
            pos_y = board_origin[1] + rank * cell_size
            with self.canvas.after:
                Color(0, 0, 1, 0.5)  # semi-transparent blue highlight
                Rectangle(pos=(pos_x, pos_y), size=(cell_size, cell_size))

    def on_touch_down(self, touch):
        # Compute board area based on a 10x10 grid.
        cell_size = min(self.width, self.height) / 10.0
        board_origin = (self.x + cell_size, self.y + cell_size)
        board_rect = (board_origin[0], board_origin[1], cell_size * 8, cell_size * 8)
        
        # Ignore touches outside the board area.
        if not (board_rect[0] <= touch.x <= board_rect[0] + board_rect[2] and
                board_rect[1] <= touch.y <= board_rect[1] + board_rect[3]):
            return super(ChessBoardWidget, self).on_touch_down(touch)
        
        # Map touch to board square.
        file = int((touch.x - board_origin[0]) / cell_size)
        rank = int((touch.y - board_origin[1]) / cell_size)
        # Convert to algebraic notation (e.g., "a1" for bottom-left).
        square = chr(ord('a') + file) + str(rank + 1)
        
        # Toggle selection: unselect if already selected; otherwise, select new square.
        if self.selected_square == square:
            self.selected_square = None
        else:
            self.selected_square = square
        
        # Redraw the canvas to update the highlight.
        self.update_canvas()
        return True

    def square_to_indices(self, square):
        """
        Converts an algebraic square name (e.g., "e4") into file and rank indices (0-based).
        The lower-left (a1) is (0, 0) and upper-right (h8) is (7, 7).
        """
        file = ord(square[0]) - ord('a')
        rank = int(square[1]) - 1
        return file, rank


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

# External game logic (assumed to be defined in control_system.py)
#from scripts.control_system_old import GameLogic

# Map chess piece symbols to image file paths.
# piece_images = {
#     'P': 'assets/white_pawn.png',
#     'R': 'assets/white_rook.png',
#     'N': 'assets/white_knight.png',
#     'B': 'assets/white_bishop.png',
#     'Q': 'assets/white_queen.png',
#     'K': 'assets/white_king.png',
#     'p': 'assets/black_pawn.png',
#     'r': 'assets/black_rook.png',
#     'n': 'assets/black_knight.png',
#     'b': 'assets/black_bishop.png',
#     'q': 'assets/black_queen.png',
#     'k': 'assets/black_king.png',
#     'K_mate': 'assets/black_king_mate.png',
#     'K_check': 'assets/black_king_check.png',
#     'k_mate': 'assets/white_king_mate.png',
#     'k_check': 'assets/white_king_mate.png',

# }

# ------------------------------------------------------------
# ChessPiece: widget representing one chess piece.
# ------------------------------------------------------------
class ChessPiece(Image):
    def __init__(self, chess_square, piece_symbol, control_system, **kwargs):
        super(ChessPiece, self).__init__(**kwargs)
        self.chess_square = chess_square  # chess square index (0-63)
        self.piece_symbol = piece_symbol
        self.control_system = control_system
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

    def __init__(self, bottom_colour_white=True, control_system=None, touch_enabled_white=True, touch_enabled_black=True, **kwargs):
        super(ChessBoard, self).__init__(**kwargs)
        self.bottom_colour_white = bottom_colour_white
        self.touch_enabled_white=touch_enabled_white
        self.touch_enabled_black=touch_enabled_black

        # External game logic
        #self.control_system = control_system if control_system is not None else GameLogic()
        # self.control_system = control_system
        self.control_system = control_system
        self.board = self.control_system.board

        self.font_size = self.control_system.font_size

        self.control_system.register_observer(self.update_board)

        # self.control_system.register_observer(self.update_board)

        # For tracking selected piece and legal moves.
        self.selected_piece = self.control_system.selected_piece
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
        Clock.schedule_once(lambda dt: self.update_board(), 0.1)

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
                    # if (file + rank) % 2 == 0:
                    #     col = (189/255, 100/255, 6/255, 1) if self.bottom_colour_white else (247/255, 182/255, 114/255, 1)
                    # else:
                    #     col = (247/255, 182/255, 114/255, 1) if self.bottom_colour_white else (189/255, 100/255, 6/255, 1)
                    # Color(*col)

                    if (file + rank) % 2 == 0:
                        col = (189/255, 100/255, 6/255, 1) if self.bottom_colour_white else (247/255, 182/255, 114/255, 1)
                    else:
                        col = (247/255, 182/255, 114/255, 1) if self.bottom_colour_white else (189/255, 100/255, 6/255, 1)
                    Color(*col)

                    # Adjust rank for perspective.
                    if self.bottom_colour_white:
                        pos_y = board_origin[1] + rank * cell_size
                        #pos_x = board_origin[0] + file * cell_size
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
                label_text = str(i + 1)
            else:
                label_text = str(8-i)
            label = Label(text=label_text, halign="center", valign="middle", font_size = self.font_size)
            # label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
            # if self.bottom_colour_white:
            pos_y = board_origin[1] + i * cell_size
            # else:
            #     pos_y = board_origin[1] + (7 - i) * cell_size
            label.pos = (self.x, pos_y)
            label.size = (cell_size, cell_size)
            self.add_widget(label)
            self.row_labels.append(label)

        # Add column labels in the bottom margin.
        for i in range(8):
            if self.bottom_colour_white:

                label_text = chr(ord('a') + i)
            else:
                label_text = chr(ord('h') - i)
            label = Label(text=label_text, halign="center", valign="middle", font_size = self.font_size)
            # label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
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
                    pos_x = board_origin[0] + file * cell_size
                else:
                    pos_y = board_origin[1] + (7 - rank) * cell_size
                    pos_x = board_origin[0] + (7 - file) * cell_size
                    #pos_y = board_origin[1] + (7 - rank) * cell_size
                #pos_x = board_origin[0] + file * cell_size
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
                # pos_y = board_origin[1] + rank * cell_size
                pos_y = board_origin[1] + rank * cell_size
                pos_x = board_origin[0] + file * cell_size
            else:
                # pos_y = board_origin[1] + (7 - rank) * cell_size
                pos_y = board_origin[1] + (7 - rank) * cell_size
                pos_x = board_origin[0] + (7 - file) * cell_size
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

        if self.control_system.move_history:
            last_move_str = self.control_system.move_history[-1]  # e.g., "e2e4"
            # Extract the two squares from the move string.
            squares = [last_move_str[:2], last_move_str[2:4]]
            for square in squares:
                index = self.notation_to_index(square)
                file = index % 8
                rank = index // 8
                if self.bottom_colour_white:
                    pos_y = board_origin[1] + rank * cell_size
                    pos_x = board_origin[0] + file * cell_size
                else:
                    pos_y = board_origin[1] + (7 - rank) * cell_size
                    pos_x = board_origin[0] + (7 - file) * cell_size
                    #pos_y = board_origin[1] + (7 - rank) * cell_size
                #pos_x = board_origin[0] + file * cell_size
                # Use blue for last move highlighting.
                col = (191/255, 128/255, 1, 0.5) 
                col_inst = Color(*col)
                rect_inst = Rectangle(pos=(pos_x, pos_y), size=(cell_size, cell_size))
                self.canvas.before.add(col_inst)
                self.canvas.before.add(rect_inst)
                self.last_move_rects.append((col_inst, rect_inst))

    # def clear_highlights(self):
    #     # Remove previously added highlight instructions.
    #     for (col_inst, rect_inst) in self.highlight_rects:
    #         if col_inst in self.canvas.after.children:
    #             self.canvas.before.remove(col_inst)
    #         if rect_inst in self.canvas.after.children:
    #             self.canvas.before.remove(rect_inst)
    #     self.highlight_rects = []

    # def clear_last_move_highlights(self):
    #     for (col_inst, rect_inst) in self.last_move_rects:
    #         if col_inst in self.canvas.after.children:
    #             self.canvas.before.remove(col_inst)
    #         if rect_inst in self.canvas.after.children:
    #             self.canvas.before.remove(rect_inst)
    #     self.last_move_rects = []

    def clear_highlights(self):
        # Remove previously added highlight instructions from canvas.before.
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
        """
        Converts a square in chess notation (e.g. 'e2') into a 0-based board index.
        Assumes 'a1' corresponds to index 0, 'h8' to 63.
        """
        file = ord(square_str[0]) - ord('a')
        rank = int(square_str[1]) - 1
        return file + rank * 8
    
    def highlight_legal_moves_from_notation(self, square_str):
        """
        Highlights legal moves for a given selected square specified in algebraic notation (e.g., 'a2').

        This function:
        1. Converts the provided notation (like 'a2') to a board index.
        2. Retrieves the legal moves for that square from the control system.
        3. Updates the widget's internal list of legal moves.
        4. Calls the canvas update method to redraw the highlights.
        """

        print(f"trying to hightlight {square_str}")
        if square_str is not None:
            self.legal_moves = self.control_system.select_piece(self.notation_to_index(square_str))

            # Convert algebraic notation (e.g., 'a2') to a board index.
            # square_index = self.notation_to_index(square_str)
            
            # Retrieve legal moves from the control system using this index.
            # self.legal_moves = self.control_system.select_piece(square_str)
            
            # Optionally set the selected piece in the control system.
            # self.control_system.selected_piece = square_str

            # Refresh the canvas to update the highlights.
            self._update_canvas()
        else:
            self.legal_moves = []
            self._update_canvas()

        


    def update_board(self, *args):
        self.highlight_legal_moves_from_notation(self.control_system.selected_piece)

        # Remove old chess pieces.
        pieces_to_remove = [child for child in self.children if isinstance(child, ChessPiece)]
        for piece in pieces_to_remove:
            self.remove_widget(piece)
        # Add new chess pieces based on external game logic.
        for sq in self.control_system.SQUARES:
            piece = self.board.piece_at(sq)
            if piece is not None:
                symbol = piece.symbol()
                if symbol in self.control_system.piece_images:
                    source = self.control_system.piece_images[symbol]
                    piece_widget = ChessPiece(chess_square=sq,
                                              piece_symbol=symbol,
                                              control_system=self.control_system,
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
                    self.handle_touch_move(move)
                    #self.control_system.push_move(chess.Move.from_uci(move))
                    self.selected_piece = None
                    self.legal_moves = []
                    self.clear_highlights()
                    self.update_board()
                    return True
        
        # Otherwise, select a piece if one exists at this square.
        piece_widget = None
        for child in self.children:
            if isinstance(child, ChessPiece) and (child.chess_square == sq):
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
                # You might call control_system.select_piece to update legal moves.
                self.legal_moves = self.control_system.select_piece(piece_widget.chess_square)
                self.clear_highlights()

                # if self.control_system.legal_moves is not None:
                self.highlight_legal_moves(self.legal_moves)
                    
            return True

        return super(ChessBoard, self).on_touch_down(touch)

    def highlight_legal_moves(self, legal_moves):

        # Set our legal moves and trigger a canvas update to draw highlights.
        self.legal_moves = legal_moves
        self._update_canvas()

    def handle_touch_move(self, move_uci):
        self.control_system.handle_ui_move(move_uci)  # triggers state transition


# class MovesHistory(ScrollView):
#     """
#     A scrollable view that displays past moves.
#     """
#     def __init__(self, control_system, **kwargs):
#         super().__init__(**kwargs)
#         self.control_system = control_system
#         self.font_size = control_system.font_size
#         # Here we register an observer if needed.
#         self.control_system.register_observer(self.update_moves)

#         self.layout = BoxLayout(orientation='vertical')
#         self.layout.bind(minimum_height=self.layout.setter('height'))
#         self.add_widget(self.layout)

#     def update_moves(self, *args):
#         self.layout.clear_widgets()
#         # Assume control_system.move_history is a list of UCI move strings.
#         for move in self.control_system.move_history:
#             move_label = Label(text=move, font_size = self.font_size, size_hint_y=None, height=30)
#             self.layout.add_widget(move_label)
#         self.scroll_y = 0

class MovesHistory(ScrollView):
    """
    A scrollable view that displays past moves with spacing between elements.
    """
    def __init__(self, control_system, **kwargs):
        super().__init__(**kwargs)
        self.control_system = control_system
        self.font_size = control_system.font_size
        
        # Ensure vertical scrolling is enabled and allow dragging on content.
        self.do_scroll_y = True
        self.scroll_type = ['bars', 'content']  # Allows dragging on the content
        
        # Register the observer for updating moves.
        self.control_system.register_observer(self.update_moves)
        
        # Create a BoxLayout with added spacing between elements and optional padding.
        self.layout = BoxLayout(orientation='vertical', spacing=10, padding=[0, 10, 0, 10])
        self.layout.bind(minimum_height=self.layout.setter('height'))
        self.add_widget(self.layout)

    def update_moves(self, *args):
        self.layout.clear_widgets()
        # Assume control_system.move_history is a list of UCI move strings.
        for move in self.control_system.move_history:
            move_label = Label(text=move, font_size=self.font_size,
                               size_hint_y=None, height=30)
            self.layout.add_widget(move_label)
        # Scroll to the top.
        self.scroll_y = 1

class CapturedPieces(Widget):
    def __init__(self, control_system=None, rows=2, **kwargs):
        super(CapturedPieces, self).__init__(**kwargs)
        self.rows = rows  # Number of rows in each side's grid
        self.control_system = control_system
        self.control_system.register_observer(self.update_captured)
        # This will hold the list of captured piece symbols.
        self.captured_list = []
        # Redraw the background whenever position or size changes.
        self.bind(pos=self.draw_board, size=self.draw_board)

    def draw_board(self, *args):
        """
        Draw a background for the captured pieces widget.
        The left half is for white captures, the right half for black captures.
        """
        self.canvas.before.clear()
        with self.canvas.before:
            # White capture area (left half) background:
            Color(0.9, 0.9, 0.9, 1)  # light grey
            Rectangle(pos=(self.x, self.y), size=(self.width/2, self.height))
            # Black capture area (right half) background:
            Color(0.7, 0.7, 0.7, 1)  # slightly darker grey
            Rectangle(pos=(self.x + self.width/2, self.y), size=(self.width/2, self.height))

    def update_captured(self, *args):
        """
        Update the widget with captured pieces.
        White pieces (uppercase symbols) are arranged on the left,
        while black pieces (lowercase symbols) are arranged on the right.
        Pieces are placed in columns:
          - For white: first piece at the bottom-left corner, next above it,
            then moving to the next column to the right.
          - For black: first piece at the bottom-right corner, next above it,
            then moving to the next column to the left.
        """
        self.captured_list = self.control_system.captured_pieces
        # Remove any previously added images.
        self.clear_widgets()

        # Separate the captured pieces by color:
        white_captures = [p for p in self.captured_list if p.isupper()]
        black_captures = [p for p in self.captured_list if p.islower()]

        # --- White Captures (Left Half) ---
        white_area_x = self.x
        white_area_y = self.y
        white_area_width = self.width / 2
        white_area_height = self.height
        # Determine the number of columns needed (each column fills vertically).
        white_cols = math.ceil(len(white_captures) / self.rows) if self.rows > 0 else 1
        # Compute cell size in the white area.
        white_cell_width = white_area_width / white_cols if white_cols > 0 else white_area_width
        white_cell_height = white_area_height / self.rows

        for i, piece in enumerate(white_captures):
            col = i // self.rows  # Column index (starting from 0)
            row = i % self.rows   # Row index (0 is bottom)
            # Place first capture in the far left (bottom-left corner).
            piece_x = white_area_x + col * white_cell_width
            piece_y = white_area_y + row * white_cell_height
            source = self.control_system.piece_images.get(piece, '')
            img = Image(source=source, allow_stretch=True, keep_ratio=True)
            img.size = (white_cell_width, white_cell_height)
            img.pos = (piece_x, piece_y)
            self.add_widget(img)

        # --- Black Captures (Right Half) ---
        black_area_x = self.x + self.width/2
        black_area_y = self.y
        black_area_width = self.width / 2
        black_area_height = self.height
        black_cols = math.ceil(len(black_captures) / self.rows) if self.rows > 0 else 1
        black_cell_width = black_area_width / black_cols if black_cols > 0 else black_area_width
        black_cell_height = black_area_height / self.rows

        for i, piece in enumerate(black_captures):
            col = i // self.rows  # Column index (starting from 0)
            row = i % self.rows   # Row index (0 is bottom)
            # For black captures, start at the far right: subtract columns from the right edge.
            piece_x = black_area_x + black_area_width - (col + 1) * black_cell_width
            piece_y = black_area_y + row * black_cell_height
            source = self.control_system.piece_images.get(piece, '')
            img = Image(source=source, allow_stretch=True, keep_ratio=True)
            img.size = (black_cell_width, black_cell_height)
            img.pos = (piece_x, piece_y)
            self.add_widget(img)

# class CapturedPieces(Widget):
#     def __init__(self, control_system = None, rows=2, cols=8, **kwargs):
#         super(CapturedPieces, self).__init__(**kwargs)
#         self.rows = rows
#         self.cols = cols
#         self.control_system = control_system
#         self.control_system.register_observer(self.update_captured)
#         # This will hold the list of captured piece symbols.
#         self.captured_list = []
#         # Redraw the board whenever position/size changes.
#         self.bind(pos=self.draw_board, size=self.draw_board)

#     def draw_board(self, *args):
#         # Draw a simple 2x8 chessboard pattern as background.
#         self.canvas.before.clear()
#         cell_width = self.width / self.cols
#         cell_height = cell_width * 2
#         self.offset_y = (self.height - (self.rows * cell_height)) / 2

#         #cell_height = self.height / self.rows
#         for r in range(self.rows):
#             for c in range(self.cols):
#                 # Alternate colors like a chessboard.
#                 color=(247/255, 182/255, 114/255, 1)
#                 with self.canvas.before:
#                     Color(*color)
#                     Rectangle(
#                         pos=(self.x + c * cell_width, self.y + self.offset_y + r * cell_height),
#                         size=(cell_width, cell_height)
#                     )

#     def update_captured(self, *args):
#         """
#         Update the board with captured pieces.
#         :param captured_list: A list of piece symbols (e.g., ['p', 'N', ...])
#         """
#         self.captured_list = self.control_system.captured_pieces
#         # Remove any previously added piece images.
#         self.clear_widgets()
#         cell_width = self.width / self.cols
#         cell_height = self.height / self.rows
#         for idx, piece in enumerate(self.captured_list):
#             row = idx // self.cols
#             col = idx % self.cols
#             source = self.control_system.piece_images.get(piece, '')
#             img = Image(source=source, allow_stretch=True, keep_ratio=True)
#             img.size = (cell_width, cell_height)
#             # Basic positioning: one image per cell.
#             # To place pieces between squares, adjust the computed pos below.
#             # img.pos = (self.x + col * cell_width, self.y + row * cell_height)
#             img.pos=(self.x + col * cell_width, self.y + self.offset_y + row * cell_height)
#             self.add_widget(img)


# class CapturedPiecesOld(GridLayout):
#     """
#     A horizontal box that displays icons (or labels) of captured pieces.
#     """
#     def __init__(self, control_system, **kwargs):
#         kwargs.setdefault('cols', 8)
#         super(CapturedPieces, self).__init__(**kwargs)
#         self.control_system = control_system
#         # self.control_system.register_observer(self.update_captured)
#         self.captured_list = self.control_system.captured_pieces

#         self.bg_color = (247/255, 182/255, 114/255, 1)

#         self.size_hint_y = None
#         self.bind(minimum_height=self.setter('height'))

    

#         with self.canvas.before:
#             Color(*self.bg_color)
#             self.rect = Rectangle(pos=self.pos, size=self.size)
#         self.bind(pos=self.update_rect, size=self.update_rect)

#     def update_rect(self, *args):
#         self.rect.pos = self.pos
#         self.rect.size = self.size


#     def update_captured(self, board, game_state, *args):\
    
#         Color(247/255, 182/255, 114/255, 1)
#         Rectangle()

#         self.clear_widgets()
#         captured_list = self.control_system.captured_pieces
#         for piece in captured_list:
#             piece_image = Image(source=f'{piece_images[piece]}', allow_stretch=True, keep_ratio=True, size_hint=(None, None))
#             self.add_widget(piece_image)
#             #piece_label = Label(text=piece, size_hint=(None, None), size=(40, 40))
#             #self.add_widget(piece_label)

class MaterialBar(BoxLayout):
    """
    A custom widget that displays a horizontal bar.
    The left portion (black) and right portion (white) reflect material percentages.
    """
    def __init__(self, control_system = None , **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = 0.1
        self.black_percentage = 50
        self.white_percentage = 50
        self.black_score = ""
        self.white_score = ""
        self.control_system = control_system
        self.font_size = self.control_system.font_size
        self.control_system.register_observer(self.update_percentages)

        self.bind(pos=self.update_canvas, size=self.update_canvas)

        self.black_label = Label(text=f"{self.black_score}", color=(1, 1, 1, 1), font_size=self.font_size)
        # White's percentage label appears above the bar on the far right;
        # text color is black.
        self.white_label = Label(text=f"{self.white_score}", color=(0, 0, 0, 1), font_size=self.font_size)
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
        self.white_value, self.black_value = self.calculate_material(self.control_system.board)

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

    def calculate_material(self, board):
        # Standard piece values: pawn=1, knight=3, bishop=3, rook=5, queen=9, king=0
        values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0
        }
        white_score = 0
        black_score = 0

        if board is None:
            board = self.board

        for square, piece in board.piece_map().items():
            if piece.color == chess.WHITE:
                white_score += values[piece.piece_type]
            else:
                black_score += values[piece.piece_type]

        print(f"White: {white_score}, Black: {black_score}")
        
        # A positive result indicates a material advantage for White,
        # while a negative result indicates an advantage for Black.
        return white_score, black_score


from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock

class PlayerClock(Widget):
    def __init__(self, side="white", control_system=None, **kwargs):
        """
        :param side: "white" or "black" indicating which clock this is.
        :param clock_instance: An instance of clock_logic that provides:
                              - white_time (for white) and black_time (for black)
                              - active_player (1 for white, 2 for black)
                              - update(dt): updates the active player's time.
                              - format_time(seconds): returns a string formatted as mm:ss.
                              - timer_enabled: if True, display the timer countdown.
        """
        super(PlayerClock, self).__init__(**kwargs)
        self.side = side.lower()
        self.control_system = control_system
        self.clock_logic = self.control_system.clock_logic
        self.timer_enabled = self.control_system.timer_enabled

        self.control_system.register_observer(self.update_clock)

        # Create a label for time display.
        self.label = Label(text=self.get_initial_text(), font_size="40sp",
                           halign="center", valign="middle")
        self.add_widget(self.label)

        # Create an Image widget for the arrow.
        # Use "left_arrow.png" for white clock, "right_arrow.png" for black clock.
        arrow_source = "assets/left_arrow.png" if self.side == "black" else "assets/right_arrow.png"
        self.arrow = Image(source=arrow_source, allow_stretch=True, keep_ratio=True, size_hint=(1,1))
        # Start with the arrow hidden.
        self.arrow.opacity = 0
        self.add_widget(self.arrow)

        # Bind layout updates.
        self.bind(pos=self.update_layout, size=self.update_layout)

        # Schedule periodic updates.
        Clock.schedule_interval(self.update_clock, 0.1)

    def get_initial_text(self):
        if self.timer_enabled and self.clock_logic:
            if self.side == "white":
                return self.clock_logic.format_time(self.clock_logic.white_time)
            else:
                return self.clock_logic.format_time(self.clock_logic.black_time)
        # When timer is disabled, show no text initially.
        return ""

    def update_layout(self, *args):
        # Make the label fill this widget.
        self.label.size = self.size
        self.label.pos = self.pos
        self.label.text_size = self.label.size
        
        # Position the arrow in the center of the widget.
        # Adjust the size (50x50 here) as needed.
        arrow_size = (50, 50)
        self.arrow.size = arrow_size
        self.arrow.pos = (self.center_x - arrow_size[0] / 2, self.center_y - arrow_size[1] / 2)
        
        self.update_background()

    def update_background(self):
        # Clear existing background instructions.
        self.label.canvas.before.clear()
        with self.label.canvas.before:
            if self.is_active():
                # Active clock: dark background with light text.
                Color(1, 1, 1, 1)
                self.label.color = (0, 0, 0, 1)
            else:
                # Inactive clock: light background with dark text.
                Color(0, 0, 0, 1)
                self.label.color = (1, 1, 1, 1)
            Rectangle(pos=self.label.pos, size=self.label.size)

    def is_active(self):
        """
        Returns True if this clock is the active clock.
        For clock_logic, active_player==1 means white is active,
        and active_player==2 means black is active.
        """
        if not self.clock_logic:
            return False
        if self.control_system.board.turn:
            return self.clock_logic.active_player == 1
        else:
            return self.clock_logic.active_player == 2

    def update_clock(self, dt):
        if not self.clock_logic:
            return

        # Update the clock logic regardless of display mode.
        self.clock_logic.update(dt)

        if self.timer_enabled:
            # When timer is enabled, display the formatted time and hide the arrow.
            self.arrow.opacity = 0
            if self.side == "white":
                time_remaining = self.clock_logic.white_time
            else:
                time_remaining = self.clock_logic.black_time
            self.label.text = self.clock_logic.format_time(time_remaining)
        else:
            # When timer is disabled, clear the label and show the arrow if this clock is active.
            self.label.text = ""
            self.arrow.opacity = 1 if self.is_active() else 0

        # Refresh the background to reflect active state.
        self.update_background()


class MatrixWidget(GridLayout):
    def __init__(self, control_system, **kwargs):
        super().__init__(**kwargs)

        self.matrix = control_system.hall.sense_layer.get_squares()
        self.cols = len(self.matrix[0])
        self.rows = len(self.matrix)
        self.spacing = 2
        self.size_hint = (1, 1)

        self.control_system.register_observer(self.update_matrix)

    def update_matrix(self):
        for row in self.matrix:
            for cell in row:
                self.add_widget(CellWidget(cell))

class CellWidget(Widget):
    def __init__(self, value, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            if value == 1:
                Color(0, 1, 0)  # Green for 1
            else:
                Color(1, 0, 0)  # Red for 0
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size



class DemoToggleButton(ToggleButton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Remove the default background image.
        self.background_normal = ''
        # Start with white background.
        self.background_color = [1, 1, 1, 1]  # RGBA for white.
        self.color_value = 'white'
        self.bind(state=self.on_toggle)

    def on_toggle(self, instance, value):
        if value == 'down':
            # Button is toggled "on" — set background to black.
            self.background_color = [0, 0, 0, 1]  # RGBA for black.
            self.color_value = 'black'
        else:
            # Button is toggled "off" — set background to white.
            self.background_color = [1, 1, 1, 1]  # RGBA for white.
            self.color_value = 'white'
        
