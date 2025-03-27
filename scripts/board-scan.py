import math
from gantry import Gantry
from nfc import NFC
import time

gantry = Gantry()
nfc = NFC()

NFC_OFFSET = 50  
BOARD_TO_PHYSICAL = {
    # Rank 1 (x = 0)
    "H1": (0, 0   + NFC_OFFSET), "G1": (0, 50  + NFC_OFFSET), "F1": (0, 100 + NFC_OFFSET), "E1": (0, 150 + NFC_OFFSET),
    "D1": (0, 200 + NFC_OFFSET), "C1": (0, 250 + NFC_OFFSET), "B1": (0, 300 + NFC_OFFSET), "A1": (0, 350 + NFC_OFFSET),

    # Rank 2 (x = 50)
    "H2": (50, 0   + NFC_OFFSET), "G2": (50, 50  + NFC_OFFSET), "F2": (50, 100 + NFC_OFFSET), "E2": (50, 150 + NFC_OFFSET),
    "D2": (50, 200 + NFC_OFFSET), "C2": (50, 250 + NFC_OFFSET), "B2": (50, 300 + NFC_OFFSET), "A2": (50, 350 + NFC_OFFSET),

    # Rank 3 (x = 100)
    "H3": (100, 0   + NFC_OFFSET), "G3": (100, 50  + NFC_OFFSET), "F3": (100, 100 + NFC_OFFSET), "E3": (100, 150 + NFC_OFFSET),
    "D3": (100, 200 + NFC_OFFSET), "C3": (100, 250 + NFC_OFFSET), "B3": (100, 300 + NFC_OFFSET), "A3": (100, 350 + NFC_OFFSET),

    # Rank 4 (x = 150)
    "H4": (150, 0   + NFC_OFFSET), "G4": (150, 50  + NFC_OFFSET), "F4": (150, 100 + NFC_OFFSET), "E4": (150, 150 + NFC_OFFSET),
    "D4": (150, 200 + NFC_OFFSET), "C4": (150, 250 + NFC_OFFSET), "B4": (150, 300 + NFC_OFFSET), "A4": (150, 350 + NFC_OFFSET),

    # Rank 5 (x = 200)
    "H5": (200, 0   + NFC_OFFSET), "G5": (200, 50  + NFC_OFFSET), "F5": (200, 100 + NFC_OFFSET), "E5": (200, 150 + NFC_OFFSET),
    "D5": (200, 200 + NFC_OFFSET), "C5": (200, 250 + NFC_OFFSET), "B5": (200, 300 + NFC_OFFSET), "A5": (200, 350 + NFC_OFFSET),

    # Rank 6 (x = 250)
    "H6": (250, 0   + NFC_OFFSET), "G6": (250, 50  + NFC_OFFSET), "F6": (250, 100 + NFC_OFFSET), "E6": (250, 150 + NFC_OFFSET),
    "D6": (250, 200 + NFC_OFFSET), "C6": (250, 250 + NFC_OFFSET), "B6": (250, 300 + NFC_OFFSET), "A6": (250, 350 + NFC_OFFSET),

    # Rank 7 (x = 300)
    "H7": (300, 0   + NFC_OFFSET), "G7": (300, 50  + NFC_OFFSET), "F7": (300, 100 + NFC_OFFSET), "E7": (300, 150 + NFC_OFFSET),
    "D7": (300, 200 + NFC_OFFSET), "C7": (300, 250 + NFC_OFFSET), "B7": (300, 300 + NFC_OFFSET), "A7": (300, 350 + NFC_OFFSET),

    # Rank 8 (x = 350)
    "H8": (350, 0   + NFC_OFFSET), "G8": (350, 50  + NFC_OFFSET), "F8": (350, 100 + NFC_OFFSET), "E8": (350, 150 + NFC_OFFSET),
    "D8": (350, 200 + NFC_OFFSET), "C8": (350, 250 + NFC_OFFSET), "B8": (350, 300 + NFC_OFFSET), "A8": (350, 350 + NFC_OFFSET),
}

def distance(x, y):
    """Calculate the Manhattan distance between two board coordinates."""
    return abs(x[0] - y[0]) + abs(x[1] - y[1])

def get_occupied_squares(board):
    """
    Return a list of (x, y) coordinates for occupied squares on the board.
    Board coordinates are given as (file index, rank index), where 0 <= index <= 7.
    """
    occupied = []
    for y in range(len(board)):
        for x in range(len(board[y])):
            if board[y][x] == 1:
                occupied.append((x, y))
    return occupied

def nearest_neighbor(start, targets):
    """
    Compute the nearest neighbor path starting at 'start' through all target squares.
    Returns a list of board coordinates representing the visiting order.
    """
    unvisited = targets[:]
    path = [start]
    current = start

    while unvisited:
        nearest = min(unvisited, key=lambda x: distance(current, x))
        path.append(nearest)
        unvisited.remove(nearest)
        current = nearest

    return path


def setup():
    nfc.begin()
    time.sleep(2)
    gantry.home()

def coord_to_chess_square(coord):
    """
    Convert board coordinate (x, y) into a chess square label.
    Assumption: Board row 0 is rank 8 and row 7 is rank 1.
    """
    x, y = coord
    file = chr(ord('A') + x)
    rank = str(8 - y)
    return file + rank

def main():
    board = [
        [1, 1, 1, 1, 1, 1, 1, 1], # 8
        [1, 1, 1, 1, 1, 1, 1, 1], # 7
        [0, 0, 0, 0, 0, 0, 0, 0], # 6
        [0, 0, 0, 0, 0, 0, 0, 0], # 5
        [0, 0, 0, 0, 0, 0, 0, 0], # 4
        [0, 0, 0, 0, 0, 0, 0, 0], # 3
        [1, 1, 1, 1, 1, 1, 1, 1], # 2
        [1, 1, 1, 1, 1, 1, 1, 1]  # 1
       # A  B  C  D  E  F  G  H
    ]
    # Toolhead's starting position (board coordinate).
    start = (7, 0)

    # Get the occupied squares and compute the nearest neighbor path.
    occupied_squares = get_occupied_squares(board)
    path = nearest_neighbor(start, occupied_squares)

    # Map board coordinates to chess square labels.
    chess_path = {coord: coord_to_chess_square(coord) for coord in path}
    # Map chess square labels to physical (x, y) coordinates using the static mapping.
    physical_mapping = {square: BOARD_TO_PHYSICAL[square] for square in chess_path.values()}

    print("Nearest Neighbor Path (board coordinates):")
    print(path)
    print("\nMapping to Chess Squares:")
    print(chess_path)
    print("\nChess Squares to Physical Coordinates:")
    print(physical_mapping)

    for square in path:
        gantry.move_to_square(coord_to_chess_square(square))
        piece = nfc.read()
        print(f"Read piece: {piece}")
        time.sleep(1)

if __name__ == "__main__":
    setup()
    while(True):
        input("Press Enter to scan the board")
        main()


    
        
