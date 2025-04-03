import time
from gantry import Gantry

def toggle_magnet(gantry):
    gantry.send("M8")
    time.sleep(0.5)
    gantry.send("M9")
    time.sleep(0.5)

def carlsen(gantry):
    for i in range(8):
        cmd = f"G1 X0 Y{i*50}"
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

if __name__ == "__main__":
    gantry = Gantry()
    gantry.home()
    carlsen(gantry)