import subprocess
import time

def main():
    # Adjust the path to your binary as necessary. For example, if your binary is built in the hall/build directory:
    binary_path = "../bin/hall_firmware.bin"
    
    while True:
        try:
            result = subprocess.run(
                [binary_path],
                capture_output=True,
                text=True,
                check=True,
                executable=binary_path
            )
            output = result.stdout.strip()
            print("C binary output:")
            print(output)
        except subprocess.CalledProcessError as e:
            print("Error running the binary:", e)
        except Exception as exc:
            print("Unexpected error:", exc)
        
        # Delay between runs (1 second)
        time.sleep(0.01)

if __name__ == '__main__':
    main()