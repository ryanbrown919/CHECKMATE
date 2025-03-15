from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Ellipse, Line
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.app import App
from kivy.core.window import Window
Window.fullscreen = True

from customWidgets import HorizontalLine, VerticalLine, IconButton, RoundedButton, headerLayout

# Constants in mm (used for documentation; drawing uses relative units)
SQUARE_SIZE_MM = 50    # each square is 50mm
STEP_MM = 25           # each step is 25mm

class GantryTargetWidget(Widget):
    """
    Draws an 8x10 grid:
      - The top 8 rows (of 10) form a chessboard (with alternating colors).
      - The bottom 2 rows are extra rows (shown here in a light gray background).
    A red dot is drawn on top of the grid.
    The dot moves in increments of 25mm (half the square size), so the underlying grid
    is considered to have 16 horizontal steps (8 squares * 2 steps per square) and
    20 vertical steps (10 rows * 2 steps per square).
    """
    def __init__(self, **kwargs):
        super(GantryTargetWidget, self).__init__(**kwargs)
        # Total squares: 8 columns x 10 rows.
        self.cols = 8
        self.rows = 10
        # These will be computed in update_canvas.
        self.square_size = None  # pixel size of a 50mm square (scaled)
        self.step_size = None    # half of square_size, corresponding to 25mm
        # Store the dot's position in "steps" (0 to 16 horizontally, 0 to 20 vertically)
        # Default: center of the chessboard area. (Chessboard occupies rows 2-9.)
        self.dot_step_x = 8
        self.dot_step_y = 11  
        self.bind(pos=self.update_canvas, size=self.update_canvas)
        Clock.schedule_once(lambda dt: self.update_canvas(), 0)
    
    def update_canvas(self, *args):
        # Clear the canvas.
        self.canvas.clear()
        
        # Compute cell (square) size so that the grid fits in the widget.
        # We want each square to be square so we use the minimum of available width and height.
        self.square_size = min(self.width / self.cols, self.height / self.rows)
        self.step_size = self.square_size / 2.0
        
        with self.canvas:
            # --- Draw the extra two rows (bottom rows 0 and 1) ---
            for row in range(2):
                for col in range(self.cols):
                    x = col * self.square_size
                    y = row * self.square_size
                    Color(247/255, 182/255, 114/255, 1)  # light gray background for extra rows
                    Rectangle(pos=(x, y), size=(self.square_size, self.square_size))
            
            # --- Draw the chessboard (top 8 rows, rows 2 to 9) ---
            for row in range(2, self.rows):
                for col in range(self.cols):
                    x = col * self.square_size
                    y = row * self.square_size
                    # Use alternating colors.
                    # (Here the alternating pattern is computed with (col+row) even/odd;
                    #  you can adjust if you need white on the bottom of the chessboard.)
                    if (col + row) % 2 == 0:
                        Color(189/255, 100/255, 6/255, 1)
                    else:
                        Color(247/255, 182/255, 114/255, 1)
                    Rectangle(pos=(x, y), size=(self.square_size, self.square_size))
            
            # --- Draw grid lines (optional) ---
            Color(0, 0, 0, 1)
            # Vertical lines:
            for col in range(self.cols + 1):
                x = col * self.square_size
                Line(points=[x, 0, x, self.rows * self.square_size], width=1)
            # Horizontal lines:
            for row in range(self.rows + 1):
                y = row * self.square_size
                Line(points=[0, y, self.cols * self.square_size, y], width=1)
            
            # --- Draw the red dot ---
            # The dot's center in pixels is computed from its step coordinates.
            dot_center_x = self.dot_step_x * self.step_size
            dot_center_y = self.dot_step_y * self.step_size
            dot_radius = self.step_size * 0.4  # adjust for desired dot size
            Color(1, 0, 0, 1)  # red
            Ellipse(pos=(dot_center_x - dot_radius, dot_center_y - dot_radius),
                    size=(dot_radius * 2, dot_radius * 2))
    
    def move_dot(self, dx, dy):
        """
        Moves the red dot by one step (25mm) in the x and/or y direction.
        Ensures the dot remains within the grid boundaries.
        """
        new_x = self.dot_step_x + dx
        new_y = self.dot_step_y + dy
        # Horizontal boundary: 0 to (cols * 2). (e.g., 0 to 16)
        if new_x < 0:
            new_x = 0
        elif new_x > self.cols * 2:
            new_x = self.cols * 2
        # Vertical boundary: 0 to (rows * 2). (e.g., 0 to 20)
        if new_y < 0:
            new_y = 0
        elif new_y > self.rows * 2:
            new_y = self.rows * 2
        self.dot_step_x = new_x
        self.dot_step_y = new_y
        self.update_canvas()
    
    def get_current_mm(self):
        """
        Returns the current gantry target coordinates in millimeters.
        (Each step is 25mm.)
        """
        return (self.dot_step_x * STEP_MM, self.dot_step_y * STEP_MM)

class GantryControlWidget(BoxLayout):
    """
    A composite widget that displays the gantry target board (grid) and arrow buttons.
    The arrow buttons move the red dot by 25mm per press.
    """
    def __init__(self, **kwargs):
        super(GantryControlWidget, self).__init__(**kwargs)
        self.orientation = 'vertical'
        # The target board occupies most of the space.

        self.header_layout = headerLayout(menu=False)
        self.body_layout = BoxLayout(orientation='horizontal', spacing=10, padding = 20)
        self.board_display = BoxLayout(orientation='vertical', spacing=10, padding = 20)
        self.gantry_controls = BoxLayout(orientation='vertical', spacing=10, padding = 20)

        self.target_board = GantryTargetWidget()
        self.board_display.add_widget(self.target_board)


        #self.target_board = GantryTargetWidget(size_hint=(1, 0.8))
        self.add_widget(self.header_layout)
        self.add_widget(HorizontalLine())
        self.add_widget(self.body_layout)
        self.body_layout.add_widget(self.board_display)
        self.body_layout.add_widget(self.gantry_controls)
        
        # Create arrow buttons.
        btn_layout = GridLayout(size_hint=(1, 1), cols=3, rows=3)
        # We arrange buttons in a simple vertical layout with a nested grid.
        arrow_layout = BoxLayout(orientation='vertical')


        
        nw = IconButton(source="figures/nw.png", size_hint=(0.1, 0.1))
        n  = IconButton(source="figures/n.png",  size_hint=(0.1, 0.1))
        ne = IconButton(source="figures/ne.png", size_hint=(0.1, 0.1))
        w  = IconButton(source="figures/w.png",  size_hint=(0.1, 0.1))
        c  = Button(text="Center", size_hint=(0.1, 0.1))
        e  = IconButton(source="figures/e.png",  size_hint=(0.1, 0.1))
        sw = IconButton(source="figures/sw.png", size_hint=(0.1, 0.1))
        s  = IconButton(source="figures/s.png",  size_hint=(0.1, 0.1))
        se = IconButton(source="figures/se.png", size_hint=(0.1, 0.1))


        btn_layout.add_widget(nw)
        btn_layout.add_widget(n)
        btn_layout.add_widget(ne)
        btn_layout.add_widget(w)
        btn_layout.add_widget(c)
        btn_layout.add_widget(e)
        btn_layout.add_widget(sw)
        btn_layout.add_widget(s)
        btn_layout.add_widget(se)

        self.gantry_controls.add_widget(btn_layout)


                #         ↖ ↑ ↗
                # ← · →
                # ↙ ↓ ↘
        
        # middle_row = BoxLayout()
        # btn_left = Button(text="Left")
        # btn_right = Button(text="Right")
        # middle_row.add_widget(btn_left)
        # middle_row.add_widget(Label())
        # middle_row.add_widget(btn_right)
        
        # bottom_row = BoxLayout()
        # btn_down = Button(text="Down")
        # bottom_row.add_widget(Label())
        # bottom_row.add_widget(btn_down)
        # bottom_row.add_widget(Label())
        
        # arrow_layout.add_widget(top_row)
        # arrow_layout.add_widget(middle_row)
        # arrow_layout.add_widget(bottom_row)
        # btn_layout.add_widget(arrow_layout)
        # self.add_widget(btn_layout)
        
        # Bind the arrow buttons to move the dot.
        nw.bind(on_release=lambda inst: self.target_board.move_dot(-1, 1))
        n.bind(on_release=lambda inst: self.target_board.move_dot(0, 1))
        ne.bind(on_release=lambda inst: self.target_board.move_dot(1, 1))
        w.bind(on_release=lambda inst: self.target_board.move_dot(-1, 0))
        c.bind(on_release=lambda inst: self.target_board.move_dot(0, 0))
        e.bind(on_release=lambda inst: self.target_board.move_dot(1, 0))
        sw.bind(on_release=lambda inst: self.target_board.move_dot(-1, -1))
        s.bind(on_release=lambda inst: self.target_board.move_dot(0, -1))
        se.bind(on_release=lambda inst: self.target_board.move_dot(1, -1))
        
        # Optionally, you can add a label to display the current coordinate in mm.
        self.coord_label = Label(text="Target: -- mm", size_hint=(1, 0.1))
        self.gantry_controls.add_widget(self.coord_label)
        # Update the label periodically.
        Clock.schedule_interval(self.update_label, 0.2)
    
    def update_label(self, dt):
        mm_coord = self.target_board.get_current_mm()
        self.coord_label.text = f"Target: {mm_coord[0]} mm, {mm_coord[1]} mm"

# --- For testing the widget in an app ---
class TestApp(App):
    def build(self):
        return GantryControlWidget()

if __name__ == '__main__':
    TestApp().run()
