import lgpio
import sys
import time

'''
@ryan: install pigpio (pip install pigpio) and run the daemon "sudo pigpiod" in the terminal whenever power cycling the pi so that this can work"
'''

# Configuration
SERVO_GPIO_PIN = 17    # Change this to the GPIO pin you are using for the servo
DUTY_CYCLE = 50        # Duty cycle for the servo (0-100)

class Servo():
    def __init__(self):
        self.handle = lgpio.gpiochip_open(0)
        lpgio.gpio_claim_output(self.handle, SERVO_GPIO_PIN)
        self.state = "home"
        self.last_state = "home"  

    def begin(self):
        self.open()
        time.sleep(0.5)
        self.home()
        self.state = "home"
        self.last_state = "open"

    def home(self):
        lgpio.tx_pwm(self.handle, SERVO_GPIO_PIN, 10000, 50)
        self.state = "home"
    
    def open(self):
        lgpio.tx_pwm(self.handle, SERVO_GPIO_PIN, 10000, 62)
        self.state = "open"
    
    def close(self):
        lgpio.tx_pwm(self.handle, SERVO_GPIO_PIN, 10000, 38)
        self.state = "close"
    
    def toggle(self):
        if self.last_state == "open":
            self.close()
            time.sleep(0.5)
            self.home()
            self.last_state = "close"
        elif self.last_state == "close":
            self.open()
            time.sleep(0.5)
            self.home()
            self.last_state = "open"

if __name__ == "__main__":
    servo = Servo()
    servo.begin()
    try:
        while True:
            input("Press Enter to toggle the servo")
            servo.toggle()
    except KeyboardInterrupt:
        servo.pi.stop()
        sys.exit(0)




