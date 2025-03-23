from grbl_streamer import GrblStreamer
import time

# Step size in mm
STEP_SIZE = 8  # adjust as needed
FEED_RATE = 10000  # change as needed

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

# Set units to mm and relative positioning mode (G21 G91) before jogging
init_cmd = "$J=G21G91X0F{0}\n".format(FEED_RATE)
print("Sending init jogging command:", repr(init_cmd))
grbl.send_immediately(init_cmd)

print("Use W/A/S/D to jog (W: Y+, S: Y-, A: X-, D: X+). Press Q to quit.")

try:
    while True:
        command = input("Direction (W/A/S/D/Q): ").strip().lower()
        if command == "w":
            cmd = "$J=G21G91Y{0}F{1}\n".format(STEP_SIZE, FEED_RATE)
            print("Sending command:", repr(cmd))
            grbl.send_immediately(cmd)
        elif command == "s":
            cmd = "$J=G21G91Y{0}F{1}\n".format(-STEP_SIZE, FEED_RATE)
            print("Sending command:", repr(cmd))
            grbl.send_immediately(cmd)
        elif command == "a":
            cmd = "$J=G21G91X{0}F{1}\n".format(-STEP_SIZE, FEED_RATE)
            print("Sending command:", repr(cmd))
            grbl.send_immediately(cmd)
        elif command == "d":
            cmd = "$J=G21G91X{0}F{1}\n".format(STEP_SIZE, FEED_RATE)
            print("Sending command:", repr(cmd))
            grbl.send_immediately(cmd)
        elif command == "q":
            print("Exiting.")
            break
        else:
            print("Invalid input. Use W/A/S/D/Q.")
finally:
    # Optionally send a command to stop jogging
    stop_cmd = "$J=G21G91X0Y0F{0}\n".format(FEED_RATE)
    print("Sending stop command:", repr(stop_cmd))
    grbl.send_immediately(stop_cmd)
    grbl.disconnect()
