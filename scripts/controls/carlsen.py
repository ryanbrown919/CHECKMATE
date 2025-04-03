import time
from gantry_control import GantryControl

def toggle_magnet(gantry_control):
    gantry_control.send("M8")
    time.sleep(0.2)
    gantry_control.send("M9")

def magnet_carlsen(gantry_control):
    gantry_control.set_acceleration(1000)

    for i in range(8):
        gantry_control.move(0, i*50)
        toggle_magnet(gantry_control)
    
    for i in range(7, -1, -1):
        gantry_control.move(50, i*50)
        toggle_magnet(gantry_control)

    for i in range(8):
        gantry_control.move(300, i*50)
        toggle_magnet(gantry_control)
    
    for i in range(7, -1, -1):
        gantry_control.move(350, i*50)
        toggle_magnet(gantry_control)

    gantry_control.set_acceleration(400)

if __name__ == "__main__":
    gantry_control = GantryControl()
    gantry_control.home()
    while True:
        input("Press Enter to start the magnet test...")
        magnet_carlsen(gantry_control)
    