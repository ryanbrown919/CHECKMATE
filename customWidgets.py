
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.uix.togglebutton import ToggleButton



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
    def __init__(self, menu=False, **kwargs):
        # You can set orientation, size_hint, padding, etc.
        super(headerLayout, self).__init__(**kwargs)
        self.orientation='horizontal'
        self.padding=10
        self.spacing=0
        self.size_hint=(1, 0.2)
        icon = Image(source='figures/logo.png', allow_stretch=True, keep_ratio=True, size_hint=(0.1, 1))

        if not menu:
            self.add_widget(Label(text="Check-M.A.T.E", font_size=120, size_hint=(0.4, 1)))

            self.add_widget(Widget(size_hint_x=0.4))
            self.add_widget(IconButton(source="figures/hamburgMenu.png", 
                                                size_hint=(0.1, 1),  # Disable relative sizing
                                                        # Set explicit dimensions
                                                allow_stretch=True,      # Allow the image to stretch to fill the widget
                                                keep_ratio=True          # Maintain the image's aspect ratio
                                                ))
            self.add_widget(icon)

        else:
            self.add_widget(Label(text="Check-M.A.T.E", font_size=120, size_hint=(0.4, 1)))
            self.add_widget(Widget(size_hint_x=0.5))
            icon = Image(source='figures/logo.png', allow_stretch=True, keep_ratio=True, size_hint=(0.1, 1))
            self.add_widget(icon)



class ChessBoardWidget(Widget):
    def __init__(self, orientation='N', **kwargs):
        """
        orientation is kept for future extension, but here we always use white at the bottom (north up).
        """
        super(ChessBoardWidget, self).__init__(**kwargs)
        self.orientation = orientation  # reserved for future rotations if needed
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

class MagnetControl(BoxLayout):
    def __init__(self, **kwargs):
        super(MagnetControl, self).__init__(**kwargs)
        self.orientation = 'horizontal'
        self.spacing = 0  # No gap between buttons so they look continuous.
        
        # Define the three options.
        options = ["OFF", "CHESS MODE", "ON"]
        
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

    def get_state(self):
        # Return the text of the currently selected button.
        for btn in self.buttons:
            if btn.state == 'down':
                return btn.text
        return None