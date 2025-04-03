import time
from control_system import ControlSystem

def toggle_magnet(control_system):
    control_system.gantry.send("M8")
    time.sleep(0.1)
    control_system.gantry.send("M9")

def carlsen(control_system):
    for i in range(8):
        cmd = f"G1 X0 Y{i*50}"
        control_system.gantry.send_commands(cmd)
        toggle_magnet(control_system)
    
    for i in range(7, -1, -1):
        cmd = f"G1 X50 Y{i*50}"
        control_system.gantry.send_commands(cmd)
        toggle_magnet(control_system)

    for i in range(8):
        cmd = f"G1 X300 Y{i*50}"
        control_system.gantry.send_commands(cmd)
        toggle_magnet(control_system)
    
    for i in range(7, -1, -1):
        cmd = f"G1 X350 Y{i*50}"
        control_system.gantry.send_commands(cmd)
        toggle_magnet(control_system)

if __name__ == "__main__":
    control_system = ControlSystem()
    control_system.gantry.home()
    carlsen(control_system)