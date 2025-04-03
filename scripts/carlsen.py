import time
from gantry import Gantry

def toggle_magnet(gantry):
    gantry.send("M8")
    time.sleep(0.2)
    gantry.send("M9")

def magnet_carlsen(gantry):
    gantry.set_acceleration(1000)

    for i in range(8):
        gantry.move(0, i*50, blocking=True)
        toggle_magnet(gantry)
    
    for i in range(7, -1, -1):
        gantry.move(50, i*50, blocking=True)
        toggle_magnet(gantry)

    for i in range(8):
        gantry.move(300, i*50, blocking=True)
        toggle_magnet(gantry)
    
    for i in range(7, -1, -1):
        gantry.move(350, i*50, blocking=True)
        toggle_magnet(gantry)

    gantry.set_acceleration(400)

if __name__ == "__main__":
    gantry = Gantry()
    gantry.home()
    while True:
        input("Press Enter to start the magnet test...")
        magnet_carlsen(gantry)
    