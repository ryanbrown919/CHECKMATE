import math

# Set the y-offset (in mm); all y values will be increased by this value.
NFC_OFFSET = 10  # Adjust this offset as needed

# Static 8x8 mapping from chess square labels to physical (x, y) coordinates.
# Assumption: A1 is at (0, 0), each square is 50 mm apart, and the y coordinate is offset by NFC_OFFSET.
BOARD_TO_PHYSICAL = {
    "A1": (0, 0 + NFC_OFFSET),    "B1": (50, 0 + NFC_OFFSET),    "C1": (100, 0 + NFC_OFFSET),   "D1": (150, 0 + NFC_OFFSET),
    "E1": (200, 0 + NFC_OFFSET),   "F1": (250, 0 + NFC_OFFSET),   "G1": (300, 0 + NFC_OFFSET),   "H1": (350, 0 + NFC_OFFSET),

    "A2": (0, 50 + NFC_OFFSET),   "B2": (50, 50 + NFC_OFFSET),   "C2": (100, 50 + NFC_OFFSET),  "D2": (150, 50 + NFC_OFFSET),
    "E2": (200, 50 + NFC_OFFSET),  "F2": (250, 50 + NFC_OFFSET),  "G2": (300, 50 + NFC_OFFSET),  "H2": (350, 50 + NFC_OFFSET),

    "A3": (0, 100 + NFC_OFFSET),  "B3": (50, 100 + NFC_OFFSET),  "C3": (100, 100 + NFC_OFFSET), "D3": (150, 100 + NFC_OFFSET),
    "E3": (200, 100 + NFC_OFFSET), "F3": (250, 100 + NFC_OFFSET), "G3": (300, 100 + NFC_OFFSET), "H3": (350, 100 + NFC_OFFSET),

    "A4": (0, 150 + NFC_OFFSET),  "B4": (50, 150 + NFC_OFFSET),  "C4": (100, 150 + NFC_OFFSET), "D4": (150, 150 + NFC_OFFSET),
    "E4": (200, 150 + NFC_OFFSET), "F4": (250, 150 + NFC_OFFSET), "G4": (300, 150 + NFC_OFFSET), "H4": (350, 150 + NFC_OFFSET),

    "A5": (0, 200 + NFC_OFFSET),  "B5": (50, 200 + NFC_OFFSET),  "C5": (100, 200 + NFC_OFFSET), "D5": (150, 200 + NFC_OFFSET),
    "E5": (200, 200 + NFC_OFFSET), "F5": (250, 200 + NFC_OFFSET), "G5": (300, 200 + NFC_OFFSET), "H5": (350, 200 + NFC_OFFSET),

    "A6": (0, 250 + NFC_OFFSET),  "B6": (50, 250 + NFC_OFFSET),  "C6": (100, 250 + NFC_OFFSET), "D6": (150, 250 + NFC_OFFSET),
    "E6": (200, 250 + NFC_OFFSET), "F6": (250, 250 + NFC_OFFSET), "G6": (300, 250 + NFC_OFFSET), "H6": (350, 250 + NFC_OFFSET),

    "A7": (0, 300 + NFC_OFFSET),  "B7": (50, 300 + NFC_OFFSET),  "C7": (100, 300 + NFC_OFFSET), "D7": (150, 300 + NFC_OFFSET),
    "E7": (200, 300 + NFC_OFFSET), "F7": (250, 300 + NFC_OFFSET), "G7": (300, 300 + NFC_OFFSET), "H7": (350, 300 + NFC_OFFSET),

    "A8": (0, 350 + NFC_OFFSET),  "B8": (50, 350 + NFC_OFFSET),  "C8": (100, 350 + NFC_OFFSET), "D8": (150, 350 + NFC_OFFSET),
    "E8": (200, 350 + NFC_OFFSET), "F8": (250, 350 + NFC_OFFSET), "G8": (300, 350 + NFC_OFFSET), "H8": (350, 350 + NFC_OFFSET)
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

def coord_to_chess_square(coord):
    """
    Convert board coordinate (x, y) into a chess square label.
    Assumption: Board coordinate (0,0) corresponds to A1 and (7,7) corresponds to H8.
    """
    x, y = coord
    # Files: A through H; Ranks: 1 through 8.
    return chr(ord('A') + x) + str(y + 1)

if __name__ == "__main__":
    # Example 8x8 board: 1 indicates an occupied square (magnet); 0 indicates an empty square.
    board = [
        [0, 0, 0, 0, 1, 0, 0, 0], # 8
        [0, 1, 0, 0, 0, 0, 1, 0], # 7
        [0, 0, 1, 0, 0, 1, 0, 0], # 6
        [0, 0, 0, 0, 0, 0, 0, 1], # 5
        [0, 0, 1, 0, 1, 0, 0, 0], # 4
        [0, 1, 0, 1, 0, 0, 1, 0], # 3
        [1, 0, 0, 0, 0, 1, 0, 0], # 2
        [0, 0, 0, 0, 0, 0, 0, 0]  # 1
       # A  B  C  D  E  F  G  H
    ]

    # Toolhead's starting position (board coordinate).
    start = (7, 7)

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
