import subprocess
import time

def main():
    # @ryan: change this path when implementing into app
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
            print(output + "\n")
        except subprocess.CalledProcessError as e:
            print("Error running the binary:", e)
        except Exception as exc:
            print("Unexpected error:", exc)

if __name__ == '__main__':
    main()