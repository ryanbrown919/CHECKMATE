from grbl_streamer import GrblStreamer
import time

# Step size in mm
STEP_SIZE = 50

# Callback function to handle events from GRBL
def my_callback(eventstring, *data):
    print(f"EVENT: {eventstring.ljust(30)} DATA: {', '.join(str(d) for d in data)}")

# Create GrblStreamer instance
grbl = GrblStreamer(my_callback)
grbl.setup_logging()

# Connect to your GRBL controller (change the port if needed)
grbl.cnect("/dev/ttyACM0", 115200)

# Start polling GRBL state
grbl.poll_start()

# Set relative positioning mode and add newline at the end
grbl.send_immediately("G91\n")

print("Use W/A/S/D to move Up/Left/Down/Right by 50mm. Press Q to quit.")

try:
    while True:
        command = input("Direction (W/A/S/D/Q): ").strip().lower()
        if command == "w":
            grbl.send_immediately(f"G1 Y{STEP_SIZE} F1000\n")
        elif command == "s":
            grbl.send_immediately(f"G1 Y{-STEP_SIZE} F1000\n")
        elif command == "a":
            grbl.send_immediately(f"G1 X{-STEP_SIZE} F1000\n")
        elif command == "d":
            grbl.send_immediately(f"G1 X{STEP_SIZE} F1000\n")
        elif command == "q":
            print("Exiting.")
            break
        else:
            print("Invalid input. Use W/A/S/D/Q.")
finally:
    # Return to absolute positioning and ensure newline is appended
    grbl.send_immediately("G90\n")
    grbl.disconnect()
