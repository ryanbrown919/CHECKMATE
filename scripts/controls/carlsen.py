import time
from gantry_control import GantryControl

def toggle_magnet(gantry_control):
    gantry_control.send("M8")
    time.sleep(0.2)
    gantry_control.send("M9")

def carlsen(gantry_control):
    for i in range(8):
        cmd = f"G1 X0 Y{i*50}"
        gantry_control.send_commands(cmd)
        toggle_magnet(gantry_control)
    
    for i in range(7, -1, -1):
        cmd = f"G1 X50 Y{i*50}"
        gantry_control.send_commands(cmd)
        toggle_magnet(gantry_control)

    for i in range(8):
        cmd = f"G1 X300 Y{i*50}"
        gantry_control.send_commands(cmd)
        toggle_magnet(gantry_control)
    
    for i in range(7, -1, -1):
        cmd = f"G1 X350 Y{i*50}"
        gantry_control.send_commands(cmd)
        toggle_magnet(gantry_control)

if __name__ == "__main__":
    gantry_control = GantryControl()
    gantry_control.home()
    carlsen(gantry_control)