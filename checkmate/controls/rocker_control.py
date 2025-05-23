import lgpio
import time
import threading

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
        self.OPEN_DUTY = 8.7
        self.CLOSE_DUTY = 6.5
        self.MAX_WAIT_TIME = 2.0
        
        # Threading related attributes
        self.pwm_thread = None
        self.thread_lock = threading.Lock()
        self.running = False
        self.current_duty = 0
        self.start_pwm_thread()

    def start_pwm_thread(self):
        """Start the PWM control thread"""
        if self.pwm_thread is None or not self.pwm_thread.is_alive():
            self.running = True
            self.pwm_thread = threading.Thread(target=self._pwm_control_loop)
            self.pwm_thread.daemon = True  # Thread will close when main program exits
            self.pwm_thread.start()
    
    def _pwm_control_loop(self):
        """Main PWM control loop that runs in the thread"""
        while self.running:
            with self.thread_lock:
                if self.current_duty > 0:
                    lgpio.tx_pwm(self.handle, self.servo_pin, self.PWM_FREQ, self.current_duty)
            time.sleep(0.02)  # Small delay to prevent CPU hogging

    def reset(self):
        if self.get_switch_state():
            self.to_white()
        else:
            self.home()

    def get_switch_state(self):
        return lgpio.gpio_read(self.handle, self.switch_pin)

    def home(self):
        self._move_servo(self.CENTER_DUTY)
        time.sleep(0.3)  
        self._stop_servo()  
    
    def to_white(self):
        self._move_servo(self.OPEN_DUTY)
        self._wait_for_switch_change()
        self.home()
    
    def to_black(self):
        self._move_servo(self.CLOSE_DUTY)
        self._wait_for_switch_change()
        self.home()
    
    def _move_servo(self, duty_cycle):
        """Thread-safe way to update the duty cycle"""
        with self.thread_lock:
            self.current_duty = duty_cycle
    
    def _wait_for_switch_change(self):
        initial_state = self.get_switch_state()
        start_time = time.time()
        while time.time() - start_time <= self.MAX_WAIT_TIME:
            if self.get_switch_state() != initial_state:
                break

    def _stop_servo(self):
        """Stop sending PWM signals to reduce jitter"""
        with self.thread_lock:
            self.current_duty = 0
            lgpio.tx_pwm(self.handle, self.servo_pin, 0, 0)
    
    def toggle(self):
        if self.get_switch_state():
            self.to_white()
        else:
            self.to_black()

    def cleanup(self):
        """Clean up resources including the PWM thread"""
        self.running = False
        if self.pwm_thread and self.pwm_thread.is_alive():
            self.pwm_thread.join(1.0)  # Wait up to 1 second for thread to finish
        lgpio.tx_pwm(self.handle, self.servo_pin, 0, 0)
        lgpio.gpiochip_close(self.handle)

if __name__ == "__main__":
    rocker = Rocker()
    rocker.reset()
    try:
        while True:
            input("Press Enter to toggle...")
            rocker.toggle()
    except KeyboardInterrupt:
        pass
    finally:
        rocker.cleanup()




