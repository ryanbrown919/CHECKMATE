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

# Set relative positioning mode (G91) and send newline
grbl.send_immediately("G91\n")

print("Use W/A/S/D to move Up/Left/Down/Right by 50mm. Press Q to quit.")

try:
    while True:
        command = input("Direction (W/A/S/D/Q): ").strip().lower()
        if command == "w":
            # Ensure there are spaces between command parts
            grbl.send_immediately("G1 Y{} F1000\n".format(STEP_SIZE))
        elif command == "s":
            grbl.send_immediately("G1 Y{} F1000\n".format(-STEP_SIZE))
        elif command == "a":
            grbl.send_immediately("G1 X{} F1000\n".format(-STEP_SIZE))
        elif command == "d":
            grbl.send_immediately("G1 X{} F1000\n".format(STEP_SIZE))
        elif command == "q":
            print("Exiting.")
            break
        else:
            print("Invalid input. Use W/A/S/D/Q.")
finally:
    # Return to absolute positioning (G90) and disconnect
    grbl.send_immediately("G90\n")
    grbl.disconnect()
