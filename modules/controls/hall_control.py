import lgpio
import time
import threading
import copy



class Multiplexer:
    MUX_S0 = 6
    MUX_S1 = 13
    MUX_S2 = 19
    MUX_S3 = 26

    MUX_Y_1 = 16
    MUX_Y_2 = 12
    MUX_Y_3 = 21
    MUX_Y_4 = 20

    def __init__(self):
        self.handle = lgpio.gpiochip_open(0)
        self.init()

    def init(self):
        # Set up control pins as outputs
        for pin in [self.MUX_S0, self.MUX_S1, self.MUX_S2, self.MUX_S3]:
            lgpio.gpio_claim_output(self.handle, pin)
            lgpio.gpio_write(self.handle, pin, 0)
        
        # Set up output pins as inputs with pull-down resistors
        for pin in [self.MUX_Y_1, self.MUX_Y_2, self.MUX_Y_3, self.MUX_Y_4]:
            lgpio.gpio_claim_input(self.handle, pin, lgpio.SET_PULL_DOWN)

    def set_pins(self, nibble):
 
        lgpio.gpio_write(self.handle, self.MUX_S0, (nibble >> 0) & 0x1)
        lgpio.gpio_write(self.handle, self.MUX_S1, (nibble >> 1) & 0x1)
        lgpio.gpio_write(self.handle, self.MUX_S2, (nibble >> 2) & 0x1)
        lgpio.gpio_write(self.handle, self.MUX_S3, (nibble >> 3) & 0x1)

    def get_output(self):
        output = 0
        if lgpio.gpio_read(self.handle, self.MUX_Y_1): output |= (1 << 0)
        if lgpio.gpio_read(self.handle, self.MUX_Y_2): output |= (1 << 1)
        if lgpio.gpio_read(self.handle, self.MUX_Y_3): output |= (1 << 2)
        if lgpio.gpio_read(self.handle, self.MUX_Y_4): output |= (1 << 3)
        return output

    def cleanup(self):
        lgpio.gpiochip_close(self.handle)

class SenseLayer:
    # Mapping from hall effect sensors to board coordinates
    hall_to_board_mapping = [
        # q1    q2     q3     q4
        [[2, 7], [2, 3], [5, 0], [5, 4]],  # HALL  7 mapping
        [[3, 7], [3, 3], [4, 0], [4, 4]],  # HALL  3 mapping
        [[3, 6], [3, 2], [4, 1], [4, 5]],  # HALL  2 mapping
        [[2, 6], [2, 2], [5, 1], [5, 5]],  # HALL  6 mapping
        [[3, 4], [3, 0], [4, 3], [4, 7]],  # HALL  0 mapping
        [[2, 4], [2, 0], [5, 3], [5, 7]],  # HALL  4 mapping
        [[2, 5], [2, 1], [5, 2], [5, 6]],  # HALL  5 mapping
        [[3, 5], [3, 1], [4, 2], [4, 6]],  # HALL  1 mapping
        [[1, 6], [1, 2], [6, 1], [6, 5]],  # HALL 10 mapping
        [[1, 7], [1, 3], [6, 0], [6, 4]],  # HALL 11 mapping
        [[0, 7], [0, 3], [7, 0], [7, 4]],  # HALL 15 mapping
        [[0, 6], [0, 2], [7, 1], [7, 5]],  # HALL 14 mapping
        [[1, 4], [1, 0], [6, 3], [6, 7]],  # HALL  8 mapping
        [[1, 5], [1, 1], [6, 2], [6, 6]],  # HALL  9 mapping
        [[0, 5], [0, 1], [7, 2], [7, 6]],  # HALL 13 mapping
        [[0, 4], [0, 0], [7, 3], [7, 7]]   # HALL 12 mapping
    ]

    # Chess notation mapping
    square_mapping = {f"{file}{rank}": (ord(file) - ord('a'), int(rank) - 1)
                      for file in "abcdefgh" for rank in "12345678"}

    def __init__(self):
        self.rows = 8
        self.cols = 8
        self.mux = Multiplexer()

    def get_squares(self):
        """
        Scan the entire board and return a 2D array of sensor values.
        1 = piece detected, 0 = no piece
        """
        # Create an 8x8 board initialized to all zeros
        board = [[0 for _ in range(self.cols)] for _ in range(self.rows)]

        # Scan through all multiplexer combinations
        for i in range(16):
            # Convert i to Gray code for more reliable multiplexing
            current_gray = i ^ (i >> 1)
            self.mux.set_pins(current_gray)
            time.sleep(0.0005)  # Short delay for multiplexer settling

            # Read the outputs
            outputs = self.mux.get_output()

            # Update board array based on sensor readings
            for j in range(4):
                col = self.hall_to_board_mapping[i][j][0]
                row = self.hall_to_board_mapping[i][j][1]
                
                # Invert the logic: 0 means a piece is present
                board[row][col] = 0 if ((outputs >> j) & 1) else 1

        return board
    
    def get_squares_gantry(self):
        board = self.get_squares()

        # transposed_np = board.T
        # print("Transposed Matrix (NumPy):")
        # print(transposed_np)

        # # Rotate the original matrix 90° counterclockwise using np.rot90
        # rotated_ccw_np = np.rot90(board, k=1)  # k=1 rotates by 90° CCW
        # # print("\nRotated 90° Counterclockwise (NumPy):")
        # print(rotated_ccw_np)

        transposed_board = list(map(list, zip(*board)))
        # transposed_board = board
        #board_t = [[transposed_board[j][i] for j in range(len(transposed_board))] for i in range(len(transposed_board[0])-1,-1,-1)]
        # final_board = list(map(list, zip(*board_t)))

        return transposed_board
    
    def get_squares_game(self):
        board = self.get_squares()
        transposed_board = list(map(list, zip(*board)))

        return transposed_board

    def get_square_from_notation(self, square):
        """
        Read the sensor at the square given in algebraic notation (e.g., 'e4').
        Returns 1 if piece detected, 0 if no piece, or False if invalid notation.
        """
        square = square.lower()
        if square not in self.square_mapping:
            return False
        
        board = self.get_squares()
            
        x, y = self.square_mapping[square]
        return board[y][x]
        
    def cleanup(self):
        """Clean up GPIO resources"""
        self.mux.cleanup()

    def main_test():
        """Test function that continuously monitors the chess board"""
        try:
            layer = SenseLayer()
            # layer.begin()
            print("Chess board monitoring - Press Ctrl+C to exit")
            
            while True:
                # Clear the screen for better readability
                print("\033[H\033[J", end="")
                
                # Read the board
                board = layer.get_squares()
                
                # Print the board with coordinate labels
                print("  a b c d e f g h")
                print(" +-----------------+")
                
                # Print the board rows in reverse order (8 to 1)
                for y in range(7, -1, -1):
                    row_str = f"{y+1}|"
                    for x in range(8):
                        if board[y][x] == 1:  # Piece present
                            row_str += "■ "  # Filled square for occupied
                        else:
                            row_str += "□ "  # Hollow square for empty
                    print(row_str + f"|{y+1}")
                
                print(" +-----------------+")
                print("  a b c d e f g h")
                
                # Count total pieces
                total = sum(sum(row) for row in board)
                print(f"Total pieces: {total}")
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
        finally:
            layer.cleanup()


class Hall:
    # Constants for state machine
    WAITING_FOR_FIRST_CHANGE = 0
    WAITING_FOR_SECOND_CHANGE = 1
    MOVE_DETECTED = 2
    
    def __init__(self):
        self.sense_layer = SenseLayer()
        self.lock = threading.Lock()
        self.reference_board = None
        self.current_board = None
        self.first_change = None
        self.second_change = None
        self.state = self.WAITING_FOR_FIRST_CHANGE
        self.move_detected_event = threading.Event()
        self.polling_thread = None
        self.running = False
        self.poll_interval = 0.05  # Default polling interval in seconds

    def board_to_chess_notation(self, row, col):
        files = "abcdefgh"
        ranks = "12345678"
        file = files[col]
        rank = ranks[row]
        return f"{file}{rank}"

    def compare_boards(self, current_board, reference_board):
        changes = []
        
        for row in range(8):
            for col in range(8):
                if reference_board[row][col] != current_board[row][col]:
                    change = self.board_to_chess_notation(row, col)
                    changes.append(change)
        
        return changes[0] if len(changes) == 1 else None

    def start_polling(self, callback=None, poll_interval=0.05):
        """Start polling the board for changes with the specified polling interval"""
        if self.polling_thread and self.polling_thread.is_alive():
            return  # Already polling
        
        self.poll_interval = poll_interval
        self.running = True
        self.move_detected_event.clear()
        self.reference_board = self.sense_layer.get_squares_game()
        self.state = self.WAITING_FOR_FIRST_CHANGE
        self.first_change = None
        self.second_change = None
        
        self.polling_thread = threading.Thread(
            target=self._polling_loop,
            args=(callback,),
            daemon=True
        )
        self.polling_thread.start()

    def stop_polling(self):
        """Stop the board polling"""
        self.running = False
        if self.polling_thread:
            self.polling_thread.join(timeout=1.0)

    def _polling_loop(self, callback=None):
        """Main polling loop that implements the state machine"""
        consecutive_identical_readings = 0
        required_identical = 3  # Number of identical readings required to confirm a change
        
        while self.running:
            with self.lock:
                current_board = self.sense_layer.get_squares_game()
                
                if self.state == self.WAITING_FOR_FIRST_CHANGE:
                    changes = self.compare_boards(current_board, self.reference_board)
                    if changes:
                        # Potential first change detected, but wait for confirmation
                        if not self.first_change:
                            self.first_change = changes
                            consecutive_identical_readings = 1
                        elif self.first_change == changes:
                            consecutive_identical_readings += 1
                            if consecutive_identical_readings >= required_identical:
                                # First change confirmed
                                self.reference_board = current_board
                                self.state = self.WAITING_FOR_SECOND_CHANGE
                                consecutive_identical_readings = 0
                        else:
                            # Reading changed, reset counter
                            self.first_change = changes
                            consecutive_identical_readings = 1
                    else:
                        # No change, reset detection
                        self.first_change = None
                        consecutive_identical_readings = 0
                
                elif self.state == self.WAITING_FOR_SECOND_CHANGE:
                    changes = self.compare_boards(current_board, self.reference_board)
                    if changes:
                        # Potential second change detected
                        if not self.second_change:
                            self.second_change = changes
                            consecutive_identical_readings = 1
                        elif self.second_change == changes:
                            consecutive_identical_readings += 1
                            if consecutive_identical_readings >= required_identical:
                                # Second change confirmed, move complete
                                self.state = self.MOVE_DETECTED
                                self.reference_board = current_board
                                move = f"{self.first_change}{self.second_change}"
                                self.move_detected_event.set()
                                if callback:
                                    callback(move)
                                # Reset for next move
                                self.state = self.WAITING_FOR_FIRST_CHANGE
                                self.first_change = None
                                self.second_change = None
                                consecutive_identical_readings = 0
                        else:
                            # Reading changed, reset counter
                            self.second_change = changes
                            consecutive_identical_readings = 1
                    else:
                        # If no second change for a while, it might be a piece lifted and returned
                        consecutive_identical_readings += 1
                        if consecutive_identical_readings > 30:  # ~1.5 seconds at 0.05s interval
                            # Reset to initial state - piece likely returned to original position
                            self.state = self.WAITING_FOR_FIRST_CHANGE
                            self.first_change = None
                            self.second_change = None
                            consecutive_identical_readings = 0
            
            time.sleep(self.poll_interval)

    def wait_for_move(self, timeout=None):
        """Wait for a complete move to be detected and return it"""
        if self.move_detected_event.wait(timeout):
            return f"{self.first_change}{self.second_change}"
        return None

    def get_current_board_state(self):
        """Get the current state of the board"""
        with self.lock:
            return copy.deepcopy(self.sense_layer.get_squares_game())
            
    def cleanup(self):
        """Clean up resources"""
        self.stop_polling()
        self.sense_layer.cleanup()