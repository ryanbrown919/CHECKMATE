import time
import threading
from hall import SenseLayer

class BoardMonitor:
    def __init__(self, poll_interval=0.1):
        self.poll_interval = poll_interval
        self.running = False
        self.previous_state = None
        self.thread = None
        self.sense_board = SenseLayer()

    def start(self):
        """Start monitoring the board state."""
        if not self.running:
            self.running = True
            # Initialize the previous state before starting the loop
            self.previous_state = self.sense_board.get_squares()
            self.thread = threading.Thread(target=self._poll_loop)
            self.thread.start()

    def stop(self):
        """Stop monitoring the board state."""
        self.running = False
        if self.thread:
            self.thread.join()

    def _poll_loop(self):
        while self.running:
            time.sleep(self.poll_interval)
            current_state = self.sense_board.get_squares()
            lifted_square = self._find_lifted_square(self.previous_state, current_state)
            if lifted_square is not None:
                print(f"Piece lifted from square: {lifted_square}")
                # You can add further logic to handle the move here.
            self.previous_state = current_state

    def _find_lifted_square(self, old_state, new_state):
        """Return the coordinates (row, col) of a square where a piece was lifted.
           Assumes that a value (e.g., 1 or True) indicates occupancy and 0/False indicates empty."""
        for i in range(len(old_state)):
            for j in range(len(old_state[i])):
                # Detect a change from occupied to empty.
                if old_state[i][j] and not new_state[i][j]:
                    return (i, j)
        return None

# Example usage:
monitor = BoardMonitor(poll_interval=0.1)
monitor.start()

# Later, when you want to stop monitoring:
# monitor.stop()
