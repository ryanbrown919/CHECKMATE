import lgpio
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

    def begin(self):
        if self.get_switch_state():
            self.to_white()
        else:
            self.home()

    def get_switch_state(self):
        DEBOUNCE_COUNT = 5
        DEBOUNCE_DELAY = 0.005 
        
        readings = []
        for _ in range(DEBOUNCE_COUNT):
            readings.append(lgpio.gpio_read(self.handle, self.switch_pin))
            time.sleep(DEBOUNCE_DELAY)
        
        high_count = readings.count(1)
        low_count = readings.count(0)
        
        return 1 if high_count > low_count else 0

    def home(self):
        self._move_servo(self.CENTER_DUTY)
    
    def to_white(self):
        self._move_servo(self.OPEN_DUTY)
        self._wait_for_switch_change()
        self.home()
    
    def to_black(self):
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




