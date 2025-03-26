from grbl_streamer import GrblStreamer
from nfc import NFC
import time

# Configuration parameters
STEP_SIZE = 50       # Jog distance in mm
FEED_RATE = 50000    # Feed rate in mm/min

# Callback function to handle events from GRBL
def my_callback(eventstring, *data):
    args = [str(d) for d in data]
    print("MY CALLBACK: event={} data={}".format(eventstring.ljust(30), ", ".join(args)))

# Create GrblStreamer instance
grbl = GrblStreamer(my_callback)
grbl.setup_logging()

# Create NFC instance
nfc = NFC()
nfc.begin()

# Connect to your GRBL controller (change the port if needed)
grbl.cnect("/dev/ttyACM0", 115200)

# Start polling GRBL state and clear alarms
grbl.poll_start()
time.sleep(2)
# grbl.send_immediately("$X\n")

# Display control menu
print("Control Menu:")
print("  WASD: Jog (W=Y+, S=Y-, A=X-, D=X+)")
print("  H   : Home")
print("  C   : Clear alarms")
print("  M   : Manual G-code input mode")
print("  Q   : Quit")

def send_jog_command(axis, distance):
    # Build a jog command in the format: $J=G21G91{axis}{distance}F{feed_rate}\n
    cmd = f"$J=G21G91{axis}{distance}F{FEED_RATE}\n"
    print("Sending jog command:", repr(cmd))
    grbl.send_immediately(cmd)

while True:
    mode = input("Enter command (W/A/S/D, H, C, M, Q): ").strip().lower()
    if mode == "q":
        print("Exiting.")
        break
    elif mode == "w":
        send_jog_command("Y", STEP_SIZE)

    elif mode == "s":
        send_jog_command("Y", -STEP_SIZE)

    elif mode == "a":
        send_jog_command("X", -STEP_SIZE)

    elif mode == "d":
        send_jog_command("X", STEP_SIZE)

    elif mode == "on":
        grbl.send_immediately("M8\n")

    elif mode == "off":
        grbl.send_immediately("M9\n")

    elif mode == "h":
        # Home command; usually $H triggers GRBL homing cycle (ensure your GRBL supports it)
        home_cmd = "$H\n"
        print("Sending home command:", repr(home_cmd))
        grbl.send_immediately(home_cmd)
        grbl.send_immediately("G90X-475Y-486")
        grbl.send_immediately("G92X0Y0Z0")

    elif mode == "c":
        # Clear alarms command
        clear_cmd = "$X\n"
        print("Sending clear alarms command:", repr(clear_cmd))
        grbl.send_immediately(clear_cmd)

    elif mode == "m":
        # Manual mode: prompt for arbitrary G-code strings.
        print("Manual G-code mode. Enter G-code commands (type 'b' to return to main menu).")
        while True:
            gcode = input("Manual G-code: ").strip()
            if gcode.lower() == "b":
                print("Returning to main menu.")
                break
            if not gcode.endswith("\n"):
                gcode += "\n"
            print("Sending manual command:", repr(gcode))
            grbl.send_immediately(gcode)

    elif mode == "read":
        read_ok, piece = nfc.read()
        if read_ok:
            print("Read successful")
            print("Piece: " + piece)
        else:
            print("Read failed")

    elif mode == "write":
        while True:
            piece = input("Enter piece: ")
            if piece in ["K", "Q", "R", "B", "N", "P", "k", "q", "r", "b", "n", "p"]:
                break
            else:
                print("Invalid piece. Please try again.")

        write_ok = nfc.write(piece)
        if write_ok:
            print("Write successful")
        else:
            print("Write failed")

    else:
        print("Invalid command. Please use W/A/S/D, H, C, M, or Q.")

grbl.disconnect()
