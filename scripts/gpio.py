import RPi.GPIO as GPIO
import time

class Multiplexer:
    # Multiplexer control pins
    MUX_S0 = 6
    MUX_S1 = 13
    MUX_S2 = 19
    MUX_S3 = 26

    # Multiplexer output pins
    MUX_Y_1 = 16
    MUX_Y_2 = 12
    MUX_Y_3 = 21
    MUX_Y_4 = 20

    def __init__(self):
        self.init()

    def init(self):
        # Set up GPIO mode
        GPIO.setmode(GPIO.BCM)
        
        # Set up control pins as outputs
        for pin in [self.MUX_S0, self.MUX_S1, self.MUX_S2, self.MUX_S3]:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
        
        # Set up output pins as inputs with pull-up resistors
        for pin in [self.MUX_Y_1, self.MUX_Y_2, self.MUX_Y_3, self.MUX_Y_4]:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def set_pins(self, nibble):
        # Set the control pins based on the 4-bit nibble
        GPIO.output(self.MUX_S0, nibble & 0x1)
        GPIO.output(self.MUX_S1, (nibble >> 1) & 0x1)
        GPIO.output(self.MUX_S2, (nibble >> 2) & 0x1)
        GPIO.output(self.MUX_S3, (nibble >> 3) & 0x1)

    def get_output(self):
        # Read the output pins and combine them into a byte
        output = 0
        if GPIO.input(self.MUX_Y_1): output |= (1 << 0)
        if GPIO.input(self.MUX_Y_2): output |= (1 << 1)
        if GPIO.input(self.MUX_Y_3): output |= (1 << 2)
        if GPIO.input(self.MUX_Y_4): output |= (1 << 3)
        return output

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

    def begin(self):
        # Nothing additional needed here as mux is initialized in __init__
        pass

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
            time.sleep(0.005)  # Short delay for multiplexer settling

            # Read the outputs
            outputs = self.mux.get_output()

            # Update board array based on sensor readings
            for j in range(4):
                col = self.hall_to_board_mapping[i][j][0]
                row = self.hall_to_board_mapping[i][j][1]
                
                # Invert the logic: 0 means a piece is present
                board[row][col] = 0 if ((outputs >> j) & 1) else 1

        return board

    def get_square_cartesian(self, x, y):
        """
        Read the sensor state at board coordinates (x, y).
        Returns 1 if piece detected, 0 if no piece.
        """
        # Scan through all multiplexer combinations
        for i in range(16):
            for j in range(4):
                # Check if this multiplexer setting reads the desired square
                if (self.hall_to_board_mapping[i][j][0] == x and 
                    self.hall_to_board_mapping[i][j][1] == y):
                    
                    # Set the multiplexer
                    current_gray = i ^ (i >> 1)
                    self.mux.set_pins(current_gray)
                    time.sleep(0.005)
                    
                    # Read the specific output
                    outputs = self.mux.get_output()
                    return 0 if ((outputs >> j) & 1) else 1

        # If coordinates weren't found in the mapping
        return 0

    def get_square_from_notation(self, square):
        """
        Read the sensor at the square given in algebraic notation (e.g., 'e4').
        Returns 1 if piece detected, 0 if no piece, or False if invalid notation.
        """
        square = square.lower()
        if square not in self.square_mapping:
            return False
            
        x, y = self.square_mapping[square]
        return self.get_square_cartesian(x, y)
        
    def cleanup(self):
        """Clean up GPIO resources"""
        GPIO.cleanup()

def main():
    """Test function that continuously monitors the chess board"""
    try:
        layer = SenseLayer()
        layer.begin()
        print("Starting continuous board monitoring. Press Ctrl+C to exit.")
        
        while True:
            # Clear the screen (optional)
            print("\033[H\033[J", end="")  # ANSI escape sequence to clear screen
            
            # Read and display the full board
            print("Current Board State:")
            board = layer.get_squares()
            
            # Print column headers
            print("  a b c d e f g h")
            print(" +-----------------+")
            
            # Print board with row numbers
            for y in range(7, -1, -1):
                row_str = f"{y+1}|"
                for x in range(8):
                    if board[y][x] == 1:
                        row_str += "■ "  # Unicode filled square for pieces
                    else:
                        row_str += "· "  # Unicode middle dot for empty squares
                print(row_str + "|")
            
            print(" +-----------------+")
            print("  a b c d e f g h")
            
            # Add a delay to make the output readable
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    finally:
        # Always clean up GPIO resources on exit
        GPIO.cleanup()

if __name__ == "__main__":
    main()