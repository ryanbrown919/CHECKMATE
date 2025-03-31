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
        self.state = None
        
        # Servo PWM configuration
        self.PWM_FREQ = 50  # 50Hz standard servo frequency
        self.CENTER_DUTY = 7.5  # ~1.5ms pulse (center)
        self.OPEN_DUTY = 10.0   # ~2.0ms pulse
        self.CLOSE_DUTY = 5.0   # ~1.0ms pulse
        
        # Configure timeout to prevent infinite loops
        self.MAX_WAIT_TIME = 2.0  # seconds

    def begin(self):
        self.home()
        self.state = self.get_switch_state()

    def get_switch_state(self):
        return lgpio.gpio_read(self.handle, self.switch_pin)

    def home(self):
        lgpio.tx_pwm(self.handle, self.servo_pin, self.PWM_FREQ, self.CENTER_DUTY)
    
    def set_duty_cycle(self, duty_cycle):
        lgpio.tx_pwm(self.handle, self.servo_pin, self.PWM_FREQ, duty_cycle)
        
    def open(self):
        print("Opening...")
        initial_state = self.get_switch_state()
        start_time = time.time()
        
        lgpio.tx_pwm(self.handle, self.servo_pin, self.PWM_FREQ, self.OPEN_DUTY)
        
        # Wait for switch state to change or timeout
        while not (self.get_switch_state() ^ initial_state):
            if time.time() - start_time > self.MAX_WAIT_TIME:
                print("Timeout waiting for switch state to change")
                break
            time.sleep(0.05)  # Less aggressive polling
        
        self.home()
    
    def close(self):
        print("Closing...")
        initial_state = self.get_switch_state()
        start_time = time.time()
        
        lgpio.tx_pwm(self.handle, self.servo_pin, self.PWM_FREQ, self.CLOSE_DUTY)
        
        # Wait for switch state to change or timeout
        while not (self.get_switch_state() ^ initial_state):
            if time.time() - start_time > self.MAX_WAIT_TIME:
                print("Timeout waiting for switch state to change")
                break
            time.sleep(0.05)
        
        self.home()
    
    def toggle(self):
        current_state = self.get_switch_state()
        print(f"Current switch state: {current_state}")
        if current_state:
            self.close()
        else:
            self.open()

if __name__ == "__main__":
    rocker = Rocker()
    try:
        print("Starting servo duty cycle sweep. Press Ctrl+C to exit.")
        
        # Define sweep parameters
        min_duty = 2.0
        max_duty = 12.0
        step = 0.5
        delay = 1.0  # seconds to hold at each position
        
        # First, center the servo
        print(f"Centering servo at {rocker.CENTER_DUTY}%")
        rocker.home()
        time.sleep(1)
        
        # Continuously sweep back and forth
        while True:
            # Sweep up
            print("\nSweeping up...")
            for duty in [min_duty + i*step for i in range(int((max_duty-min_duty)/step) + 1)]:
                print(f"Setting duty cycle: {duty:.1f}%")
                rocker.set_duty_cycle(duty)
                switch_state = rocker.get_switch_state()
                print(f"  Switch state: {switch_state}")
                time.sleep(delay)
            
            # Brief pause at max
            time.sleep(1)
            
            # Sweep down
            print("\nSweeping down...")
            for duty in [max_duty - i*step for i in range(int((max_duty-min_duty)/step) + 1)]:
                print(f"Setting duty cycle: {duty:.1f}%")
                rocker.set_duty_cycle(duty)
                switch_state = rocker.get_switch_state()
                print(f"  Switch state: {switch_state}")
                time.sleep(delay)
            
            # Brief pause at min
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        # Return to center position before exit
        rocker.home()
        time.sleep(0.5)
        
        # Proper cleanup
        lgpio.tx_pwm(rocker.handle, rocker.servo_pin, 0, 0)  # Stop PWM
        lgpio.gpiochip_close(rocker.handle)




