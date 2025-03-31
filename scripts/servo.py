import lgpio
import sys
import time

class Rocker():
    def __init__(self):
        self.servo_pin = 17
        self.switch_pin = None # Placeholder for switch pin
        self.handle = lgpio.gpiochip_open(0)
        lpgio.gpio_claim_output(self.handle, self.servo_pin)
        self.state = "home"
        self.last_state = "home"  

    def begin(self):
        self.open()
        time.sleep(0.5)
        self.home()
        self.state = get_switch_state()

    def get_switch_state(self):
        return lgpio.gpio_read(self.handle, self.switch_pin)

    def home(self):
        lgpio.tx_pwm(self.handle, self.servo_pin, 10000, 50)
        self.state = "home"
    
    def open(self):
        initial_state = self.get_switch_state()
        while not (self.get_switch_state() ^ initial_state):
            lgpio.tx_pwm(self.handle, self.servo_pin, 10000, 62)
            time.sleep(0.005)
        self.home()
    
    def close(self):
        initial_state = self.get_switch_state()
        while not (self.get_switch_state() ^ initial_state):
            lgpio.tx_pwm(self.handle, self.servo_pin, 10000, 38)
            time.sleep(0.005)
        self.home()
    
    def toggle(self):
        if self.last_state == "open":
            if self.get_switch_state():
                self.close()
            else:
                self.open()

if __name__ == "__main__":
    rocker = Rocker()
    rocker.begin()
    try:
        while True:
            input("Press Enter to toggle the servo")
            rocker.toggle()
    except KeyboardInterrupt:
        rocker.home()
        rocker.handle.cleanup()
        sys.exit(0)




