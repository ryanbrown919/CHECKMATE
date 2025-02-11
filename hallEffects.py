import random
import platform
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, BooleanProperty, ListProperty
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.slider import Slider

class ChessSquare(Widget):
    # Property for analog sensor reading.
    analog_value = NumericProperty(0)
    # Occupied flag is true if the sensor reading is above a threshold.
    occupied = BooleanProperty(False)
    # The RGBA color of the square.
    color = ListProperty([1, 1, 1, 1])

    def __init__(self, **kwargs):
        super(ChessSquare, self).__init__(**kwargs)
        # Redraw when position, size, or color changes.
        self.bind(pos=self.redraw, size=self.redraw, color=self.redraw)
        # Update the square when the analog value changes.
        self.bind(analog_value=self.on_analog_value)
        # A label that shows "Occupied" when applicable.
        self.label = Label(text="", center=self.center)
        self.add_widget(self.label)

    def redraw(self, *args):
        # Clear the canvas and redraw the square with its current color.
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.color)
            Rectangle(pos=self.pos, size=self.size)
        # Update the label's position and text.
        self.label.center = self.center
        self.label.text = "Occupied" if self.occupied else ""

    def on_analog_value(self, instance, value):
        # Use a threshold of 0.5 to determine occupation.
        threshold = 0.5
        self.occupied = value > threshold
        # Create a gradient effect: as value increases, red goes up and blue goes down.
        self.color = [value, 0, 1 - value, 1]
        self.redraw()

class ChessBoardHallEffect(GridLayout):
    def __init__(self, simulation_mode=False, **kwargs):
        super(ChessBoardHallEffect, self).__init__(**kwargs)
        # Create a 2x2 grid.
        self.cols = 2
        self.rows = 2
        self.squares = []
        for _ in range(4):
            sq = ChessSquare()
            self.add_widget(sq)
            self.squares.append(sq)
        # On non-simulation mode (Linux), update sensors periodically.
        if not simulation_mode:
            Clock.schedule_interval(self.update_sensors, 1)

    def update_sensors(self, dt):
        # Replace this random simulation with your sensor reading logic.
        for square in self.squares:
            square.analog_value = random.random()

class ChessBoardScreen(BoxLayout):
    """
    This widget serves as the main screen.
    It contains the chess board grid and, when in simulation mode (non-Linux),
    adds slider controls to manually adjust the analog values.
    """
    def __init__(self, **kwargs):
        super(ChessBoardScreen, self).__init__(**kwargs)
        self.orientation = "vertical"
        # Determine simulation mode: if not Linux, we assume simulation.
        simulation_mode = (platform.system() != "Linux")
        self.board = ChessBoardHallEffect(simulation_mode=simulation_mode)
        self.add_widget(self.board)
        if simulation_mode:
            # Create a slider panel to simulate sensor values.
            slider_layout = GridLayout(cols=2, size_hint_y=0.3)
            self.sliders = []
            for i, square in enumerate(self.board.squares):
                label = Label(text=f"Square {i+1}")
                slider = Slider(min=0, max=1, value=square.analog_value)
                # Bind the slider's value to update the square's analog_value.
                slider.bind(value=lambda instance, value, sq=square: setattr(sq, 'analog_value', value))
                slider_layout.add_widget(label)
                slider_layout.add_widget(slider)
                self.sliders.append(slider)
            self.add_widget(slider_layout)

class ChessBoardApp(App):
    def build(self):
        return ChessBoardScreen()

if __name__ == '__main__':
    ChessBoardApp().run()
