import time
from gantry_control import GantryControl

def toggle_magnet(gantry_control):
    gantry_control.send("M8")
    time.sleep(0.3)
    gantry_control.send("M9")

def magnet_on(gantry_control):
    gantry_control.send("M8")

def magnet_off(gantry_control):
    gantry_control.send("M9")

def magnet_carlsen(gantry_control):
    gantry_control.set_acceleration(1000)

    for i in range(8):
        gantry_control.move(0, i*50 - 5)
        magnet_on(gantry_control)
        time.sleep(0.3)
        gantry_control.send(f"G3 X0 Y{i*50 + 5} I-5 J0")
        gantry_control.send(f"G3 X0 Y{i*50 - 5} I5 J0")
        magnet_off(gantry_control)
        time.sleep(0.1)
    
    for i in range(7, -1, -1):
        gantry_control.move(50, i*50 - 5)
       magnet_on(gantry_control)
        time.sleep(0.3)
        gantry_control.send(f"G3 X50 Y{i*50 + 5} I-5 J0")
        gantry_control.send(f"G3 X50 Y{i*50 - 5} I5 J0")
        magnet_off(gantry_control)
        time.sleep(0.1)

    for i in range(8):
        gantry_control.move(300, i*50 - 5)
        magnet_on(gantry_control)
        time.sleep(0.3)
        gantry_control.send(f"G3 X300 Y{i*50 + 5} I-5 J0")
        gantry_control.send(f"G3 X300 Y{i*50 - 5} I5 J0")
        magnet_off(gantry_control)
        time.sleep(0.1)
    
    for i in range(7, -1, -1):
        gantry_control.move(350, i*50 - 5)
        magnet_on(gantry_control)
        time.sleep(0.3)
        gantry_control.send(f"G3 X350 Y{i*50 + 5} I-5 J0")
        gantry_control.send(f"G3 X350 Y{i*50 - 5} I5 J0")
        magnet_off(gantry_control)
        time.sleep(0.1)

    gantry_control.set_acceleration(400)

if __name__ == "__main__":
    gantry_control = GantryControl()
    gantry_control.home()
    while True:
        input("Press Enter to start the magnet test...")
        magnet_carlsen(gantry_control)
    