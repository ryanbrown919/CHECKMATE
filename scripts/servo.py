import pigpio
import sys

# Configuration
SERVO_GPIO_PIN = 17  # Change this to the GPIO pin you are using for the servo
MIN_PULSEWIDTH = 500   # Minimum pulse width in microseconds (adjust for your servo)
MAX_PULSEWIDTH = 2500  # Maximum pulse width in microseconds (adjust for your servo)

pi = pigpio.pi()

def duty_cycle_to_pulsewidth(duty_cycle, min_pw, max_pw):
    """
    Map a duty cycle (0-100%) to a pulse width between min_pw and max_pw.
    """
    if not (0 <= duty_cycle <= 100):
        raise ValueError("Duty cycle must be between 0 and 100.")
    # Linear mapping from duty cycle to pulse width
    return min_pw + (duty_cycle / 100.0) * (max_pw - min_pw)
    
def home():
    pulse_width = duty_cycle_to_pulsewidth(50, MIN_PULSEWIDTH, MAX_PULSEWIDTH)
    pi.set_servo_pulsewidth(SERVO_GPIO_PIN, pulse_width)

def open():
    pulse_width = duty_cycle_to_pulsewidth(61, MIN_PULSEWIDTH, MAX_PULSEWIDTH)
    pi.set_servo_pulsewidth(SERVO_GPIO_PIN, pulse_width)

def close():
    pulse_width = duty_cycle_to_pulsewidth(39, MIN_PULSEWIDTH, MAX_PULSEWIDTH)
    pi.set_servo_pulsewidth(SERVO_GPIO_PIN, pulse_width)

def main():
    # Get user input for duty cycle
    user_input = input("Enter home, open, or close: ").strip().lower()
    if user_input == "home" or user_input == "h":
        home()
    elif user_input == "open" or user_input == "o":
        open()
    elif user_input == "close" or user_input == "c":
        close()
    else:
        print("Invalid input. Please enter 'home', 'open', or 'close'.")
    
if __name__ == "__main__":
    while(1):
        main()
