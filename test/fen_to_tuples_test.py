def square_to_coord(square):
            """
            Converts a chess square string (e.g. "e2") to coordinates (x, y)
            in half‐step units using the following system:
            - h1 is (0,0)
            - x increases as rank increases (rank 1 → 0, rank 8 → 14)
            - y increases as file goes from h to a (h → 0, a → 14)
            This yields a difference of 2 between adjacent squares so that there are
            intermediate half‐steps between them.
            """
            file = square[0].lower()
            try:
                rank = int(square[1])
            except ValueError:
                raise ValueError("Invalid square: rank must be a number")
            x = (rank - 1) * 2   # Multiply by 2 to represent half-steps
            y = (ord('h') - ord(file)) * 2
            return (x*25, y*25)

def fen_to_coords(fen):
    # Extract board setup from the FEN string
    board_part = fen.split()[0]
    ranks = board_part.split("/")  # Split into ranks

    pieces = []
    
    for rank_idx, rank in enumerate(reversed(ranks)):  # Reverse so rank 1 is at the bottom
        file_idx = 0
        for char in rank:
            if char.isdigit():
                file_idx += int(char)  # Skip empty squares
            else:
                square = f"{chr(ord('a') + file_idx)}{rank_idx + 1}"
                coord = square_to_coord(square)
                pieces.append((char, coord))
                file_idx += 1  # Move to the next file

    return pieces

# Test Cases
def test_fen_to_squares():
    test_fens = {
        "Starting Position": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "Few Pieces": "8/8/8/3k4/8/4Q3/8/8 w - - 0 1",
        "Empty Board": "8/8/8/8/8/8/8/8 w - - 0 1"
    }

    for name, fen in test_fens.items():
        print(f"\nTest: {name}")
        result = fen_to_coords(fen)
        print(result)

# Run Tests
if __name__ == "__main__":
    test_fen_to_squares()
