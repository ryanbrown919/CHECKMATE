import time
import argparse
from hall import SenseLayer

def setup(layer):
    layer.begin()

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
    parser = argparse.ArgumentParser(
        description="Hall Sensor Board Scan Utility"
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")
    
    # Sub-command: full board scan
    full_parser = subparsers.add_parser("full", help="Perform a full board scan.")
    
    # Sub-command: single square read
    single_parser = subparsers.add_parser("single", help="Read a single coordinate from square notation.")
    single_parser.add_argument("square", type=str, help="Square notation (e.g., a1, b5)")
    
    args = parser.parse_args()
    
    layer = SenseLayer()
    setup(layer)
    
    if args.command == "full":
        scan_full(layer)
    elif args.command == "single":
        scan_square(layer, args.square)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()