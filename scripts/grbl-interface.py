from grbl_streamer import GrblStreamerimport serial
import time

# Configuration
PORT = "/dev/ttyUSB0"  # Change to COM3 or similar on Windows
BAUD = 115200
STEP_SIZE = 50  # mm

# Initialize GRBL serial connection
ser = serial.Serial(PORT, BAUD)
time.sleep(2)  # Wait for GRBL to initialize
ser.flushInput()

# Set to relative positioning mode
ser.write(b"G91\n")
time.sleep(0.1)

print("Connected to GRBL. Enter direction to move (u/d/l/r), or 'q' to quit.")
print("Each move is 50mm. Commands: u=up, d=down, l=left, r=right")

def send_move(command):
    ser.write((command + "\n").encode())
    while True:
        response = ser.readline().decode().strip()
        print(f"GRBL: {response}")
        if response in ["ok", "error"]:
            break

try:
    while True:
        direction = input("Move (u/d/l/r): ").lower()
        if direction == "u":
            send_move(f"G0 Y{STEP_SIZE}")
        elif direction == "d":
            send_move(f"G0 Y{-STEP_SIZE}")
        elif direction == "l":
            send_move(f"G0 X{-STEP_SIZE}")
        elif direction == "r":
            send_move(f"G0 X{STEP_SIZE}")
        elif direction == "q":
            print("Exiting...")
            break
        else:
            print("Invalid input. Use u/d/l/r/q.")

finally:
    ser.write(b"G90\n")  # Reset to absolute mode
    ser.close()
