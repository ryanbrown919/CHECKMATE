def get_chess_positions():
    chess_positions = {
        'R': [f'{file}1' for file in 'ah'],  # White Rook
        'N': [f'{file}1' for file in 'bg'],  # White Knight
        'B': [f'{file}1' for file in 'cf'],  # White Bishop
        'Q': ['d1'],  # White Queen
        'K': ['e1'],  # White King
        'P': [f'{file}2' for file in 'abcdefgh'],  # White Pawn
        'r': [f'{file}8' for file in 'ah'],  # Black Rook
        'n': [f'{file}8' for file in 'bg'],  # Black Knight
        'b': [f'{file}8' for file in 'cf'],  # Black Bishop
        'q': ['d8'],  # Black Queen
        'k': ['e8'],  # Black King
        'p': [f'{file}7' for file in 'abcdefgh']  # Black Pawn
    }
    return chess_positions

def test_chess_positions():
    chess_positions = get_chess_positions()
    print("Testing chess piece positions:")
    for piece, squares in chess_positions.items():
        print(f"{piece}: {squares}")

if __name__ == "__main__":
    test_chess_positions()