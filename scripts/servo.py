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
        
        # Servo PWM configuration based on 0.5-2.5ms pulse width
        self.PWM_FREQ = 50  # 50Hz standard servo frequency
        self.CENTER_DUTY = 7.5  # ~1.5ms pulse (center)
        self.OPEN_DUTY = 9   # ~2.5ms pulse (maximum)
        self.CLOSE_DUTY = 6   # ~0.5ms pulse (minimum)
        
        # Configure timeout to prevent infinite loops
        self.MAX_WAIT_TIME = 2.0  # seconds
        
        # Track current position
        self.current_position = "home"

    def begin(self):
        self.home()
        self.state = self.get_switch_state()

    def get_switch_state(self):
        return lgpio.gpio_read(self.handle, self.switch_pin)

    def home(self):
        """Move servo to home position and stop PWM after movement completes"""
        print("Moving to home position...")
        self._move_servo(self.CENTER_DUTY)
        self.current_position = "home"
    
    def open(self):
        """Open the mechanism"""
        print("Opening...")
        self._move_servo(self.OPEN_DUTY)
        
        # Wait for switch state to change or timeout
        initial_state = self.get_switch_state()
        start_time = time.time()
        
        while not (self.get_switch_state() ^ initial_state):
            if time.time() - start_time > self.MAX_WAIT_TIME:
                print("Timeout waiting for switch state to change")
                break
            time.sleep(0.05)
        
        # Return to home position
        self.home()
    
    def close(self):
        """Close the mechanism"""
        print("Closing...")
        self._move_servo(self.CLOSE_DUTY)
        
        # Wait for switch state to change or timeout
        initial_state = self.get_switch_state()
        start_time = time.time()
        
        while not (self.get_switch_state() ^ initial_state):
            if time.time() - start_time > self.MAX_WAIT_TIME:
                print("Timeout waiting for switch state to change")
                break
            time.sleep(0.05)
        
        # Return to home position
        self.home()
    
    def _move_servo(self, duty_cycle):
        """Helper method to move servo and stop PWM to prevent jitter"""
        # Set PWM to move the servo
        lgpio.tx_pwm(self.handle, self.servo_pin, self.PWM_FREQ, duty_cycle)
        
        # Give the servo time to reach position
        time.sleep(0.5)
        
        # Option 1: Stop PWM (servo will hold position mechanically)
        # Uncomment this line if you want the servo to relax after moving
        # lgpio.tx_pwm(self.handle, self.servo_pin, 0, 0)
    
    def toggle(self):
        current_state = self.get_switch_state()
        print(f"Current switch state: {current_state}")
        if current_state:
            self.open()
        else:
            self.close()

if __name__ == "__main__":
    rocker = Rocker()
    try:
        rocker.begin()
        print("\nToggle Test - Press Enter to toggle, Ctrl+C to exit\n")
        
        while True:
            input("Press Enter to toggle...")
            rocker.toggle()
            
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        # Clean up
        lgpio.tx_pwm(rocker.handle, rocker.servo_pin, 0, 0)
        lgpio.gpiochip_close(rocker.handle)




