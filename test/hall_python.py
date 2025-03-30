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

    #/* q1    q2     q3     q4*/
hall_map_felipe =  {
    7: [(2, 7),  (2, 3),  (5, 0),  (5, 4)], 
   3:  [(3, 7),  (3, 3),  (4, 0),  (4, 4)], 
    2: [(3, 6),  (3, 2),  (4, 1),  (4, 5)], 
    6:[(2, 6),  (2, 2),  (5, 1),  (5, 5)], 
    0:[(3, 4),  (3, 0),  (4, 3),  (4, 7)], 
    4:[(2, 4),  (2, 0),  (5, 3),  (5, 7)], 
    5:[(2, 5),  (2, 1),  (5, 2),  (5, 6)], 
    1:[(3, 5),  (3, 1),  (4, 2),  (4, 6)], 
    10:[(1, 6),  (1, 2),  (6, 1),  (6, 5)], 
    11:[(1, 7),  (1, 3),  (6, 0),  (6, 4)], 
    15:[(0, 7),  (0, 3),  (7, 0),  (7, 4)], 
    14:[(0, 6),  (0, 2),  (7, 1),  (7, 5)], 
    8: [(1, 4),  (1, 0),  (6, 3),  (6, 7)], 
    9: [(1, 5),  (1, 1),  (6, 2),  (6, 6)], 
    13: [(0, 5),  (0, 1),  (7, 2),  (7, 6)],
    12: [(0, 4),  (0, 0),  (7, 3),  (7, 7)] }


hall_map = {
    1: [(4, 0), (4, 4), (3, 7), (3, 3)],
    2: [(4, 1), (4, 5), (3, 6), (3, 2)],
    3: [(4, 2), (4, 6), (3, 5), (3, 1)],
    4: [(4, 3), (4, 7), (3, 4), (3, 0)],
    5: [(5, 0), (5, 4), (2, 7), (2, 3)],
    6: [(5, 1), (5, 5), (2, 6), (2, 2)],
    7: [(5, 2), (5, 6), (2, 5), (2, 1)],
    8: [(5, 3), (5, 7), (2, 4), (2, 0)],
    9: [(6, 0), (6, 4), (1, 7), (1, 3)],
    10: [(6, 1), (6, 5), (1, 6), (1, 2)],
    11: [(6, 2), (6, 6), (1, 5), (1, 1)],
    12: [(6, 3), (6, 7), (1, 4), (1, 0)],
    13: [(7, 0), (7, 4), (0, 7), (0, 3)],
    14: [(7, 1), (7, 5), (0, 6), (0, 2)],
    15: [(7, 2), (7, 6), (0, 5), (0, 1)],
    16: [(7, 3), (7, 7), (0, 4), (0, 0)]
}
hall_map_encoded = {
    7: [(4, 0), (4, 4), (3, 7), (3, 3)],
    12: [(4, 1), (4, 5), (3, 6), (3, 2)],
    1: [(4, 2), (4, 6), (3, 5), (3, 1)],
    10: [(4, 3), (4, 7), (3, 4), (3, 0)],
    6: [(5, 0), (5, 4), (2, 7), (2, 3)],
    8: [(5, 1), (5, 5), (2, 6), (2, 2)],
    0: [(5, 2), (5, 6), (2, 5), (2, 1)],
    14: [(5, 3), (5, 7), (2, 4), (2, 0)],
    3: [(6, 0), (6, 4), (1, 7), (1, 3)],
    13: [(6, 1), (6, 5), (1, 6), (1, 2)],
    5: [(6, 2), (6, 6), (1, 5), (1, 1)],
    11: [(6, 3), (6, 7), (1, 4), (1, 0)],
    2: [(7, 0), (7, 4), (0, 7), (0, 3)],
    9: [(7, 1), (7, 5), (0, 6), (0, 2)],
    4: [(7, 2), (7, 6), (0, 5), (0, 1)],
    15: [(7, 3), (7, 7), (0, 4), (0, 0)]
}

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
    """Retrieve an 8x8 array representing the chessboard occupancy using the encoded table."""
    occupancy = [[0 for _ in range(8)] for _ in range(8)]
    for select, positions in hall_map_felipe.items():
        set_select_pins(select)
        time.sleep(0.001)  # Small delay to allow signals to stabilize
        mux_values = read_mux_outputs()
        for i, value in enumerate(mux_values):
            row, col = positions[i]
            occupancy[row][col] = value
    return occupancy

if __name__ == "__main__":
    try:
        setup_gpio()
        while True:
            board = get_chessboard_occupancy()
            for row in board:
                print(row)
            print("Done")
            time.sleep(1)  # Update every second
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        GPIO.cleanup()