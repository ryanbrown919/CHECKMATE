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

# Set relative positioning mode (G91)
cmd = "G91\n"
print("Sending command:", repr(cmd))
grbl.send_immediately(cmd)

print("Use W/A/S/D to move Up/Left/Down/Right by 50mm. Press Q to quit.")

try:
    while True:
        command = input("Direction (W/A/S/D/Q): ").strip().lower()
        if command == "w":
            cmd = "G1 " + "Y" + str(STEP_SIZE) + " " + "F1000\n"
            print("Sending command:", repr(cmd))
            grbl.send_immediately(cmd)
        elif command == "s":
            cmd = "G1 " + "Y" + str(-STEP_SIZE) + " " + "F1000\n"
            print("Sending command:", repr(cmd))
            grbl.send_immediately(cmd)
        elif command == "a":
            cmd = "G1 " + "X" + str(-STEP_SIZE) + " " + "F1000\n"
            print("Sending command:", repr(cmd))
            grbl.send_immediately(cmd)
        elif command == "d":
            cmd = "G1 " + "X" + str(STEP_SIZE) + " " + "F1000\n"
            print("Sending command:", repr(cmd))
            grbl.send_immediately(cmd)
        elif command == "q":
            print("Exiting.")
            break
        else:
            print("Invalid input. Use W/A/S/D/Q.")
finally:
    # Return to absolute positioning (G90)
    cmd = "G90\n"
    print("Sending command:", repr(cmd))
    grbl.send_immediately(cmd)
    grbl.disconnect()
