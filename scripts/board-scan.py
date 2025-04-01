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
# Physical coordinates for each square (in mm)
SQUARE_COORDINATES = [
    # Format: (x, y) for each square
    # Each entry represents a square on the 8x8 board
    # Row 0 (A1-H1)
    (0, 0 + NFC_OFFSET),     (50, 0 + NFC_OFFSET),   (100, 0 + NFC_OFFSET),   (150, 0 + NFC_OFFSET),
    (200, 0 + NFC_OFFSET),   (250, 0 + NFC_OFFSET),  (300, 0 + NFC_OFFSET),   (350, 0 + NFC_OFFSET),
    
    # Row 1 (A2-H2)
    (0, 50 + NFC_OFFSET),    (50, 50 + NFC_OFFSET),  (100, 50 + NFC_OFFSET),  (150, 50 + NFC_OFFSET),
    (200, 50 + NFC_OFFSET),  (250, 50 + NFC_OFFSET), (300, 50 + NFC_OFFSET),  (350, 50 + NFC_OFFSET),
    
    # Row 2 (A3-H3)
    (0, 100 + NFC_OFFSET),   (50, 100 + NFC_OFFSET), (100, 100 + NFC_OFFSET), (150, 100 + NFC_OFFSET),
    (200, 100 + NFC_OFFSET), (250, 100 + NFC_OFFSET),(300, 100 + NFC_OFFSET), (350, 100 + NFC_OFFSET),
    
    # Row 3 (A4-H4)
    (0, 150 + NFC_OFFSET),   (50, 150 + NFC_OFFSET), (100, 150 + NFC_OFFSET), (150, 150 + NFC_OFFSET),
    (200, 150 + NFC_OFFSET), (250, 150 + NFC_OFFSET),(300, 150 + NFC_OFFSET), (350, 150 + NFC_OFFSET),
    
    # Row 4 (A5-H5)
    (0, 200 + NFC_OFFSET),   (50, 200 + NFC_OFFSET), (100, 200 + NFC_OFFSET), (150, 200 + NFC_OFFSET),
    (200, 200 + NFC_OFFSET), (250, 200 + NFC_OFFSET),(300, 200 + NFC_OFFSET), (350, 200 + NFC_OFFSET),
    
    # Row 5 (A6-H6)
    (0, 250 + NFC_OFFSET),   (50, 250 + NFC_OFFSET), (100, 250 + NFC_OFFSET), (150, 250 + NFC_OFFSET),
    (200, 250 + NFC_OFFSET), (250, 250 + NFC_OFFSET),(300, 250 + NFC_OFFSET), (350, 250 + NFC_OFFSET),
    
    # Row 6 (A7-H7)
    (0, 300 + NFC_OFFSET),   (50, 300 + NFC_OFFSET), (100, 300 + NFC_OFFSET), (150, 300 + NFC_OFFSET),
    (200, 300 + NFC_OFFSET), (250, 300 + NFC_OFFSET),(300, 300 + NFC_OFFSET), (350, 300 + NFC_OFFSET),
    
    # Row 7 (A8-H8)
    (0, 350 + NFC_OFFSET),   (50, 350 + NFC_OFFSET), (100, 350 + NFC_OFFSET), (150, 350 + NFC_OFFSET),
    (200, 350 + NFC_OFFSET), (250, 350 + NFC_OFFSET),(300, 350 + NFC_OFFSET), (350, 350 + NFC_OFFSET)
]

# Utility functions
def distance(point1, point2):
    """Calculate Manhattan distance between two points."""
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
    Return a list of physical coordinates for occupied squares on the board.
    board_state: 2D array with 1 for occupied squares, 0 for empty
    """
    occupied = []
    for y in range(len(board_state)):
        for x in range(len(board_state[y])):
            if board_state[y][x] == 1:
                # Convert board position to index in SQUARE_COORDINATES
                index = y * 8 + x
                if index < len(SQUARE_COORDINATES):
                    occupied.append(SQUARE_COORDINATES[index])
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
    Returns a dictionary mapping coordinates to piece identifiers.
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
    for i, coords in enumerate(path[1:]):  # Skip start point
        x, y = coords
        print(f"  {i+1}. Coordinates ({x}, {y})")
    
    # Ask user to confirm before executing
    input("\nPress Enter to execute scan sequence...")
    
    # Execute the scan path
    results = {}
    for i, coords in enumerate(path[1:]):  # Skip start point
        x, y = coords
        print(f"Scanning position {i+1}/{len(path)-1}...")
        
        # Move gantry to the position and wait until it arrives
        print(f"  Moving to coordinates: ({x}, {y})")
        gantry.move(x, y, blocking=True)
        
        # Read the piece with NFC
        piece_info = f"piece_{i}"  # Placeholder for NFC read
        results[coords] = piece_info
        print(f"  → Position ({x}, {y}): {piece_info}")
        
        # Brief pause to ensure stability
        time.sleep(0.5)
    
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
                for coords, piece in scan_results.items():
                    print(f"Position {coords}: {piece}")
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




