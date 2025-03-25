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
        scan_full(layer)
        

if __name__ == "__main__":
    main()