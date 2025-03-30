import time

import RPi.GPIO as GPIO

# GPIO pin configuration
SELECT_PINS = [6, 13, 19, 26]  # GPIO pins for the 4-bit select signal
MUX_OUTPUTS = [16, 12, 21, 20]    # GPIO pins for the outputs of the 4 multiplexers

#define MUX_S0 6
#define MUX_S1 13
#define MUX_S2 19
#define MUX_S3 26

#define MUX_Y_1 16  
#define MUX_Y_2 12   
#define MUX_Y_3 21   
#define MUX_Y_4 20
# Mapping for the hall effect sensors to the chessboard
HALL_MAPPING = [
    [(2, 7), (2, 3), (5, 0), (5, 4)],  # HALL 7 mapping
    [(3, 7), (3, 3), (4, 0), (4, 4)],  # HALL 3 mapping
    [(3, 6), (3, 2), (4, 1), (4, 5)],  # HALL 2 mapping
    [(2, 6), (2, 2), (5, 1), (5, 5)],  # HALL 6 mapping
    [(3, 4), (3, 0), (4, 3), (4, 7)],  # HALL 0 mapping
    [(2, 4), (2, 0), (5, 3), (5, 7)],  # HALL 4 mapping
    [(2, 5), (2, 1), (5, 2), (5, 6)],  # HALL 5 mapping
    [(3, 5), (3, 1), (4, 2), (4, 6)],  # HALL 1 mapping
    [(1, 6), (1, 2), (6, 1), (6, 5)],  # HALL 10 mapping
    [(1, 7), (1, 3), (6, 0), (6, 4)],  # HALL 11 mapping
    [(0, 7), (0, 3), (7, 0), (7, 4)],  # HALL 15 mapping
    [(0, 6), (0, 2), (7, 1), (7, 5)],  # HALL 14 mapping
    [(1, 4), (1, 0), (6, 3), (6, 7)],  # HALL 8 mapping
    [(1, 5), (1, 1), (6, 2), (6, 6)],  # HALL 9 mapping
    [(0, 5), (0, 1), (7, 2), (7, 6)],  # HALL 13 mapping
    [(0, 4), (0, 0), (7, 3), (7, 7)],  # HALL 12 mapping
]


def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    for pin in SELECT_PINS:
        GPIO.setup(pin, GPIO.OUT)
    for pin in MUX_OUTPUTS:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def set_select_pins(value):
    """Set the 4-bit select signal."""
    for i, pin in enumerate(SELECT_PINS):
        GPIO.output(pin, (value >> i) & 1)

def read_mux_outputs():
    """Read the outputs of the 4 multiplexers."""
    return [GPIO.input(pin) for pin in MUX_OUTPUTS]

def get_chessboard_occupancy():
    """Retrieve an 8x8 array representing the chessboard occupancy derived from hall sensor mapping."""
    sensor_values = []
    for select in range(16):  # 16 hall sensors
        set_select_pins(select)
        time.sleep(0.001)  # Small delay to allow signals to stabilize
        mux_values = read_mux_outputs()
        # Determine sensor state as active if any multiplexer output is high.
        sensor_active = any(mux_values)
        sensor_values.append(sensor_active)
    occupancy = apply_hall_mapping(sensor_values)
    return occupancy

def apply_hall_mapping(sensor_values):
    """
    Apply HALL_MAPPING to sensor output.
    sensor_values: List of booleans (length=16) indicating the state of each hall sensor.
    Returns an 8x8 board where each cell is True if activated by any hall sensor.
    """
    # Create an 8x8 board initialized to False.
    chessboard = [[False] * 8 for _ in range(8)]
    for sensor_index, active in enumerate(sensor_values):
        if active:
            for (row, col) in HALL_MAPPING[sensor_index]:
                chessboard[row][col] = True
    return chessboard

def print_chessboard(board):
    """
    Print the chessboard state.
    Active cells are printed as '1', inactive as '0'.
    """
    for row in board:
        print(" ".join("1" if cell else "0" for cell in row))

if __name__ == "__main__":
    try:
        setup_gpio()
        while True:
            board = get_chessboard_occupancy()
            for row in board:
                print(row)
            time.sleep(1)  # Update every second

        
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        GPIO.cleanup()