from grbl_streamer import GrblStreamer
from nfc import NFC

# Configuration parameters
STEP_SIZE = 50       # Jog distance in mm
FEED_RATE = 10000    # Feed rate in mm/min

# Callback function to handle events from GRBL
def my_callback(eventstring, *data):
    args = [str(d) for d in data]
    print("MY CALLBACK: event={} data={}".format(eventstring.ljust(30), ", ".join(args)))

# Create GrblStreamer instance and connect
grbl = GrblStreamer(my_callback)
grbl.setup_logging()
grbl.cnect("/dev/ttyACM0", 115200)``

# Start polling GRBL state and clear alarms
grbl.poll_start()
grbl.send_immediately("$X\n")

# Initialize the NFC device
nfc_device = NFC()
nfc_device.begin()

# Display control menu
print("Control Menu:")
print("  WASD: Jog (W=Y+, S=Y-, A=X-, D=X+)")
print("  H   : Home")
print("  C   : Clear alarms")
print("  M   : Manual G-code input mode")
print("  N   : NFC mode (Read/Write)")
print("  Q   : Quit")

def send_jog_command(axis, distance):
    # Build a jog command in the format: $J=G21G91{axis}{distance}F{feed_rate}\n
    cmd = f"$J=G21G91{axis}{distance}F{FEED_RATE}\n"
    print("Sending jog command:", repr(cmd))
    grbl.send_immediately(cmd)

while True:
    mode = input("Enter command (W/A/S/D, H, C, M, N, Q): ").strip().lower()
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
    elif mode == "h":
        # Home command (ensure your GRBL supports homing)
        home_cmd = "$H\n"
        print("Sending home command:", repr(home_cmd))
        grbl.send_immediately(home_cmd)
    elif mode == "c":
        # Clear alarms command
        clear_cmd = "$X\n"
        print("Sending clear alarms command:", repr(clear_cmd))
        grbl.send_immediately(clear_cmd)
    elif mode == "m":
        # Manual G-code input mode
        print("Manual G-code mode. Enter G-code commands (enter 'b' to return to main menu).")
        while True:
            gcode = input("Manual G-code: ").strip()
            if gcode.lower() == "b":
                print("Returning to main menu.")
                break
            if not gcode.endswith("\n"):
                gcode += "\n"
            print("Sending manual command:", repr(gcode))
            grbl.send_immediately(gcode)
    elif mode == "n":
        # NFC mode: prompt for NFC operations
        print("NFC Mode. Enter 'r' to read, 'w' to write, or 'b' to return to main menu.")
        while True:
            nfc_action = input("NFC command (r/w/b): ").strip().lower()
            if nfc_action == "b":
                print("Returning to main menu.")
                break
            elif nfc_action == "r":
                success, data = nfc_device.read()
                if success:
                    print("NFC read success. Data:", data)
                else:
                    print("NFC read failed.")
            elif nfc_action == "w":
                fen_piece = input("Enter FEN piece to write (e.g., K, Q, R, etc.): ").strip()
                if nfc_device.write(fen_piece):
                    print("NFC write successful.")
                else:
                    print("NFC write failed.")
            else:
                print("Invalid NFC command. Use 'r', 'w', or 'b'.")
    else:
        print("Invalid command. Please use W/A/S/D, H, C, M, N, or Q.")

grbl.disconnect()
