import RPi.GPIO as GPIO  # Imports the standard Raspberry Pi GPIO library
from time import sleep   # Imports sleep (aka wait or pause) into the program
GPIO.setmode(GPIO.BOARD) # Sets the pin numbering system to use the physical layout

# Set up pin 11 for PWM
GPIO.setup(11,GPIO.OUT)  # Sets up pin 11 to an output (instead of an input)
p = GPIO.PWM(11, 50)     # Sets up pin 11 as a PWM pin
p.start(0)      

def open():
    p.ChangeDutyCycle(4)

def close():
    p.ChangeDutyCycle(11)

def main():
    cmd = input("Enter command (open/close): ").strip().lower()
    if cmd == "open":
        open()
    elif cmd == "close":
        close()
    else:
        print("Invalid command")
    

if __name__ == "__main__":
    while True:
        main()
