import serial
import time
import threading 

class Gantry():
    def __init__(self):
        self.serial = serial.Serial("/dev/ttyACM0", 115200)

    def begin(self):
        ''' init sequence recommended by grbl '''
        self.send("\r\n\r")
        time.sleep(2)
        self.serial.flushInput()  

    def send(self, command):
        self.serial.write(str.encode(command + "\n"))

    def home(self):
        self.send("$H")
        self.send("G90 X-475 Y-486") # Center under H1
        self.send("G92 X0 Y0 Z0")    # Reposition coordinate system
    
    def get_position(self):
        self.send("?")
        response = self.serial.readline().decode().strip()
        return response
    
    def move(self, x, y, blocking_flag = False):
        ''' Absolute positioning'''
        self.send(f"G90 X{x} Y{y}")

        if blocking_flag:
            while True:
                pos_str = self.get_position()
                if "Idle" in pos_str:
                    self.serial.flushInput()
                    break
    
    def jog(self, x, y, blocking_flag = False)
        ''' Relative positioning'''
        self.send(f"G91 X{x} Y{y}")

        if blocking_flag:
            while True:
                pos_str = self.get_position()
                if "Idle" in pos_str:
                    self.serial.flushInput()
                    break


''' @ryan: example use case that I tested today, unnoticable delay '''

if __name__ == "__main__":
    gantry = Gantry()
    gantry.begin()
    gantry.home()

    while True:
        square = input("Enter target square: ").strip().upper()
        print(f"Moving to {square} ...")
        gantry.move_to_square(square, blocking_flag = True)
        print("Arrived at target.")
            
            

      






