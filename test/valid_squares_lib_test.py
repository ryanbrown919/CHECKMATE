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

def symbol_to_vaild_coodinates():
    valid_gantry_coords = {
        'R': [square_to_coord(f'{file}1') for file in 'ah'],  # White Rook
        'N': [square_to_coord(f'{file}1') for file in 'bg'],  # White Knight
        'B': [square_to_coord(f'{file}1') for file in 'cf'],  # White Bishop
        'Q': [square_to_coord('d1')],  # White Queen
        'K': [square_to_coord('e1')],  # White King
        'P': [square_to_coord(f'{file}2') for file in 'abcdefgh'],  # White Pawn
        'r': [square_to_coord(f'{file}8') for file in 'ah'],  # Black Rook
        'n': [square_to_coord(f'{file}8') for file in 'bg'],  # Black Knight
        'b': [square_to_coord(f'{file}8') for file in 'cf'],  # Black Bishop
        'q': [square_to_coord('d8')],  # Black Queen
        'k': [square_to_coord('e8')],  # Black King
        'p': [square_to_coord(f'{file}7') for file in 'abcdefgh']  # Black Pawn
    }
    return valid_gantry_coords

def test_chess_positions():
    chess_positions = symbol_to_vaild_coodinates()
    print("Testing chess piece positions:")
    for piece, squares in chess_positions.items():
        print(f"{piece}: {squares}")

if __name__ == "__main__":
    test_chess_positions()