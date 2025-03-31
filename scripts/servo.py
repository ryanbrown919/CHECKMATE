import lgpio
import sys
import time

class Rocker():
    def __init__(self):
        self.servo_pin = 18
        self.switch_pin = 23
        self.handle = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_output(self.handle, self.servo_pin)
        lgpio.gpio_claim_input(self.handle, self.switch_pin, lgpio.SET_PULL_UP)
        
        # Servo PWM configuration
        self.PWM_FREQ = 50
        self.CENTER_DUTY = 7.5
        self.OPEN_DUTY = 9
        self.CLOSE_DUTY = 6
        self.MAX_WAIT_TIME = 2.0

        print(f"Initialized servo on pin {self.servo_pin} with switch on pin {self.switch_pin}")
        print(f"PWM settings: frequency={self.PWM_FREQ}Hz, center={self.CENTER_DUTY}, open={self.OPEN_DUTY}, close={self.CLOSE_DUTY}")

    def begin(self):
        current_state = self.get_switch_state()
        print(f"Initial switch state: {'HIGH' if current_state else 'LOW'}")

        if current_state:
            self.to_black()
        else:
            self.home()

    def get_switch_state(self):
        return lgpio.gpio_read(self.handle, self.switch_pin)

    def home(self):
        self._move_servo(self.CENTER_DUTY)
    
    def to_white(self):
        print("Moving to white position")
        self._move_servo(self.OPEN_DUTY)
        self._wait_for_switch_change()
        self.home()
    
    def to_black(self):
        print("Moving to black position")
        self._move_servo(self.CLOSE_DUTY)
        self._wait_for_switch_change()
        self.home()
    
    def _move_servo(self, duty_cycle):
        lgpio.tx_pwm(self.handle, self.servo_pin, self.PWM_FREQ, duty_cycle)
    
    def _wait_for_switch_change(self):
        initial_state = self.get_switch_state()
        start_time = time.time()
        while time.time() - start_time <= self.MAX_WAIT_TIME:
            if self.get_switch_state() != initial_state:
                break
    
    def toggle(self):
        if self.get_switch_state():
            self.to_white()
        else:
            self.to_black()

    def cleanup(self):
        lgpio.tx_pwm(self.handle, self.servo_pin, 0, 0)
        lgpio.gpiochip_close(self.handle)

if __name__ == "__main__":
    rocker = Rocker()
    rocker.begin()
    try:
        while True:
            input("Press Enter to toggle...")
            rocker.toggle()
    except KeyboardInterrupt:
        pass
    finally:
        rocker.cleanup()




