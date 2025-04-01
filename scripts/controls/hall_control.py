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

    def __init__(self):

        self.sense_layer = SenseLayer()
        # self.sense_layer.begin()
        self.initial_board = self.sense_layer.get_squares()
        self.lock = threading.Lock()
        self.reference_board = None
        self.first_change = None
        self.second_change = None
        self.move = None

    def board_to_chess_notation(self, row, col):
        return f"{chr(96 + row)}{col}"

    def compare_boards(self, board, reference_board):
        # if self.initial_board is None:
        #     self.initial_board = board
        #     self.reference_board = board
        #     return None, None

        # Compare with the reference board
        for row in range(8):
            for col in range(8):
                print(f"Checking: {repr(reference_board[row][col])} == {repr(board[row][col])}")
                if reference_board[row][col] != board[row][col]:
                    print("yo these are not the same")
                    change = self.board_to_chess_notation(row, col)
                    print(change)
                    return change  # Update reference board after first change

        return None

    def process_boards(self, boards):
        first_change = None
        second_change = None

        self.reference_board = boards[0]

        for i, board in enumerate(boards):
            # print(f"Board {i + 1}:")
            if first_change is None:
                # print("Checking first change")
                first_change = self.compare_boards(board, self.reference_board)
                if first_change and not second_change:
                    print(f"First change detected: {first_change}")
                    self.reference_board = boards[i]
            elif second_change is None:
                # print("checking second change")
                second_change = self.compare_boards(board, self.reference_board)
                
            else:
                print(f"Move detected: {first_change}{second_change}")
                return f"{first_change}{second_change}"
        print("No changes detected")
        return None
    
    def poll_board_for_change(self, board):

        # print(f"Board {i + 1}:")
        if self.first_change is None:
            # print("Checking first change")
            self.first_change = self.compare_boards(board)
            if self.first_change and not self.second_change:
                print(f"First change detected: {self.first_change}")
                self.reference_board = board
        elif self.second_change is None:
            # print("checking second change")
            self.second_change = self.compare_boards(board)
            
        else:
            print(f"Move detected: {self.first_change}{self.second_change}")
            return f"{self.first_change}{self.second_change}"
        print("No changes detected")
        return None
    
    def scan_for_first_move(self, result_event):

        initial_board = self.sense_layer.get_squares_game()
        print("Initial Board first move")
        # Print the board rows in reverse order (8 to 1)
        for y in range(7, -1, -1):
            row_str = f"{y+1}|"
            for x in range(8):
                if initial_board[y][x] == 1:  # Piece present
                    row_str += "■ "  # Filled square for occupied
                else:
                    row_str += "□ "  # Hollow square for empty
            print(row_str + f"|{y+1}")
        
        print(" +-----------------+")
        print("  a b c d e f g h")

        self.first_change = None

        while self.first_change is None:

            new_board = self.sense_layer.get_squares_game()
            time.sleep(0.5)
            print("New board")
            #print(new_board)
            self.first_change = self.compare_boards(initial_board, new_board)

        result_event.set()    
    def scan_for_second_move(self, result_event):

        with self.lock:

            initial_board = self.sense_layer.get_squares_game()
            print("Initial Board second move")
            print(initial_board)

            self.second_change = None

            while self.second_change is None:

                new_board = self.sense_layer.get_squares_game()
                time.sleep(0.5)

                self.second_change = self.compare_boards(initial_board, new_board)

            result_event.set()

    def wait_for_first_board_change(self, result_event, poll_interval=0.1):
        """
        Poll the board state until a change is detected compared to the initial_board.
        Once a difference is found, store the difference in self.first_change and signal the event.

        Args:
            initial_board: The board state to compare against.
            result_event: A threading.Event to signal when a change is detected.
            poll_interval: Delay in seconds between polls.
        """
        with self.lock:
            time.sleep(0.5)
            initial_board = self.sense_layer.get_squares()
            time.sleep(0.5)

            for y in range(7, -1, -1):
                row_str = f"{y+1}|"
                for x in range(8):
                    if initial_board[y][x] == 1:  # Piece present
                        row_str += "■ "  # Filled square for occupied
                    else:
                        row_str += "□ "  # Hollow square for empty
                print(row_str + f"|{y+1}")
            
            print(" +-----------------+")
            print("  a b c d e f g h")

            while True:
                # Obtain the current board state.
                new_board = self.sense_layer.get_squares()
                time.sleep(0.5)

                print("Polling new board state:", new_board)

                for y in range(7, -1, -1):
                    row_str = f"{y+1}|"
                    for x in range(8):
                        if new_board[y][x] == 1:  # Piece present
                            row_str += "■ "  # Filled square for occupied
                        else:
                            row_str += "□ "  # Hollow square for empty
                    print(row_str + f"|{y+1}")
                
                print(" +-----------------+")
                print("  a b c d e f g h")

                # Compare the boards using your custom function.
                diff = self.compare_boards(initial_board, new_board)
                if diff is not None:
                    self.first_change = diff  # diff can be (row, col, initial_value, new_value)
                    print("Board change detected:", diff)
                    result_event.set()  # Signal that the change was detected.
                    break

                # Sleep briefly to prevent high CPU usage.
                time.sleep(poll_interval)

    def wait_for_second_board_change(self, initial_board, result_event, poll_interval=0.1):
        """
        Poll the board state until a change is detected compared to the initial_board.
        Once a difference is found, store the difference in self.first_change and signal the event.

        Args:
            initial_board: The board state to compare against.
            result_event: A threading.Event to signal when a change is detected.
            poll_interval: Delay in seconds between polls.
        """

        with self.lock:
            initial_board = self.sense_layer.get_squares()

            while True:
                # Obtain the current board state.
                new_board = self.sense_layer.get_squares()
                time.sleep(0.5)

                print("Polling new board state:", new_board)

                # Compare the boards using your custom function.
                diff = self.compare_boards(initial_board, new_board)
                if diff is not None:
                    self.first_change = diff  # diff can be (row, col, initial_value, new_value)
                    print("Board change detected:", diff)
                    result_event.set()  # Signal that the change was detected.
                    break

                # Sleep briefly to prevent high CPU usage.
                time.sleep(poll_interval)

    # def poll_board_for_change(self):
    #     while move is None:
    #         move = self.poll_board_for_change(self.sense_layer.get_squares())

    #     return move