from kivy.config import Config
Config.set('graphics', 'fullscreen', 'auto')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.button import Button 
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle, Ellipse, Line
from kivy.clock import Clock

#------------------------------------------------
# ChessSquare: a square drawn with a unique ID.
# The physical mapping is such that the square
# with ID "h1" (file h, rank 1) will be in the
# bottom‐left of the board.
#------------------------------------------------
class ChessSquare(Widget):
    def __init__(self, square_id, **kwargs):
        super(ChessSquare, self).__init__(**kwargs)
        self.square_id = square_id
        # Our board’s ordering: bottom row is rank 1.
        # In each row, we add squares from file h to a.
        # Compute physical indices:
        #   x_full = rank - 1
        #   y_full = ord('h') - ord(file)
        file = square_id[0]  # e.g. "h"
        rank = int(square_id[1])
        x_index = rank - 1
        y_index = ord('h') - ord(file)
        # Alternate color pattern.
        if (x_index + y_index) % 2 == 0:
            self.bg_color = [189/255., 100/255., 6/255., 1]   # dark brown
        else:
            self.bg_color = [247/255., 182/255., 114/255., 1]  # light brown
        with self.canvas:
            Color(*self.bg_color)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)
    
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

#------------------------------------------------
# RedDot: the dot that will be moved around.
# Its position is controlled in "half‑steps" so that
# it can be placed on square centers, edges, or corners.
#------------------------------------------------
class RedDot(Widget):
    def __init__(self, **kwargs):
        super(RedDot, self).__init__(**kwargs)
        with self.canvas:
            Color(1, 0, 0, 1)
            self.dot = Ellipse(pos=self.pos, size=self.size)
        self.bind(pos=self.update_dot, size=self.update_dot)
    
    def update_dot(self, *args):
        self.dot.pos = self.pos
        self.dot.size = self.size

#------------------------------------------------
# TrailWidget: draws a continuous line connecting
# all red dot centers that have been recorded.
#------------------------------------------------
class TrailWidget(Widget):
    def update_trail_with_points(self, points):
        self.canvas.clear()
        if len(points) >= 2:
            flat_points = [coord for p in points for coord in p]
            with self.canvas:
                Color(1, 0, 0, 1)
                Line(points=flat_points, width=2)
    def clear_trail(self):
        self.canvas.clear()

#------------------------------------------------
# ChessBoardWidget: builds an 8×8 board inside a FloatLayout.
# The board is constructed using a vertical BoxLayout
# (each row is a horizontal BoxLayout). The rows are added
# in ascending order (rank 1 at the bottom, rank 8 at the top),
# and within each row squares are added from file h to a.
# The board's area is used to compute absolute positions.
#------------------------------------------------
class ChessBoardWidget(FloatLayout):
    def __init__(self, **kwargs):
        super(ChessBoardWidget, self).__init__(**kwargs)
        self.squares = {}  # Maps square ID (e.g. "e2") to widget.
        # Build the board layout.
        self.board_layout = BoxLayout(orientation='vertical', spacing=0)
        self.rows = []
        # For ranks 1 to 8 (bottom to top).
        for rank in range(1, 9):
            row = BoxLayout(orientation='horizontal', spacing=0)
            # For each rank, add squares in order: files h, g, f, e, d, c, b, a.
            for file in ["h", "g", "f", "e", "d", "c", "b", "a"]:
                square_id = file + str(rank)
                sq = ChessSquare(square_id)
                row.add_widget(sq)
                self.squares[square_id] = sq
            self.rows.append(row)
        # Add rows in the same order (first added at bottom).
        for row in self.rows:
            self.board_layout.add_widget(row)
        self.add_widget(self.board_layout)
        
        # Add a TrailWidget to draw the continuous line.
        self.trail_widget = TrailWidget()
        self.add_widget(self.trail_widget)
        
        # Add the red dot.
        self.red_dot = RedDot(size_hint=(None, None))
        self.red_dot.size = (30, 30)  # This size will be updated in on_size.
        self.add_widget(self.red_dot)
        
        # Dot position in half-steps (from 0 to 16 in both directions).
        # The board's bottom-left (physical h1) corresponds to (0,0).
        # For square centers, use: center of square = (2*x_full + 1, 2*y_full + 1),
        # where x_full = rank - 1 and y_full = ord('h') - ord(file).
        # Initialize dot at square e2:
        #   For e2: rank = 2 -> x_full = 1 → center_x = 2*1+1 = 3.
        #           file = e → y_full = ord('h')-ord('e') = 104-101 = 3 → center_y = 2*3+1 = 7.
        self.dot_x = 3
        self.dot_y = 7
        
        self.trail_enabled = False
        self.trail_points = []  # Absolute positions (in pixels).
        Clock.schedule_once(lambda dt: self.update_dot_position(), 0)
    
    def on_size(self, *args):
        # Make the board_layout fill the widget.
        self.board_layout.size = self.size
        self.board_layout.pos = self.pos
        # Ensure each row is 1/8th of the height.
        for row in self.rows:
            row.size_hint_y = 1/8.0
        # Trail widget covers the board.
        self.trail_widget.size = self.size
        self.trail_widget.pos = self.pos
        self.update_dot_position()
    
    def update_dot_position(self):
        # Calculate square size (S = board_layout.width / 8).
        S = self.board_layout.width / 8.0
        half_step = S / 2.0  # Each half-step is S/2.
        # The board_layout’s bottom-left corner is the position of square h1.
        base_x, base_y = self.board_layout.pos
        # Compute absolute position in pixels.
        abs_x = base_x + self.dot_x * half_step
        abs_y = base_y + self.dot_y * half_step
        # Update the red dot so that its center is at (abs_x, abs_y).
        self.red_dot.pos = (abs_x - self.red_dot.width/2, abs_y - self.red_dot.height/2)
        # If trail capture is active, record the point.
        if self.trail_enabled:
            self.trail_points.append((abs_x, abs_y))
            self.trail_widget.update_trail_with_points(self.trail_points)
    
    def move_dot_to_square(self, square_id):
        # Move the dot to the center of the specified square.
        if square_id not in self.squares:
            print("Invalid square id:", square_id)
            return
        file = square_id[0]
        rank = int(square_id[1])
        self.dot_x = (rank - 1) * 2 + 1
        self.dot_y = (ord('h') - ord(file)) * 2 + 1
        self.update_dot_position()
    
    def arrow_move(self, dx, dy):
        # Move the dot by (dx, dy) half-steps, clamped to [0, 16].
        self.dot_x = max(0, min(16, self.dot_x + dx))
        self.dot_y = max(0, min(16, self.dot_y + dy))
        self.update_dot_position()
    
    def clear_trail(self):
        self.trail_points = []
        self.trail_widget.clear_trail()

#------------------------------------------------
# ArrowControlWidget: a 3×3 grid of arrow buttons.
# Each button moves the dot by 1 half-step in the given direction.
#------------------------------------------------
class ArrowControlWidget(GridLayout):
    def __init__(self, move_callback, **kwargs):
        super(ArrowControlWidget, self).__init__(**kwargs)
        self.cols = 3
        self.rows = 3
        self.spacing = 5
        self.move_callback = move_callback
        # Mapping: each button’s text and (dx, dy) in half-steps.
        mapping = [
            [("↖",  1,  1), ("↑",  1,  0), ("↗",  1, -1)],
            [("←",  0,  1), ("",   0,  0), ("→",  0, -1)],
            [("↙", -1,  1), ("↓", -1,  0), ("↘", -1, -1)]
        ]
        for row in mapping:
            for text, dx, dy in row:
                btn = Button(text=text, font_size=32)
                if text == "":
                    btn.disabled = True
                else:
                    btn.bind(on_release=lambda inst, dx=dx, dy=dy: self.move_callback(dx, dy))
                self.add_widget(btn)

#------------------------------------------------
# MainWidget: the parent container.
# Uses a vertical BoxLayout so that the chessboard is
# at the top and the control panel sits below it.
#------------------------------------------------
class MainWidget(BoxLayout):
    def __init__(self, **kwargs):
        super(MainWidget, self).__init__(**kwargs)
        self.orientation = 'vertical'
        # The chessboard takes ~70% of the vertical space.
        self.chessboard = ChessBoardWidget(size_hint=(1, 0.7))
        self.add_widget(self.chessboard)
        
        # Control panel takes ~30% of the vertical space.
        control_panel = BoxLayout(orientation='vertical', size_hint=(1, 0.3), padding=10, spacing=10)
        
        # TextInput for standard move entry (e.g. "e2e4").
        self.move_input = TextInput(size_hint=(1, 0.3), multiline=False, hint_text="Enter move (e.g. e2e4)")
        self.move_input.bind(on_text_validate=self.on_move_entered)
        control_panel.add_widget(self.move_input)
        
        # 3×3 Arrow grid for relative movement.
        arrow_grid = ArrowControlWidget(self.arrow_move_callback, size_hint=(1, 0.4))
        control_panel.add_widget(arrow_grid)
        
        # Button panel for trail control.
        button_panel = BoxLayout(orientation='horizontal', size_hint=(1, 0.3), spacing=10)
        btn_start = Button(text="Start")
        btn_stop = Button(text="Stop")
        btn_clear = Button(text="Clear")
        btn_start.bind(on_release=self.start_trail)
        btn_stop.bind(on_release=self.stop_trail)
        btn_clear.bind(on_release=self.clear_trail)
        button_panel.add_widget(btn_start)
        button_panel.add_widget(btn_stop)
        button_panel.add_widget(btn_clear)
        control_panel.add_widget(button_panel)
        
        self.add_widget(control_panel)
    
    def on_move_entered(self, instance):
        move = instance.text.strip().lower()
        if len(move) >= 4:
            from_sq = move[:2]
            to_sq = move[2:4]
            self.chessboard.move_dot_to_square(from_sq)
            Clock.schedule_once(lambda dt: self.chessboard.move_dot_to_square(to_sq), 0.5)
        instance.text = ""
    
    def arrow_move_callback(self, dx, dy):
        self.chessboard.arrow_move(dx, dy)
    
    def start_trail(self, instance):
        self.chessboard.trail_enabled = True
    
    def stop_trail(self, instance):
        self.chessboard.trail_enabled = False
    
    def clear_trail(self, instance):
        self.chessboard.clear_trail()

#------------------------------------------------
# Run the app.
#------------------------------------------------
class ChessApp(App):
    def build(self):
        return MainWidget()

if __name__ == '__main__':
    ChessApp().run()
