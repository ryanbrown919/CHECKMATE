import time
from gantry_control import GantryControl

def toggle_magnet(gantry_control):
    gantry_control.send("M8")
    time.sleep(0.2)
    gantry_control.send("M9")

def magnet_carlsen(gantry_control):
    gantry_control.set_acceleration(1000)

    for i in range(8):
        gantry_control.send_commands(f"G90 X0 Y{i*50}")
        toggle_magnet(gantry_control)
    
    for i in range(7, -1, -1):
        gantry_control.send_commands(f"G90 X50 Y{i*50}")
        toggle_magnet(gantry_control)

    for i in range(8):
        gantry_control.send_commands(f"G90 X300 Y{i*50}")
        toggle_magnet(gantry_control)
    
    for i in range(7, -1, -1):
        gantry_control.send_commands(f"G90 X350 Y{i*50}")
        toggle_magnet(gantry_control)

    gantry_control.set_acceleration(400)

if __name__ == "__main__":
    gantry_control = GantryControl()
    gantry_control.home()
    while True:
        input("Press Enter to start the magnet test...")
        magnet_carlsen(gantry_control)
    