import pigpio
import sys
import time

'''
@ryan: install pigpio (pip install pigpio) and run the daemon "sudo pigpiod" in the terminal whenever power cycling the pi so that this can work"
'''

# Configuration
SERVO_GPIO_PIN = 17    # Change this to the GPIO pin you are using for the servo
MIN_PULSEWIDTH = 500   # Minimum pulse width in microseconds (adjust for your servo)
MAX_PULSEWIDTH = 2500  # Maximum pulse width in microseconds (adjust for your servo)

class Servo():
    def __init__(self):
        self.pi = pigpio.pi()
        self.pi.set_mode(SERVO_GPIO_PIN, pigpio.OUTPUT)
        self.pi.set_servo_pulsewidth(SERVO_GPIO_PIN, 0)
        self.state = "home"
        self.last_sate = "home"
    
    def duty_cycle_to_pulsewidth(self, duty_cycle, min_pw, max_pw):
        if not (0 <= duty_cycle <= 100):
            raise ValueError("Duty cycle must be between 0 and 100.")
        return min_pw + (duty_cycle / 100.0) * (max_pw - min_pw)

    def begin(self):
        self.close()
        time.sleep(0.5)
        self.home()
        self.state = "home"
        self.last_sate = "close"

    def home(self):
        pulse_width = duty_cycle_to_pulsewidth(50, MIN_PULSEWIDTH, MAX_PULSEWIDTH)
        pi.set_servo_pulsewidth(SERVO_GPIO_PIN, pulse_width)
        self.state = "home"
    
    def open(self):
        pulse_width = duty_cycle_to_pulsewidth(62, MIN_PULSEWIDTH, MAX_PULSEWIDTH)
        pi.set_servo_pulsewidth(SERVO_GPIO_PIN, pulse_width)
        self.state = "open"
    
    def close(self):
        pulse_width = duty_cycle_to_pulsewidth(38, MIN_PULSEWIDTH, MAX_PULSEWIDTH)
        pi.set_servo_pulsewidth(SERVO_GPIO_PIN, pulse_width)
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
            self.last_sate = "open"

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




