from grbl_streamer import GrblStreamer
import time

# Callback function to handle events from GRBL
def my_callback(eventstring, *data):
    args = [str(d) for d in data]
    print("MY CALLBACK: event={} data={}".format(eventstring.ljust(30), ", ".join(args)))

# Create GrblStreamer instance
grbl = GrblStreamer(my_callback)
grbl.setup_logging()

# Connect to your GRBL controller (change the port if needed)
grbl.cnect("/dev/ttyACM0", 115200)

# Start polling GRBL state
grbl.poll_start()
grbl.send_immediately("$$\n")  # Ensuring newline termination

print("Enter any G-code command to send. Type 'q' to quit.")

try:
    while True:
        gcode = input("G-code: ").strip()
        if gcode.lower() == "q":
            print("Exiting.")
            break
        # # Ensure the command ends with a newline
        # if not gcode.endswith("\n"):
        #     gcode += "\n"
        print("Sending command:", repr(gcode))
        grbl.send_immediately(gcode)
finally:
    grbl.disconnect()
