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
    

def main():
    # Get user input for duty cycle
    user_input = input("Enter duty cycle (0 to 100%): ")
    try:
        duty_cycle = float(user_input)
    except ValueError:
        print("Invalid input. Please enter a numeric value for the duty cycle.")
        sys.exit(1)
    # Convert the duty cycle to a pulse width in microseconds
    pulse_width = duty_cycle_to_pulsewidth(duty_cycle, MIN_PULSEWIDTH, MAX_PULSEWIDTH)
    print(f"Setting servo to a pulse width of {pulse_width:.2f} µs based on {duty_cycle}% duty cycle.")
    
    # Set the servo pulse width
    pi.set_servo_pulsewidth(SERVO_GPIO_PIN, pulse_width)


if __name__ == "__main__":
    while(1):
        main()
