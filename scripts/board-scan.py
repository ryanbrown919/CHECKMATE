"""
Chess Board Scanner
------------------
Scans a chess board using a gantry system and NFC reader to identify pieces.
"""

import math
import time

from gantry import Gantry
from hall import SenseLayer
# from nfc import NFC

NFC_OFFSET = 42
BOARD_TO_PHYSICAL = {
    # Organized by ranks for better readability
    # Rank 1
    "A1": (0, 350 + NFC_OFFSET), "B1": (0, 300 + NFC_OFFSET), 
    "C1": (0, 250 + NFC_OFFSET), "D1": (0, 200 + NFC_OFFSET),
    "E1": (0, 150 + NFC_OFFSET), "F1": (0, 100 + NFC_OFFSET), 
    "G1": (0, 50 + NFC_OFFSET),  "H1": (0, 0 + NFC_OFFSET),
    
    # Rank 2
    "A2": (50, 350 + NFC_OFFSET), "B2": (50, 300 + NFC_OFFSET), 
    "C2": (50, 250 + NFC_OFFSET), "D2": (50, 200 + NFC_OFFSET),
    "E2": (50, 150 + NFC_OFFSET), "F2": (50, 100 + NFC_OFFSET), 
    "G2": (50, 50 + NFC_OFFSET),  "H2": (50, 0 + NFC_OFFSET),
    
    # Rank 3
    "A3": (100, 350 + NFC_OFFSET), "B3": (100, 300 + NFC_OFFSET),
    "C3": (100, 250 + NFC_OFFSET), "D3": (100, 200 + NFC_OFFSET),
    "E3": (100, 150 + NFC_OFFSET), "F3": (100, 100 + NFC_OFFSET),
    "G3": (100, 50 + NFC_OFFSET),  "H3": (100, 0 + NFC_OFFSET),
    
    # Rank 4
    "A4": (150, 350 + NFC_OFFSET), "B4": (150, 300 + NFC_OFFSET),
    "C4": (150, 250 + NFC_OFFSET), "D4": (150, 200 + NFC_OFFSET),
    "E4": (150, 150 + NFC_OFFSET), "F4": (150, 100 + NFC_OFFSET),
    "G4": (150, 50 + NFC_OFFSET),  "H4": (150, 0 + NFC_OFFSET),
    
    # Rank 5
    "A5": (200, 350 + NFC_OFFSET), "B5": (200, 300 + NFC_OFFSET),
    "C5": (200, 250 + NFC_OFFSET), "D5": (200, 200 + NFC_OFFSET),
    "E5": (200, 150 + NFC_OFFSET), "F5": (200, 100 + NFC_OFFSET),
    "G5": (200, 50 + NFC_OFFSET),  "H5": (200, 0 + NFC_OFFSET),
    
    # Rank 6
    "A6": (250, 350 + NFC_OFFSET), "B6": (250, 300 + NFC_OFFSET),
    "C6": (250, 250 + NFC_OFFSET), "D6": (250, 200 + NFC_OFFSET),
    "E6": (250, 150 + NFC_OFFSET), "F6": (250, 100 + NFC_OFFSET),
    "G6": (250, 50 + NFC_OFFSET),  "H6": (250, 0 + NFC_OFFSET),
    
    # Rank 7
    "A7": (300, 350 + NFC_OFFSET), "B7": (300, 300 + NFC_OFFSET),
    "C7": (300, 250 + NFC_OFFSET), "D7": (300, 200 + NFC_OFFSET),
    "E7": (300, 150 + NFC_OFFSET), "F7": (300, 100 + NFC_OFFSET),
    "G7": (300, 50 + NFC_OFFSET),  "H7": (300, 0 + NFC_OFFSET),
    
    # Rank 8
    "A8": (350, 350 + NFC_OFFSET), "B8": (350, 300 + NFC_OFFSET),
    "C8": (350, 250 + NFC_OFFSET), "D8": (350, 200 + NFC_OFFSET),
    "E8": (350, 150 + NFC_OFFSET), "F8": (350, 100 + NFC_OFFSET),
    "G8": (350, 50 + NFC_OFFSET),  "H8": (350, 0 + NFC_OFFSET),
}

# Utility functions
def distance(point1, point2):
    """Calculate Manhattan distance between two board coordinates."""
    return abs(point1[0] - point2[0]) + abs(point1[1] - point2[1])

def coord_to_chess_square(coord):
    """
    Convert board coordinate (x, y) into a chess square label.
    x=0, y=0 corresponds to A1 (bottom-left of board)
    """
    x, y = coord
    file = chr(ord('A') + x)  # A→B→C→...→H as x increases
    rank = str(y + 1)         # 1→2→3→...→8 as y increases
    return file + rank

def get_occupied_squares(board_state):
    """
    Return a list of (x, y) coordinates for occupied squares on the board.
    board_state: 2D array with 1 for occupied squares, 0 for empty
    """
    occupied = []
    for y in range(len(board_state)):
        for x in range(len(board_state[y])):
            if board_state[y][x] == 1:
                occupied.append((x, y))
    return occupied

def nearest_neighbor(start_point, targets):
    """
    Compute an efficient path starting at start_point and visiting all target points.
    Uses nearest neighbor algorithm (greedy approach).
    """
    unvisited = targets.copy()
    path = [start_point]
    current = start_point

    while unvisited:
        nearest = min(unvisited, key=lambda x: distance(current, x))
        path.append(nearest)
        unvisited.remove(nearest)
        current = nearest

    return path

def scan_board(gantry, layer):
    """
    Scan the chess board using Hall sensors and read pieces with NFC.
    Returns a dictionary mapping square names to piece identifiers.
    """
    print("Starting board scan...")
    
    # Get board state from hall sensors
    board = layer.get_squares()

    # Use current position as start point for path planning
    current_x, current_y = gantry.get_position()
    start_point = (current_x, current_y)

    # Find occupied squares and plan an efficient path
    occupied_squares = get_occupied_squares(board)
    path = nearest_neighbor(start_point, occupied_squares)

    print(f"Found {len(occupied_squares)} occupied squares")
    print("Planning scan path...")
    
    # Display the full planned path
    print("\nPlanned scan sequence:")
    planned_moves = []
    for i, square_coord in enumerate(path[1:]):  # Skip start point
        square_name = coord_to_chess_square(square_coord)
        if square_name in BOARD_TO_PHYSICAL:
            x, y = BOARD_TO_PHYSICAL[square_name]
            planned_moves.append(f"{i+1}. {square_name} at coordinates ({x}, {y})")
        else:
            planned_moves.append(f"{i+1}. {square_name} - NO PHYSICAL COORDINATES")
    
    for move in planned_moves:
        print(f"  {move}")
    
    # Ask user to confirm before executing
    input("\nPress Enter to execute scan sequence...")
    
    # Execute the scan path
    results = {}
    for i, square_coord in enumerate(path[1:]):  # Skip start point
        square_name = coord_to_chess_square(square_coord)
        print(f"Scanning square {square_name} ({i+1}/{len(path)-1})...")
        
        # Get physical coordinates from mapping
        if square_name in BOARD_TO_PHYSICAL:
            x, y = BOARD_TO_PHYSICAL[square_name]
            
            # Move gantry to the square and wait until it arrives
            print(f"  Moving to coordinates: ({x}, {y})")
            gantry.move(x, y, blocking=True)
            
            # Read the piece with NFC
            piece_info = square_name  # Placeholder for NFC read
            results[square_name] = piece_info
            print(f"  → {square_name}: {piece_info}")
            
            # Brief pause to ensure stability
            time.sleep(0.5)
        else:
            print(f"  Warning: No physical coordinates for {square_name}")
    
    print("Board scan complete!")
    return results

def main():
    """Main program execution."""
    
    # Create hardware objects
    sense_layer = SenseLayer()
    gantry = Gantry()
    # nfc_reader = NFC()
    
    gantry.home()
    # nfc_begin()
    
    try:
        while True:
            input("\nPress Enter to scan the board...")
            
            try:
                scan_results = scan_board(gantry, sense_layer)
                print("\nScan Results:")
                for square, piece in scan_results.items():
                    print(f"{square}: {piece}")
            except Exception as e:
                print(f"Error during scan: {e}")
                
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
    finally:
        # Clean up hardware resources
        print("Cleaning up...")
        try:
            gantry.home()  # Return to home position
            # Add any other cleanup needed
        except Exception as e:
            print(f"Error during cleanup: {e}")

if __name__ == "__main__":
    main()




