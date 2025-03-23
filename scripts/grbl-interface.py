from grbl_streamer import GrblStreamer
import time

# Step size in mm
JOG_STEP = 50  # adjust as needed
FEED_RATE = 10000  # change as needed

# Callback function to handle events from GRBL
def my_callback(eventstring, *data):
    args = []
    for d in data:
        args.append(str(d))
    print("MY CALLBACK: event={} data={}".format(eventstring.ljust(30), ", ".join(args)))

# Create GrblStreamer instance
grbl = GrblStreamer(my_callback)
grbl.setup_logging()

# Connect to your GRBL controller (change the port if needed)
grbl.cnect("/dev/ttyACM0", 115200)

# Start polling GRBL state
grbl.poll_start()
grbl.send_immediately("$$")

print("Use W/A/S/D to jog (W: Y+, S: Y-, A: X-, D: X+). Press Q to quit.")

try:
    while True:
        command = input("Direction (W/A/S/D/Q): ").strip().lower()
        if command == "w":
            cmd = cmd = f"$J=G21G91Y{JOG_STEP}F{FEED_DRATE}"
            print("Sending command:", repr(cmd))
            grbl.send_immediately(cmd)
        elif command == "s":
            cmd = f"$J=G21G91Y-{JOG_STEP}F{FEED_DRATE}"  
            print("Sending command:", repr(cmd))
            grbl.send_immediately(cmd)
        elif command == "a":
            cmd = f"$J=G21G91X-{JOG_STEP}F{FEED_RATE}"  # Jog X-
            print("Sending command:", repr(cmd))
            grbl.send_immediately(cmd)
        elif command == "d":
            cmd = f"$J=G21G91X{JOG_STEP}F{FEED_RATE}"  # Jog X+
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
