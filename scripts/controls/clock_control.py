

class ClockLogic:
    def __init__(self, total_time=300, enable_increment=True, increment_time=5, increment_threshold=10, timer_enabled=False):
        self.total_time = total_time
        self.enable_increment = enable_increment
        self.increment_time = increment_time
        self.increment_threshold = increment_threshold
        self.timer_enabled = timer_enabled

        self.white_time = total_time
        self.black_time = total_time
        self.active_player = 1  # 1 for player1, 2 for player2
        self.paused = True     # False = running, True = paused

    def update(self, dt):
        """Call this method regularly to update the active player's clock."""
        if self.paused:
            return
        if self.active_player == 1 and self.white_time > 0:
            self.white_time = max(0, self.white_time - dt)
        elif self.active_player == 2 and self.black_time > 0:
            self.black_time = max(0, self.black_time - dt)

    def toggle_active_player(self):
        """
        Switch the active player. If increment is enabled and the current player's remaining
        time is below the threshold, add extra seconds.
        """
        if self.enable_increment:
            if self.active_player == 1 and self.white_time < self.increment_threshold:
                self.white_time += self.increment_time
                print("Incremented player 1 time by", self.increment_time)
            elif self.active_player == 2 and self.black_time < self.increment_threshold:
                self.black_time += self.increment_time
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
        self.white_time = self.total_time
        self.black_time = self.total_time
        self.active_player = 1
        self.paused = False
        print("Clocks have been reset.")

    def format_time(self, seconds):
        """Return a string in mm:ss format."""
        minutes = int(seconds) // 60
        secs = int(seconds) % 60
        return f"{minutes:02d}:{secs:02d}"

    # def update_display(self, dt):
    #     """Update the ChessClock and refresh the display labels."""
    #     self.clock_instance.update(dt)
    #     self.white_label.text = self.format_time(self.clock_instance.white_time)
    #     self.black_label.text = self.format_time(self.clock_instance.black_time)

    # def on_pause(self, instance):
    #     """Toggle pause and update the button text."""
    #     self.clock_instance.toggle_pause()
    #     self.pause_button.text = "Play" if self.clock_instance.paused else "Pause"

    # def on_reset(self, instance):
    #     """Reset the clock and update the display immediately."""
    #     self.clock_instance.reset()
    #     self.white_label.text = self.format_time(self.clock_instance.white_time)
    #     self.black_label.text = self.format_time(self.clock_instance.black_time)
    #     self.pause_button.text = "Pause"
