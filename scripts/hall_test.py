import time
from hall import SenseLayer

def scan_full(layer):
    board = layer.get_squares()
    print("Full Board Scan:")
    for row in board:
        print(" ".join(str(val) for val in row))

def scan_square(layer, square):
    result = layer.get_square_from_notation(square)
    if result is False:
        print(f"Invalid square notation: {square}")
    else:
        print(f"{square}: {result}")

def main():
    layer = SenseLayer()
    layer.begin()

    while True:
        cmd = input("Enter command ([full] for full scan, [single] for single square, [exit] to quit): ").strip().lower()
        if cmd == "full":
            scan_full(layer)
        elif cmd == "single":
            square = input("Enter square notation (e.g., a1, b5): ").strip().lower()
            scan_square(layer, square)
        elif cmd in ["exit", "quit", "q"]:
            print("Exiting.")
            break
        else:
            print("Unknown command. Please try again.")

if __name__ == "__main__":
    main()
```  

This loop will keep prompting until the user types "exit", "quit", or "q".