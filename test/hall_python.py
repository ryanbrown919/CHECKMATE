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
    """Retrieve an 8x8 array representing the chessboard occupancy."""
    occupancy = [[0 for _ in range(8)] for _ in range(8)]
    for select in range(16):  # 16 select signals for the multiplexers
        set_select_pins(select)
        time.sleep(0.001)  # Small delay to allow signals to stabilize
        mux_values = read_mux_outputs()
        for i, value in enumerate(mux_values):
            row = (select * 4 + i) // 8
            col = (select * 4 + i) % 8
            occupancy[row][col] = value
    return occupancy

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