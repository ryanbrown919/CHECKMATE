import lgpio
import time

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
        [[7, 2], [3, 2], [0, 5], [4, 5]],  # HALL  7 mapping
        [[7, 3], [3, 3], [0, 4], [4, 4]],  # HALL  3 mapping
        [[6, 3], [2, 3], [1, 4], [5, 4]],  # HALL  2 mapping
        [[6, 2], [2, 2], [1, 5], [5, 5]],  # HALL  6 mapping
        [[4, 3], [0, 3], [3, 4], [7, 4]],  # HALL  0 mapping
        [[4, 2], [0, 2], [3, 5], [7, 5]],  # HALL  4 mapping
        [[5, 2], [1, 2], [2, 5], [6, 5]],  # HALL  5 mapping
        [[5, 3], [1, 3], [2, 4], [6, 4]],  # HALL  1 mapping
        [[6, 1], [2, 1], [1, 6], [5, 6]],  # HALL 10 mapping
        [[7, 1], [3, 1], [0, 6], [4, 6]],  # HALL 11 mapping
        [[7, 0], [3, 0], [0, 7], [4, 7]],  # HALL 15 mapping
        [[6, 0], [2, 0], [1, 7], [5, 7]],  # HALL 14 mapping
        [[4, 1], [0, 1], [3, 6], [7, 6]],  # HALL  8 mapping
        [[5, 1], [1, 1], [2, 6], [6, 6]],  # HALL  9 mapping
        [[5, 0], [1, 0], [2, 7], [6, 7]],  # HALL 13 mapping
        [[4, 0], [0, 0], [3, 7], [7, 7]]   # HALL 12 mapping
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
        self.mux.cleanup()

def main():
    """Test function that continuously monitors the chess board"""
    try:
        layer = SenseLayer()
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

if __name__ == "__main__":
    main()