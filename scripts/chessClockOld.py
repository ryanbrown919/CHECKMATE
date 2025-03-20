import time
#import machine
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.uix.button import Button

# Configuration
TOTAL_TIME = 300           # Total time per player in seconds (e.g., 5 minutes)
ENABLE_INCREMENT = True    # Enable extra time addition on toggle
INCREMENT_TIME = 5         # Extra seconds to add if conditions are met
INCREMENT_THRESHOLD = 10   # Only add time if player's remaining time is below this threshold

# Global variables for time, active player, and paused state.
player1_time = TOTAL_TIME
player2_time = TOTAL_TIME
active_player = 1  # 1 for player 1, 2 for player 2
paused = False     # False = clocks running; True = clocks paused

# Try to import the machine module for GPIO (Pi 4B)
try:
    from machine import Pin
    USE_MACHINE = True
except ImportError:
    print("machine module not found; running in simulation mode.")
    USE_MACHINE = False

def toggle_active_player(*args):
    """
    Toggle the active player and, if the increment option is enabled, add extra time
    to the player who just moved if their remaining time is below the specified threshold.
    """
    global active_player, player1_time, player2_time

    if ENABLE_INCREMENT:
        if active_player == 1 and player1_time < INCREMENT_THRESHOLD:
            player1_time += INCREMENT_TIME
            print("Incremented player 1 time by", INCREMENT_TIME)
        elif active_player == 2 and player2_time < INCREMENT_THRESHOLD:
            player2_time += INCREMENT_TIME
            print("Incremented player 2 time by", INCREMENT_TIME)

    active_player = 2 if active_player == 1 else 1
    print("Switched active player to", active_player)

# If using hardware, set up the physical switch on GPIO pin 17.
if USE_MACHINE:
    # Set up GPIO pin 17 as an input with an internal pull-up (assumes a normally HIGH button).
    switch_pin = Pin(17, Pin.IN, Pin.PULL_UP)
    switch_pin.irq(trigger=Pin.IRQ_FALLING, handler=lambda pin: toggle_active_player())

class ChessClockWidget(BoxLayout):
    def __init__(self, **kwargs):
        super(ChessClockWidget, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 20

        # Create a horizontal layout for the two clocks.
        clocks_layout = BoxLayout(orientation='horizontal', spacing=20)
        self.player1_label = Label(text=self.format_time(player1_time), font_size='64sp')
        self.player2_label = Label(text=self.format_time(player2_time), font_size='64sp')
        clocks_layout.add_widget(self.player1_label)
        clocks_layout.add_widget(self.player2_label)
        self.add_widget(clocks_layout)

        # Create a horizontal layout for the control buttons.
        controls_layout = BoxLayout(orientation='horizontal', spacing=20, size_hint=(1, 0.2))

        # In simulation mode, add an on-screen button to simulate the physical toggle.
        if not USE_MACHINE:
            self.simulation_button = Button(text="Toggle Active Player", font_size='24sp')
            self.simulation_button.bind(on_press=lambda instance: toggle_active_player())
            controls_layout.add_widget(self.simulation_button)

        # Pause/Play button to toggle the countdown.
        self.pause_button = Button(text="Pause", font_size='24sp')
        self.pause_button.bind(on_press=self.toggle_pause)
        controls_layout.add_widget(self.pause_button)

        # Reset button to restart the clocks.
        self.reset_button = Button(text="Reset", font_size='24sp')
        self.reset_button.bind(on_press=self.reset_clocks)
        controls_layout.add_widget(self.reset_button)

        self.add_widget(controls_layout)

        # Schedule the clock update function.
        Clock.schedule_interval(self.update_clock, 0.1)

    def format_time(self, seconds):
        """Convert seconds into a mm:ss formatted string."""
        minutes = int(seconds) // 60
        secs = int(seconds) % 60
        return f"{minutes:02d}:{secs:02d}"

    def update_clock(self, dt):
        """Update the active player's clock, if not paused."""
        global player1_time, player2_time, active_player, paused

        if paused:
            return

        if active_player == 1 and player1_time > 0:
            player1_time -= dt
            if player1_time < 0:
                player1_time = 0
        elif active_player == 2 and player2_time > 0:
            player2_time -= dt
            if player2_time < 0:
                player2_time = 0

        self.player1_label.text = self.format_time(player1_time)
        self.player2_label.text = self.format_time(player2_time)

    def toggle_pause(self, instance):
        """Toggle between pause and play modes and update button text accordingly."""
        global paused
        paused = not paused
        if paused:
            self.pause_button.text = "Play"
            print("Paused")
        else:
            self.pause_button.text = "Pause"
            print("Resumed")

    def reset_clocks(self, instance):
        """
        Reset both clocks to the starting time, set the active player to 1,
        and resume if paused.
        """
        global player1_time, player2_time, active_player, paused
        player1_time = TOTAL_TIME
        player2_time = TOTAL_TIME
        active_player = 1
        paused = False
        self.pause_button.text = "Pause"
        self.player1_label.text = self.format_time(player1_time)
        self.player2_label.text = self.format_time(player2_time)
        print("Clocks have been reset.")

class ChessClockApp(App):
    def build(self):
        return ChessClockWidget()

if __name__ == '__main__':
    ChessClockApp().run()
