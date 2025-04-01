import serial
import time

class Gantry():
    def __init__(self):
        self.serial = serial.Serial("/dev/ttyACM0", 115200)
        self.send("\r\n\r")
        time.sleep(2)
        self.serial.flushInput()  
        self.position = None

    def send(self, command):
        self.serial.write(str.encode(command + "\n"))

    def home(self):
        self.send("$H")
        self.send("G91 X0 Y-11")  # Center under H1
        self.send("G92 X0 Y0 Z0") # Reposition coordinate system
        self.position = (0, 0)  
    
    def is_idle(self):
        self.send("?")
        response = self.serial.readline().decode().strip()
        if "Idle" in response:
            return True
        else:
            return False
    
    def get_position(self, max_attempts=10, delay=0.1):
        for _ in range(max_attempts):
            self.send("?")
            response = self.serial.readline().decode().strip()
            
            if 'MPos:' in response:
                pos_part = response.split('MPos:')[1].split('|')[0]
                coords = pos_part.split(',')
            elif 'WPos:' in response:
                pos_part = response.split('WPos:')[1].split('|')[0]
                coords = pos_part.split(',')
            else:
                continue 
                
            x = int(float(coords[0]) + 475)
            y = int(float(coords[1]) + 486)
            
            return x, y   
        return None, None  
    
    def move(self, x, y, blocking = False):
        ''' Absolute positioning'''
        self.send(f"G90 X{x} Y{y}")
        time.sleep(0.05) 

        if blocking:
            self.serial.flushInput()
            while True:
                if self.is_idle():
                    self.serial.flushInput()
                    break

        self.position = (x, y)
                
    
    def jog(self, x, y, blocking = False):
        ''' Relative positioning'''
        self.send(f"G91 X{x} Y{y}")

        if blocking:
            while True:
                pos_str = self.get_position()
                print(pos_str)
                if "Idle" in pos_str:
                    self.serial.flushInput()
                    break

        self.position = self.get_position()












