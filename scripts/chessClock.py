import time
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.uix.button import Button

# -------------------------------
# Chess clock logic module
# -------------------------------

class clock_logic:
    def __init__(self, total_time=300, enable_increment=True, increment_time=5, increment_threshold=10):
        self.total_time = total_time
        self.enable_increment = enable_increment
        self.increment_time = increment_time
        self.increment_threshold = increment_threshold

        self.player1_time = total_time
        self.player2_time = total_time
        self.active_player = 1  # 1 for player1, 2 for player2
        self.paused = True     # False = running, True = paused

    def update(self, dt):
        """Call this method regularly to update the active player's clock."""
        if self.paused:
            return
        if self.active_player == 1 and self.player1_time > 0:
            self.player1_time = max(0, self.player1_time - dt)
        elif self.active_player == 2 and self.player2_time > 0:
            self.player2_time = max(0, self.player2_time - dt)

    def toggle_active_player(self):
        """
        Switch the active player. If increment is enabled and the current player's remaining
        time is below the threshold, add extra seconds.
        """
        if self.enable_increment:
            if self.active_player == 1 and self.player1_time < self.increment_threshold:
                self.player1_time += self.increment_time
                print("Incremented player 1 time by", self.increment_time)
            elif self.active_player == 2 and self.player2_time < self.increment_threshold:
                self.player2_time += self.increment_time
                print("Incremented player 2 time by", self.increment_time)
        self.active_player = 2 if self.active_player == 1 else 1
        print("Switched active player to", self.active_player)

    def toggle_pause(self):
        """Toggle between pause and play modes."""
        self.paused = not self.paused
        if self.paused:
            print("Paused")
        else:
            print("Resumed")

    def reset(self):
        """Reset both clocks to the initial total time and set active player to 1."""
        self.player1_time = self.total_time
        self.player2_time = self.total_time
        self.active_player = 1
        self.paused = False
        print("Clocks have been reset.")

    def format_time(self, seconds):
        """Return a string in mm:ss format."""
        minutes = int(seconds) // 60
        secs = int(seconds) % 60
        return f"{minutes:02d}:{secs:02d}"

# -------------------------------
# Kivy widget to display the clock
# -------------------------------

class ChessClockWidget(BoxLayout):
    def __init__(self, clock_instance=None, **kwargs):
        super(ChessClockWidget, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 20

        # If no external ChessClock is provided, create one.
        self.clock_instance = clock_instance

        # Create labels to display times
        clocks_layout = BoxLayout(orientation='horizontal', spacing=20)
        self.player1_label = Label(text=self.format_time(self.clock_instance.player1_time), font_size='64sp')
        self.player2_label = Label(text=self.format_time(self.clock_instance.player2_time), font_size='64sp')
        clocks_layout.add_widget(self.player1_label)
        clocks_layout.add_widget(self.player2_label)
        self.add_widget(clocks_layout)

        # Create control buttons
        controls_layout = BoxLayout(orientation='horizontal', spacing=20, size_hint=(1, 0.2))
        toggle_button = Button(text="Toggle Active Player", font_size='24sp')
        toggle_button.bind(on_press=lambda instance: self.clock_instance.toggle_active_player())
        controls_layout.add_widget(toggle_button)

        self.pause_button = Button(text="Pause", font_size='24sp')
        self.pause_button.bind(on_press=self.on_pause)
        controls_layout.add_widget(self.pause_button)

        reset_button = Button(text="Reset", font_size='24sp')
        reset_button.bind(on_press=self.on_reset)
        controls_layout.add_widget(reset_button)

        self.add_widget(controls_layout)

        # Schedule regular updates for the clock display.
        Clock.schedule_interval(self.update_display, 0.1)

    def format_time(self, seconds):
        """Return a string in mm:ss format."""
        minutes = int(seconds) // 60
        secs = int(seconds) % 60
        return f"{minutes:02d}:{secs:02d}"

    def update_display(self, dt):
        """Update the ChessClock and refresh the display labels."""
        self.clock_instance.update(dt)
        self.player1_label.text = self.format_time(self.clock_instance.player1_time)
        self.player2_label.text = self.format_time(self.clock_instance.player2_time)

    def on_pause(self, instance):
        """Toggle pause and update the button text."""
        self.clock_instance.toggle_pause()
        self.pause_button.text = "Play" if self.clock_instance.paused else "Pause"

    def on_reset(self, instance):
        """Reset the clock and update the display immediately."""
        self.clock_instance.reset()
        self.player1_label.text = self.format_time(self.clock_instance.player1_time)
        self.player2_label.text = self.format_time(self.clock_instance.player2_time)
        self.pause_button.text = "Pause"

# -------------------------------
# Example usage in a Kivy App
# -------------------------------

class ChessClockApp(App):
    def build(self):
        return ChessClockWidget()

if __name__ == '__main__':
    ChessClockApp().run()
