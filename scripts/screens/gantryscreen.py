'''
Contains wwidget to conenct and control gantry, as well as interface for manual gantry control and debug log

'''


import glob
import serial
import time
import threading
import sys

from kivy.uix.screenmanager import Screen

from kivy.uix.label import Label
from kivy.core.text import Label as CoreLabel

from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Ellipse, Line
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput   
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.app import App
from kivy.core.window import Window
Window.fullscreen = True

try:
    from scripts.screens.custom_widgets import HorizontalLine, VerticalLine, IconButton, headerLayout, ChessBoard, MaterialBar, MovesHistory, CapturedPieces, PlayerClock

except:
    from custom_widgets import HorizontalLine, VerticalLine, IconButton, RoundedButton, headerLayout, MaterialBar, CapturedPieces, MovesHistory


'''
Gantry parameters from testing mar 25

Max Y value: 430, 435 barely touching end ??
440 (445 reachable)
Home then move -y 11mm



'''


SQUARE_SIZE_MM = 50    # each square is 50mm
STEP_MM = 25  # each step is 25mm

# Constant feedrate as in your original code
FEEDRATE = 15000  # mm/min


class GantryTargetWidget(Widget):

    
    """
    Draws an 8x10 grid:
      - The inner 8x8 area (rows 2 to 9, columns 0 to 7) is the chessboard.
      - The extra rows/columns serve as margins.
    A red dot is drawn on top whose position is maintained in half‑steps.
    The grid scales relative to the parent widget and is offset from the bottom‑left.
    When trail mode is active, each new dot center is appended to a continuous red line.
    
    The coordinate system is rotated 90° clockwise relative to standard chess so that:
      - Traditional h1 appears at the top right,
      - h8 appears at the top left,
      - a8 appears at the bottom left,
      - a1 appears at the bottom right.
    Border labels are drawn in the outermost margin cells.
    """
    def __init__(self, control_system, **kwargs):
        super(GantryTargetWidget, self).__init__(**kwargs)
        self.control_system = control_system
        self.capture_move = self.control_system.capture_move
        self.hall = self.control_system.hall
        self.gantry = self.control_system.gantry
        self.cols = 8
        self.rows = 10
        self.square_size = None  # computed in update_canvas
        self.step_size = None    # half of square_size
        # Dot's position in half‑steps (range: 0 to 16 horizontally, 0 to 20 vertically)
        self.dot_step_x = 8
        self.dot_step_y = 11  
        # Offset (in pixels) from the widget's bottom‑left where the grid starts.
        self.offset_value = 50  
        # Trail points: list of (x,y) pixel positions.
        self.trail_points = []
        self.trail_enabled = False

        self.path = []
        # Lists for border labels.
        self.top_labels = []
        self.bottom_labels = []
        self.left_labels = []
        self.right_labels = []
        self.bind(pos=self.update_canvas, size=self.update_canvas)
        Clock.schedule_interval(lambda dt: self.update_canvas(), 0.5)
        Clock.schedule_once(lambda dt: self.add_labels(), 0.1)
    
    def update_canvas(self, *args):
        self.canvas.clear()
        self.board_occupancy = self.hall.sense_layer.get_squares_gantry()
        # transposed_board = list(map(list, zip(*self.board_occupancy)))
        # rotated_board = [list(row) for row in list(zip(*transposed_board))[::-1]]


        # Compute square size relative to parent's available size minus the offset.
        self.square_size = min((self.width - self.offset_value) / self.cols,
                               (self.height - self.offset_value) / self.rows)
        self.step_size = self.square_size / 2.0
        # The full grid origin (bottom‑left of drawn grid)
        grid_origin = (self.x + self.offset_value, self.y + self.offset_value)
        with self.canvas:
            # --- Draw extra two rows (rows 0 and 1) at the bottom ---
            for row in range(2):
                for col in range(self.cols):
                    x = grid_origin[0] + col * self.square_size
                    y = grid_origin[1] + row * self.square_size
                    Color(247/255.0, 182/255.0, 114/255.0, 1)
                    Rectangle(pos=(x, y), size=(self.square_size, self.square_size))
            # --- Draw chessboard (rows 2 to 9) ---
            for row in range(2, self.rows):
                for col in range(self.cols):
                    x = grid_origin[0] + col * self.square_size
                    y = grid_origin[1] + row * self.square_size
                    if (col + row) % 2 == 0:
                        #Color(189/255.0, 100/255.0, 6/255.0, 1)
                        Color(247/255.0, 182/255.0, 114/255.0, 1)
                    else:
                        #Color(247/255.0, 182/255.0, 114/255.0, 1)
                        Color(189/255.0, 100/255.0, 6/255.0, 1)
                    Rectangle(pos=(x, y), size=(self.square_size, self.square_size))
                    # Draw a circle in the top left of the square.
                    circle_radius = self.square_size * 0.1
                    circle_x = x + self.square_size * 0.1 - circle_radius
                    circle_y = y + self.square_size * 0.9 - circle_radius

                    # Calculate the chess notation for the square.
                    # In the rotated system:
                    # - Files (columns) are labeled from 'a' to 'h' (left to right).
                    # - Ranks (rows) are labeled from 8 to 1 (top to bottom).
                    # file_label = chr(ord('a') + (row - 2))
                    # rank_label = str((8 - col))
                    # square_label = f"{file_label}{rank_label}"
                    # Calculate the diagonal mirror square.
                    # In the rotated system:
                    # - Files (columns) are labeled from 'a' to 'h' (left to right).
                    # - Ranks (rows) are labeled from 8 to 1 (top to bottom).
                    
                    square_occupancy = self.board_occupancy[7-col][row-2]

                    # print(f"Square {square_label} is {square_occupancy}")

                    if square_occupancy:
                        Color(0, 1, 0, 1)  # Blue color for the circle.
                    else:
                        Color(0, 1, 0, 0)  # No visibility if not detected for the circle.
                    Ellipse(pos=(circle_x, circle_y), size=(circle_radius * 2, circle_radius * 2))

                    Color(1, 1, 1, 1)
                    #square_label = f"{chr(ord('a') + (7 - col))}{row - 1}"
                    square_label = f"{chr(ord('h') - (7 - (row-2)))}{8-col}"
                    # Create a CoreLabel to render the text.
                    core_lbl = CoreLabel(text=square_label, font_size=self.square_size * 0.2, color=(0, 0, 0, 0.8))
                    core_lbl.refresh()
                    texture = core_lbl.texture
                    # Position the label in the bottom right of the square.
                    label_x = x + self.square_size * 0.7
                    label_y = y + self.square_size * 0.05
                    # Draw the label texture.
                    Rectangle(texture=texture, pos=(label_x, label_y), size=texture.size)
            # --- Draw grid lines ---
            Color(0, 0, 0, 1)
            for col in range(self.cols + 1):
                x = grid_origin[0] + col * self.square_size
                Line(points=[x, grid_origin[1], x, grid_origin[1] + self.rows * self.square_size], width=1)
            for row in range(self.rows + 1):
                y = grid_origin[1] + row * self.square_size
                Line(points=[grid_origin[0], y, grid_origin[0] + self.cols * self.square_size, y], width=1)
            # --- Draw the trail (continuous red line) ---
            if len(self.trail_points) >= 2:
                Color(1, 0, 0, 1)
                flat_points = [coord for pt in self.trail_points for coord in pt]
                Line(points=flat_points, width=2)
            # --- Draw the red dot ---
            dot_center_x = grid_origin[0] + self.dot_step_x * self.step_size
            dot_center_y = grid_origin[1] + self.dot_step_y * self.step_size
            dot_radius = self.step_size * 0.4
            Color(1, 0, 0, 1)
            Ellipse(pos=(dot_center_x - dot_radius, dot_center_y - dot_radius),
                    size=(dot_radius * 2, dot_radius * 2))
        self.update_labels()
    
    def add_labels(self):
        # Create 8 labels for each border if not already created.
        if len(self.top_labels) < 8:
            for i in range(8):
                lbl = Label(text="", halign="center", valign="middle", color=(0,0,0,1))
                self.top_labels.append(lbl)
                self.add_widget(lbl)
            for i in range(8):
                lbl = Label(text="", halign="center", valign="middle", color=(0,0,0,1))
                self.bottom_labels.append(lbl)
                self.add_widget(lbl)
            for j in range(8):
                lbl = Label(text="", halign="center", valign="middle", color=(0,0,0,1))
                self.left_labels.append(lbl)
                self.add_widget(lbl)
            for j in range(8):
                lbl = Label(text="", halign="center", valign="middle", color=(0,0,0,1))
                self.right_labels.append(lbl)
                self.add_widget(lbl)

            Clock.schedule_once(lambda dt: self.update_labels(), 0)

    
    def update_labels(self):
        # Ensure labels are present.
        if len(self.top_labels) < 8:
            self.add_labels()
        # Define the inner chessboard as the 8x8 area (rows 2 to 9, cols 0 to 7).
        grid_origin = (self.x + self.offset_value, self.y + self.offset_value)
        chess_origin = (grid_origin[0], grid_origin[1] + 2 * self.square_size)
        board_width = 8 * self.square_size
        board_height = 8 * self.square_size
        # Top labels (above the chessboard): Files in rotated coordinates.
        # In our rotated system, top-left is h8 and top-right is a8.
        top_files = ["h","g","f","e","d","c","b","a"]
        for i in range(8):
            lbl = self.top_labels[i]
            lbl.text = f"{top_files[i]}8"
            lbl.font_size = self.square_size * 0.4
            lbl.size = (self.square_size, self.square_size)
            lbl.pos = (chess_origin[0] + i * self.square_size, chess_origin[1] + board_height)
        # Bottom labels (below the chessboard): Files (h1 to a1)
        bottom_files = ["h","g","f","e","d","c","b","a"]
        for i in range(8):
            lbl = self.bottom_labels[i]
            lbl.text = f"{bottom_files[i]}1"
            lbl.font_size = self.square_size * 0.4
            lbl.size = (self.square_size, self.square_size)
            lbl.pos = (chess_origin[0] + i * self.square_size, chess_origin[1] - self.square_size)
        # Left labels (to the left of the chessboard): Ranks 8 to 1.
        for j in range(8):
            lbl = self.left_labels[j]
            lbl.text = f"{8 - j}"
            lbl.font_size = self.square_size * 0.4
            lbl.size = (self.square_size, self.square_size)
            lbl.pos = (chess_origin[0] - self.square_size, chess_origin[1] + (7 - j) * self.square_size)
        # Right labels (to the right of the chessboard): Ranks 8 to 1.
        for j in range(8):
            lbl = self.right_labels[j]
            lbl.text = f"{8 - j}"
            lbl.font_size = self.square_size * 0.4
            lbl.size = (self.square_size, self.square_size)
            lbl.pos = (chess_origin[0] + board_width, chess_origin[1] + (7 - j) * self.square_size)
    
    def move_dot(self, dx, dy):
        new_x = self.dot_step_x + dx
        new_y = self.dot_step_y + dy
        new_x = max(0, min(self.cols * 2, new_x))
        new_y = max(0, min(self.rows * 2, new_y))
        self.dot_step_x = new_x
        self.dot_step_y = new_y
        grid_origin = (self.x + self.offset_value, self.y + self.offset_value)
        new_center = (grid_origin[0] + self.dot_step_x * self.step_size,
                      grid_origin[1] + self.dot_step_y * self.step_size)
        if self.trail_enabled:
            self.trail_points.append(new_center)
            self.path.append(self.adjust_coords(new_x, new_y))
        self.update_canvas()
    
    def adjust_coords(self, x, y):
        return (15-x, 19-y)
    
    def clear_trail(self):
        self.trail_points = []
        self.path = []
        self.update_canvas()
    
    def move_dot_to_chess_square(self, square_str):
        """
        Given a traditional chess square (e.g., "e2"), moves the red dot to that square's center,
        using a rotated coordinate system (90° clockwise rotation):
          Standard chess: col = ord(file)-ord('a'), row = rank-1.
          Then: new_col = 7 - row, new_row = col.
          For the inner chessboard (rows 2 to 9), set:
            dot_step_x = 2 * new_col + 1,
            dot_step_y = 2 * (new_row + 2) + 1.
        For example, "h8": col=7, row=7 => new_col=0, new_row=7,
            dot_step_x = 2*0+1 = 1, dot_step_y = 2*(7+2)+1 = 19.
        """
        if len(square_str) != 2:
            return
        file = square_str[0].lower()
        try:
            rank = int(square_str[1])
        except ValueError:
            return
        col_index = ord(file) - ord('a')   # 0 to 7
        row_index = rank - 1               # 0 to 7
        new_col_index = 7 - row_index
        new_row_index = col_index
        self.dot_step_x = 2 * new_col_index + 1
        self.dot_step_y = 2 * (new_row_index + 2) + 1
        grid_origin = (self.x + self.offset_value, self.y + self.offset_value)
        new_center = (grid_origin[0] + self.dot_step_x * self.step_size,
                      grid_origin[1] + self.dot_step_y * self.step_size)
        if self.trail_enabled:
            self.trail_points.append(new_center)
        self.update_canvas()
    
    def process_chess_move(self, move_str, is_capture, is_castling, is_en_passant, is_white):
        """
        Processes a chess move string (e.g., "e2e4").
        Moves the red dot first to the "from" square then (after 0.5 sec) to the "to" square.
        """

        if len(move_str) < 4:
            return
        from_sq = move_str[:2]
        to_sq = move_str[2:4]
        
        
        self.path = (self.gantry.interpret_chess_move(move_str, is_capture, is_castling, is_en_passant, is_white))
        self.move_dot_to_chess_square(from_sq)
        Clock.schedule_once(lambda dt: self.move_dot_to_chess_square(to_sq), 0.5)

    
    def get_current_mm(self):
        # Get internal half-step coordinates:
        ix = self.dot_step_x
        iy = self.dot_step_y
        # Transform so that h1 (internal (15,19)) becomes (0,0) in half-steps.
        # In our mapping:
        #   h1: (15, 19)  => (15 - 15, 19 - 19) = (0, 0)
        #   a1: should be (0, 14) half-steps, etc.
        desired_x_steps = (15 - ix)
        desired_y_steps = (19 - iy)
        return (desired_x_steps * STEP_MM, desired_y_steps * STEP_MM)


class GantryControlScreen(Screen):
    """
    A composite widget that displays the gantry target board (grid) and arrow buttons.
    The arrow buttons move the red dot by 25mm per press.
    """
    def __init__(self, control_system, **kwargs):
        super(GantryControlScreen, self).__init__(**kwargs)
        self.orientation = 'vertical'
        # The target board occupies most of the space.
        self.control_system = control_system
        self.gantry = self.control_system.gantry
        self.font_size = self.control_system.font_size

        self.capture_move= False

        self.root_layout = BoxLayout(orientation='vertical')

        self.header_layout = headerLayout(control_system = self.control_system, menu=False)
        self.body_layout = BoxLayout(orientation='horizontal')
        self.board_display = BoxLayout(orientation='vertical')
        self.gantry_controls = BoxLayout(orientation='vertical')


        self.target_board = GantryTargetWidget(control_system=self.control_system, size_hint=(1,1))
        self.board_display.add_widget(self.target_board)


        #self.target_board = GantryTargetWidget(size_hint=(1, 0.8))
        self.root_layout.add_widget(self.header_layout)
        self.root_layout.add_widget(HorizontalLine())
        self.root_layout.add_widget(self.body_layout)
        self.body_layout.add_widget(self.board_display)
        self.body_layout.add_widget(self.gantry_controls)
        
        # Create arrow buttons.
        btn_layout = GridLayout(size_hint=(1, 0.4), cols=3, rows=3)
        # We arrange buttons in a simple vertical layout with a nested grid.
        arrow_layout = BoxLayout(orientation='vertical')


        
        nw = IconButton(source="assets/nw.png", size_hint=(0.1, 0.1))
        n  = IconButton(source="assets/n.png",  size_hint=(0.1, 0.1))
        ne = IconButton(source="assets/ne.png", size_hint=(0.1, 0.1))
        w  = IconButton(source="assets/w.png",  size_hint=(0.1, 0.1))
        c = GoButton(gantry=self.gantry, target_board=self.target_board, size_hint=(0.1, 0.1))
        e  = IconButton(source="assets/e.png",  size_hint=(0.1, 0.1))
        sw = IconButton(source="assets/sw.png", size_hint=(0.1, 0.1))
        s  = IconButton(source="assets/s.png",  size_hint=(0.1, 0.1))
        se = IconButton(source="assets/se.png", size_hint=(0.1, 0.1))

        self.pathButton = PathPlanToggleButton(target_widget = self.target_board, font_size=self.font_size)
        self.chess_move_input = ChessMoveInput(target_widget=self.target_board,
                                               path_button=self.pathButton,
                                               on_move_callback=self.on_move_entered,
                                               size_hint=(1, 1), font_size=self.font_size)  
        c_clear  = ClearTrailButton(target_widget=self.target_board, path_toggle_button=self.pathButton, move_input=self.chess_move_input, font_size=self.font_size)
        controls = BoxLayout(orientation='horizontal', size_hint=(1, 0.2))
        self.move_input_block = BoxLayout(orientation='horizontal', size_hint=(1, 0.2))


        controls.add_widget(self.pathButton)
        controls.add_widget(c_clear)
        controls.add_widget(Button(text="Home", font_size=self.font_size, on_press=lambda instance: self.gantry.home()))


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
        # Instantiate the modular chess move input.
              
        # self.move_input.bind(on_text_validate=self.target_board.process_chess_move)
        self.gantry_controls.add_widget(controls)

        self.move_input_block.add_widget(self.chess_move_input)

        capture_toggle = CaptureToggleButton(
            text="Capture Move", font_size=self.font_size,
            size_hint=(0.3, 1))
        capture_toggle.bind(state=self.on_toggle_state)

        self.move_input_block.add_widget(capture_toggle)
        self.gantry_controls.add_widget(self.move_input_block)
        #self.gantry_controls.add_widget(Label(text="Magnet Controls", size_hint=(1, 0.1)))
        self.magnet_control = MagnetControl(gantry=self.gantry, size_hint=(1, 0.2))
        #self.magnet_state = self.magnet_control.get_state()
        self.gantry_controls.add_widget(self.magnet_control)
        commandButton = SendCommandButton(gantry=self.gantry, target_widget=self.target_board, path_toggle_button=self.pathButton, move_input=self.chess_move_input, font_size=self.font_size, size_hint=(1, 0.2))

        self.gantry_controls.add_widget(commandButton)

   
        
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
        self.add_widget(self.root_layout)
        # Optionally, you can add a label to display the current coordinate in mm.
        self.coord_label = Label(text="Target: -- mm", size_hint=(1, 0.1))
        # self.gantry_controls.add_widget(self.coord_label)
        # Update the label periodically.
        Clock.schedule_interval(self.update_label, 0.2)
    
    def update_label(self, dt):
        mm_coord = self.target_board.get_current_mm()
        self.coord_label.text = f"Target: {mm_coord[0]} mm, {mm_coord[1]} mm"

    def on_move_entered(self, move):
        # When a move is entered via the text input, force trail mode so the moves leave a trail.

        self.is_castling = False
        self.is_en_passant = False
        self.is_white = False
        self.target_board.trail_enabled = True
        self.symbol = None
        self.target_board.process_chess_move(move, self.capture_move, self.is_castling, self.is_en_passant, self.is_white, self.symbol)
        # Disable the text input and update its display with the trail coordinates.
        self.chess_move_input.disabled = True
        if self.target_board.trail_points:
            coords = [f"({int(x)},{int(y)})" for x, y in self.target_board.trail_points]
            self.chess_move_input.text = (move)


    def send_command(self):


        pass

    def on_toggle_state(self, instance, value):
        # Update the app-level variable based on the button's state
        self.capture_move = (value == "down")
        print(f"App Variable: capture_move = {self.capture_move}")



class PathPlanToggleButton(Button):
    """
    A toggle button that enables/disables trail updates.
    On first press, it changes to "Finish Path Plan" (green), enables trail mode,
    and disables the text input. On next press, it ends the path, disables trail mode,
    and then disables itself until the trail is cleared.
    """
    def __init__(self, target_widget, **kwargs):
        super(PathPlanToggleButton, self).__init__(**kwargs)
        self.target_widget = target_widget
        self.text = "Start Path Plan"
        self.background_color = [0.8, 0.8, 0.8, 1]
        self.bind(on_release=self.toggle_path)

    def adjust_coords(self, x, y):
        return (15-x, 19-y)
    
    def toggle_path(self, instance):
        if not self.target_widget.trail_enabled:
            # Enable trail mode.
            self.target_widget.trail_enabled = True
            self.text = "Finish Path Plan"
            self.background_color = [0, 1, 0, 1]
            board_origin = (self.target_widget.x + self.target_widget.offset_value,
                            self.target_widget.y + self.target_widget.offset_value)
            current_center = (board_origin[0] + self.target_widget.dot_step_x * self.target_widget.step_size,
                              board_origin[1] + self.target_widget.dot_step_y * self.target_widget.step_size)
            self.target_widget.trail_points.append(current_center)
            print((self.target_widget.dot_step_x, self.target_widget.dot_step_y))
            adjusted_path = self.adjust_coords(self.target_widget.dot_step_x, self.target_widget.dot_step_y)
            self.target_widget.path.append(adjusted_path)
            self.target_widget.update_canvas()
            # Disable the text input.
            if self.parent and hasattr(self.parent, 'chess_move_input'):
                self.parent.chess_move_input.disabled = True
        else:
            # Finish the path: disable trail mode and disable this button.
            self.target_widget.trail_enabled = False
            print("Path Plan finished. Trail path:", self.target_widget.path)

            self.text = "Path Plan Finished"
            self.background_color = [0.5, 0.5, 0.5, 1]
            self.disabled = True

class ClearTrailButton(Button):
    """
    A button that clears the current trail, resets the path planning controls,
    and clears & re-enables the text input.
    """
    def __init__(self, target_widget, path_toggle_button, move_input, **kwargs):
        super(ClearTrailButton, self).__init__(**kwargs)
        self.target_widget = target_widget
        self.path_toggle_button = path_toggle_button
        self.move_input = move_input
        self.text = "Clear Trail"
        self.background_color = [1, 0, 0, 1]
        self.bind(on_release=self.clear_trail)
    
    def clear_trail(self, instance):
        self.target_widget.clear_trail()
        self.target_widget.trail_enabled = False
        self.path_toggle_button.text = "Start Path Plan"
        self.path_toggle_button.background_color = [0.8, 0.8, 0.8, 1]
        self.path_toggle_button.disabled = False
        self.move_input.text = ""
        self.move_input.disabled = False

class GoButton(Button):
    """
    A button that clears the current trail, resets the path planning controls,
    and clears & re-enables the text input.
    """
    def __init__(self, gantry, target_board, **kwargs):
        super(GoButton, self).__init__(**kwargs)
        self.gantry = gantry
        self.target_board = target_board
        self.text = "Go"
        self.font_size = 40
        self.background_color = [0, 0, 0, 1]
        self.bind(on_release=self.send_commands)


    def send_commands(self, instance):
        dot_location = self.target_board.get_current_mm()
        print(f"Sending command: {dot_location}")
        if not self.gantry.simulate:
            self.gantry.send_coordinates_command(dot_location)
    
    




class SendCommandButton(Button):
    """
    A button that clears the current trail and resets the path plan toggle.
    """
    def __init__(self, gantry, target_widget, path_toggle_button, move_input, **kwargs):
        super(SendCommandButton, self).__init__(**kwargs)
        self.target_widget = target_widget
        self.path_toggle_button = path_toggle_button
        self.move_input = move_input
        self.gantry = gantry

        self.text = "Send Command"
        self.background_color = [1, 0, 0, 1]
        self.bind(on_release=self.send_command)
    
    def send_command(self, instance):
        #self.gantry.interpret_move(self.move_input.text, STEP_MM)
        print("Path Plan finished HAHA. Trail path:", self.target_widget.path)
        movements = self.gantry.parse_path_to_movement(self.target_widget.path)
        commands = self.gantry.movement_to_gcode(movements)
        print(f"Sending movements: {movements}")
        print(f"Sending commands: {commands}")

        if not self.gantry.simulate:
            self.gantry.send_commands(commands)

        self.target_widget.clear_trail()
        self.target_widget.trail_enabled = False
        self.path_toggle_button.text = "Start Path Plan"
        self.path_toggle_button.background_color = [0.8, 0.8, 0.8, 1]
        self.path_toggle_button.disabled = False
        self.move_input.text = ""
        self.move_input.disabled = False
        self.path = []
        
class MagnetControl(BoxLayout):
    def __init__(self, gantry, **kwargs):
        super(MagnetControl, self).__init__(**kwargs)
        self.orientation = 'horizontal'
        self.spacing = 0  # No gap between buttons so they look continuous.
        self.gantry = gantry
        
        # Define the three options.
        options = ["MAG OFF", "MOVE MODE", "MAG ON"]
        
        # Create three ToggleButtons that belong to the same group.
        self.buttons = []
        for option in options:
            btn = ToggleButton(text=option,
                               group="segmented",
                               background_normal='',
                               background_down='',
                               # Normal (unselected) background color.
                               background_color=[0.8, 0.8, 0.8, 1],
                               color=[0, 0, 0, 1],
                               size_hint=(1, 1))
            btn.bind(state=self.on_button_state)
            self.buttons.append(btn)
            self.add_widget(btn)
        
        # Set a default selection.
        self.buttons[1].state = 'down'

    def on_button_state(self, instance, value):
        # When the button is selected, use a highlight color; otherwise, the normal color.
        if value == 'down':
            instance.background_color = [0.2, 0.6, 1, 1]  # highlight (blue)
        else:
            instance.background_color = [0.8, 0.8, 0.8, 1]
        self.gantry.magnet_state = self.get_state()
        self.gantry.magnet_control()

    def get_state(self):
        # Return the text of the currently selected button.
        for btn in self.buttons:
            if btn.state == 'down':
                return btn.text
        return None     
    
class CaptureToggleButton(ToggleButton):
    def on_state(self, instance, value):
        # Update a property on the widget itself (or notify the app)
        self.is_capture = (value == "down")
        print(f"Toggle Button: capture_move = {self.is_capture}")



class ChessMoveInput(TextInput):
    """
    A modular text input widget that either accepts traditional chess moves (e.g. "e2e4")
    or displays the current trail's coordinates if a path exists.
    It also disables the path toggle button when there is any text.
    """
    def __init__(self, target_widget, path_button, on_move_callback=None, **kwargs):
        super(ChessMoveInput, self).__init__(**kwargs)
        self.multiline = False
        self.hint_text = "Enter chess move (e.g. e2e4)"
        self.target_widget = target_widget
        self.path_button = path_button
        self.on_move_callback = on_move_callback
        self.bind(on_text_validate=self.handle_move)
        self.bind(text=self.on_text_change)
    
    def on_text_change(self, instance, value):
        # Disable the path button if there is any text.
        
        self.path_button.disabled = bool(value.strip())

    
    def handle_move(self, instance):
        move = self.text.strip().lower()
        # If a path already exists, display its coordinates.
        if self.target_widget.trail_points:
            # coords = [f"({int(x)},{int(y)})" for x, y in self.target_widget.trail_points]
            # self.text = "Path: " + " -> ".join(coords)
            self.text = "hello"
            self.disabled = True
        else:
            if self.on_move_callback and move:
                # Force trail mode on so that the movement leaves a trail.
                self.target_widget.trail_enabled = True
                self.on_move_callback(move)
            #self.text = ""
    



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


# # --- For testing the widget in an app ---
# class TestApp(App):
#     def build(self):
#         return GantryControlWidget()

# if __name__ == '__main__':
#     TestApp().run()














