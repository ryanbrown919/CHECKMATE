def clamp(value, minimum, maximum):
    """Clamp the value between minimum and maximum."""
    return max(minimum, min(value, maximum))

def safe_rank(x):
    """
    Returns a safe intermediate x coordinate (for rank movement)
    ensuring that x is between 25 and 325.
    """
    return clamp(x, 25, 325)

def safe_file(y, center):
    """
    Returns a safe intermediate y coordinate (for file movement).
    For most files, y is clamped between 25 and 325.
    However, if the square’s center is at 350 (file a), then 350 is allowed.
    """
    if center == 350:
        return clamp(y, 25, 350)
    else:
        return clamp(y, 25, 325)

def generate_path(start, dest, offset=25):
    """
    Generates an L-shaped, collision-free path from start to dest.
    
    Coordinate system:
      - x: rank coordinate (0 at rank 1 up to 350 at rank 8)
      - y: file coordinate (0 at file h up to 350 at file a)
      
    Returns a list where:
      - The first element is the absolute starting coordinate.
      - Each subsequent element is a relative move (delta_x, delta_y)
        representing the movement from the previous waypoint.
    """
    start_x, start_y = start
    dest_x, dest_y = dest

    # Horizontal (file) movement: adjust the y coordinate.
    if dest_y > start_y:
        # Moving in the positive y direction (toward file a)
        start_safe_y = safe_file(start_y + offset, start_y)
        dest_safe_y = safe_file(dest_y - offset, dest_y)
    else:
        # Moving in the negative y direction (toward file h)
        start_safe_y = safe_file(start_y - offset, start_y)
        dest_safe_y = safe_file(dest_y + offset, dest_y)

    # Vertical (rank) movement: adjust the x coordinate.
    if dest_x > start_x:
        # Moving upward (from rank 1 to rank 8)
        start_safe_x = safe_rank(start_x + offset)
        dest_safe_x = safe_rank(dest_x - offset)
    else:
        # Moving downward (from a higher rank to a lower rank)
        start_safe_x = safe_rank(start_x - offset)
        dest_safe_x = safe_rank(dest_x + offset)

    # Define waypoints:
    # P0: Starting center.
    # P1: Horizontal move: adjust y to safe file coordinate, keep x constant.
    # P2: Vertical move: adjust x to destination safe rank, keep y from P1.
    # P3: Horizontal move: adjust y to destination safe file coordinate.
    # P4: Final move: absolute destination.
    P0 = (start_x, start_y)
    P1 = (start_x, start_safe_y)
    P2 = (dest_safe_x, start_safe_y)
    P3 = (dest_safe_x, dest_safe_y)
    P4 = (dest_x, dest_y)

    waypoints = [P0, P1, P2, P3, P4]

    # Convert waypoints to relative moves.
    relative_moves = []
    for i in range(1, len(waypoints)):
        prev = waypoints[i - 1]
        curr = waypoints[i]
        delta = (curr[0] - prev[0], curr[1] - prev[1])
        relative_moves.append(delta)

    # Return a list with the absolute starting coordinate followed by the relative moves.
    return [P0] + relative_moves

def parse_fen(fen):
    """
    Parses a FEN string and returns a dictionary mapping board squares (e.g., "e4")
    to piece characters (e.g., "P", "n", etc.).
    
    FEN rows are processed from rank 8 to rank 1.
    """
    board = {}
    fen_rows = fen.split()[0].split('/')
    for i, row in enumerate(fen_rows):
        rank = 8 - i  # ranks 8 to 1
        file_index = 0
        for ch in row:
            if ch.isdigit():
                file_index += int(ch)
            else:
                file_letter = chr(ord('a') + file_index)
                square = file_letter + str(rank)
                board[square] = ch
                file_index += 1
    return board

def square_to_coords(square):
    """
    Converts a board square (e.g., "h1" or "a8") to physical coordinates.
    
    Coordinate system:
      - x: rank coordinate, with rank 1 at x = 0 and rank 8 at x = 350.
      - y: file coordinate, with file h at y = 0 and file a at y = 350.
    
    For example:
      "h1" -> (0, 0)
      "a8" -> (350, 350)
    """
    file_letter = square[0]
    rank_digit = int(square[1])
    x = (rank_digit - 1) * 50
    file_index = ord(file_letter) - ord('a')
    y = (7 - file_index) * 50
    return (x, y)

def select_target_square(piece, candidates, occupancy):
    """
    Given a piece and a list of candidate target squares, returns the first candidate
    that is not yet occupied.
    """
    for candidate in candidates:
        if occupancy.get(candidate) is None:
            return candidate
    return None

# Define alternative placements for pieces that might have more than one acceptable target.
# (These can be applied if needed; keys are current squares and values are lists of alternate squares.)
piece_alternatives = {
    # White pieces alternatives (for demonstration)
    "a1": ["h1"],
    "h1": ["a1"],
    "b1": ["g1"],
    "g1": ["b1"],
    "c1": ["f1"],
    "f1": ["c1"],
    # Pawns: allow adjacent files on the same rank.
    "a2": ["b2"],
    "b2": ["a2", "c2"],
    "c2": ["b2", "d2"],
    "d2": ["c2", "e2"],
    "e2": ["d2", "f2"],
    "f2": ["e2", "g2"],
    "g2": ["f2", "h2"],
    "h2": ["g2"],
    # Black pieces alternatives (for demonstration)
    "a8": ["h8"],
    "h8": ["a8"],
    "b8": ["g8"],
    "g8": ["b8"],
    "c8": ["f8"],
    "f8": ["c8"],
    "a7": ["b7"],
    "b7": ["a7", "c7"],
    "c7": ["b7", "d7"],
    "d7": ["c7", "e7"],
    "e7": ["d7", "f7"],
    "f7": ["e7", "g7"],
    "g7": ["f7", "h7"],
    "h7": ["g7"]
}

def plan_board_reset(current_fen, target_fen, piece_alternatives):
    """
    Plans moves to reset the board from a current configuration to a target configuration.
    
    Instead of assuming pieces remain on the same square, this version matches pieces by type.
    It builds a list of candidate target squares (from the target configuration) for each piece type
    and assigns a target to each piece that is not already in a square that has the correct piece.
    
    Returns a dictionary mapping the current square (for pieces that need to move) to a move plan.
    Each move plan includes:
      - "piece": the piece character
      - "final_square": the target square
      - "path": a list starting with the absolute starting coordinate followed by relative moves.
    """
    current_mapping = parse_fen(current_fen)
    target_mapping = parse_fen(target_fen)
    
    # Build a dictionary: piece letter -> list of squares from target configuration.
    target_positions = {}
    for square, piece in target_mapping.items():
        target_positions.setdefault(piece, []).append(square)
    
    # Occupancy for target squares (initially all free)
    target_occupancy = {square: None for square in target_mapping.keys()}
    
    move_paths = {}
    
    # For each piece in the current configuration:
    # If the piece is not already in a square that has the correct piece in the target configuration,
    # assign a target square from the candidate list.
    for square, piece in current_mapping.items():
        # Check if the piece is already in a correct square.
        if square in target_mapping and target_mapping[square] == piece:
            # Already correct; skip moving it.
            continue
        
        # Get candidate target squares for this piece type.
        candidates = target_positions.get(piece, [])
        
        # Remove any candidate that is the same as the current square (or that is already occupied).
        candidates = [sq for sq in candidates if sq != square and target_occupancy.get(sq) is None]
        
        # Optionally add alternatives from the piece_alternatives dictionary.
        if square in piece_alternatives:
            candidates.extend(piece_alternatives[square])
        
        # Select the first available candidate.
        chosen = select_target_square(piece, candidates, target_occupancy)
        if chosen is None:
            print(f"No available target square for {piece} from {square}")
            continue
        
        # Mark the chosen square as occupied.
        target_occupancy[chosen] = piece
        
        # Convert current square and chosen target square into physical coordinates.
        start_coords = square_to_coords(square)
        dest_coords = square_to_coords(chosen)
        
        # Generate the movement path.
        path = generate_path(start_coords, dest_coords, offset=25)
        
        move_paths[square] = {
            "piece": piece,
            "final_square": chosen,
            "path": path
        }
    
    return move_paths

# Example usage:
if __name__ == "__main__":
    # Provided current configuration FEN:
    current_fen = "4r3/8/2kPnK2/8/8/2QpNq2/8/4R3"
    # Target configuration FEN: swap the white queen and white rook.
    target_fen  = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
    
    moves = plan_board_reset(current_fen, target_fen, piece_alternatives)
    
    for start_square, info in moves.items():
        print(f"Move {info['piece']} from {start_square} to {info['final_square']} via path:")
        print(info["path"])



# def clamp(value, minimum, maximum):
#     """Clamp the value between minimum and maximum."""
#     return max(minimum, min(value, maximum))

# def safe_rank(x):
#     """
#     Returns a safe intermediate x coordinate (for rank movement)
#     ensuring that x is between 25 and 325.
#     """
#     return clamp(x, 25, 325)

# def safe_file(y, center):
#     """
#     Returns a safe intermediate y coordinate (for file movement).
#     For most files, y is clamped between 25 and 325.
#     However, if the square’s center is at 350 (file a), then 350 is allowed.
#     """
#     if center == 350:
#         return clamp(y, 25, 350)
#     else:
#         return clamp(y, 25, 325)

# def generate_path(start, dest, offset=25):
#     """
#     Generates an L-shaped, collision-free path from start to dest.
    
#     Coordinate system:
#       - x: rank coordinate (0 at rank 1 up to 350 at rank 8)
#       - y: file coordinate (0 at file h up to 350 at file a)
      
#     Returns a list where:
#       - The first element is the absolute starting coordinate.
#       - Each subsequent element is a relative move (delta_x, delta_y)
#         representing the movement from the previous waypoint.
#     """
#     start_x, start_y = start
#     dest_x, dest_y = dest

#     # Horizontal (file) movement: adjust the y coordinate.
#     if dest_y > start_y:
#         # Moving in the positive y direction (toward file a)
#         start_safe_y = safe_file(start_y + offset, start_y)
#         dest_safe_y = safe_file(dest_y - offset, dest_y)
#     else:
#         # Moving in the negative y direction (toward file h)
#         start_safe_y = safe_file(start_y - offset, start_y)
#         dest_safe_y = safe_file(dest_y + offset, dest_y)

#     # Vertical (rank) movement: adjust the x coordinate.
#     if dest_x > start_x:
#         # Moving upward (from rank 1 to rank 8)
#         start_safe_x = safe_rank(start_x + offset)
#         dest_safe_x = safe_rank(dest_x - offset)
#     else:
#         # Moving downward (from a higher rank to a lower rank)
#         start_safe_x = safe_rank(start_x - offset)
#         dest_safe_x = safe_rank(dest_x + offset)

#     # Define waypoints:
#     # P0: Starting center.
#     # P1: Horizontal move: adjust y to safe file coordinate, keep x constant.
#     # P2: Vertical move: adjust x to destination safe rank, keep y from P1.
#     # P3: Horizontal move: adjust y to destination safe file coordinate.
#     # P4: Final move: absolute destination.
#     P0 = (start_x, start_y)
#     P1 = (start_x, start_safe_y)
#     P2 = (dest_safe_x, start_safe_y)
#     P3 = (dest_safe_x, dest_safe_y)
#     P4 = (dest_x, dest_y)

#     waypoints = [P0, P1, P2, P3, P4]

#     # Convert waypoints to relative moves.
#     relative_moves = []
#     for i in range(1, len(waypoints)):
#         prev = waypoints[i - 1]
#         curr = waypoints[i]
#         delta = (curr[0] - prev[0], curr[1] - prev[1])
#         relative_moves.append(delta)

#     # Return a list with the absolute starting coordinate followed by the relative moves.
#     return [P0] + relative_moves

# def parse_fen(fen):
#     """
#     Parses a FEN string and returns a dictionary mapping board squares (e.g., "e4")
#     to piece characters (e.g., "P", "n", etc.).
    
#     FEN rows are processed from rank 8 to rank 1.
#     """
#     board = {}
#     # The FEN part before the first space represents piece placement.
#     fen_rows = fen.split()[0].split('/')
#     # FEN rows go from rank 8 (first row) to rank 1 (last row)
#     for i, row in enumerate(fen_rows):
#         rank = 8 - i  # rank number (8 down to 1)
#         file_index = 0
#         for ch in row:
#             if ch.isdigit():
#                 # Skip empty squares.
#                 file_index += int(ch)
#             else:
#                 # Files in FEN are labeled from 'a' to 'h'
#                 file_letter = chr(ord('a') + file_index)
#                 square = file_letter + str(rank)
#                 board[square] = ch
#                 file_index += 1
#     return board

# def square_to_coords(square):
#     """
#     Converts a board square (e.g., "h1" or "a8") to physical coordinates.
    
#     Coordinate system:
#       - x: rank coordinate, with rank 1 at x = 0 and rank 8 at x = 350.
#       - y: file coordinate, with file h at y = 0 and file a at y = 350.
    
#     For example:
#       "h1" -> (0, 0)
#       "a8" -> (350, 350)
#     """
#     # Extract file and rank from the square string.
#     file_letter = square[0]
#     rank_digit = int(square[1])
#     # x coordinate: (rank - 1) * 50 (so rank 1 is 0 and rank 8 is 350)
#     x = (rank_digit - 1) * 50
#     # y coordinate: files go from a to h, but y increases from file h to file a.
#     # Compute index with 'a' as 0, then reverse: y = (7 - index) * 50.
#     file_index = ord(file_letter) - ord('a')
#     y = (7 - file_index) * 50
#     return (x, y)

# def select_target_square(piece, desired_square, occupancy, alternative_squares=None):
#     """
#     Given a piece and its desired target square, this function checks if the square is empty.
#     For pieces that have multiple acceptable target squares, an alternative list can be provided.
    
#     Parameters:
#       piece: the piece character (e.g., 'P' for pawn)
#       desired_square: the primary target square (e.g., "e2")
#       occupancy: a dictionary mapping squares to the occupying piece (or None if empty)
#       alternative_squares: a list of alternative square names (if applicable)
    
#     Returns:
#       The selected target square (string).
    
#     Raises:
#       Exception if no acceptable square is available.
#     """
#     if occupancy.get(desired_square) is None:
#         return desired_square
#     elif alternative_squares:
#         for alt in alternative_squares:
#             if occupancy.get(alt) is None:
#                 return alt
#     raise Exception(f"No available target square for {piece} from {desired_square}")

# # Define a dictionary of alternative placements for pieces that have multiple acceptable target squares.
# # (Based on the standard starting position)
# piece_alternatives = {
#     # White pieces:
#     # Rooks: alternate between a1 and h1.
#     "a1": ["h1"],
#     "h1": ["a1"],
#     # Knights: alternate between b1 and g1.
#     "b1": ["g1"],
#     "g1": ["b1"],
#     # Bishops: alternate between c1 and f1.
#     "c1": ["f1"],
#     "f1": ["c1"],
#     # King and Queen have only one target square.
#     "d1": [],
#     "e1": [],
#     # Pawns: each pawn can try adjacent files on the same rank.
#     "a2": ["b2"],
#     "b2": ["a2", "c2"],
#     "c2": ["b2", "d2"],
#     "d2": ["c2", "e2"],
#     "e2": ["d2", "f2"],
#     "f2": ["e2", "g2"],
#     "g2": ["f2", "h2"],
#     "h2": ["g2"],
    
#     # Black pieces:
#     # Rooks: alternate between a8 and h8.
#     "a8": ["h8"],
#     "h8": ["a8"],
#     # Knights: alternate between b8 and g8.
#     "b8": ["g8"],
#     "g8": ["b8"],
#     # Bishops: alternate between c8 and f8.
#     "c8": ["f8"],
#     "f8": ["c8"],
#     # King and Queen:
#     "d8": [],
#     "e8": [],
#     # Pawns:
#     "a7": ["b7"],
#     "b7": ["a7", "c7"],
#     "c7": ["b7", "d7"],
#     "d7": ["c7", "e7"],
#     "e7": ["d7", "f7"],
#     "f7": ["e7", "g7"],
#     "g7": ["f7", "h7"],
#     "h7": ["g7"]
# }

# def plan_board_reset(current_fen, target_fen, piece_alternatives):
#     """
#     Plans the moves required to reset the board.
    
#     Parameters:
#       current_fen: FEN string representing the current board state.
#       target_fen: FEN string representing the desired final board configuration.
#       piece_alternatives: a dictionary mapping starting squares (e.g., "e2") to lists of alternative
#                           target squares for pieces with multiple acceptable placements.
    
#     Returns:
#       A dictionary mapping each piece's starting square to its move plan, which includes:
#          - piece: the piece character
#          - final_square: the target square
#          - path: a list where the first element is the absolute starting coordinate and
#                  subsequent elements are relative moves (delta_x, delta_y).
#     """
#     current_mapping = parse_fen(current_fen)  # e.g., {"e2": "P", "e7": "p", ...}
#     target_mapping = parse_fen(target_fen)      # e.g., final positions for each piece
    
#     # Build an occupancy dictionary for the target squares (all start empty).
#     target_occupancy = {square: None for square in target_mapping.keys()}
    
#     move_paths = {}
    
#     # For every piece on the current board:
#     for square, piece in current_mapping.items():
#         # Only consider pieces that should remain on the board.
#         if square in target_mapping:
#             desired_square = square  # In this example, the desired square is taken as the same.
#         else:
#             # Skip captured pieces.
#             continue

#         # If the piece has alternatives (applies to pieces with multiple acceptable placements),
#         # use them.
#         if square in piece_alternatives and piece_alternatives[square]:
#             alternatives = piece_alternatives[square]
#             try:
#                 final_square = select_target_square(piece, desired_square, target_occupancy, alternatives)
#             except Exception as e:
#                 print(e)
#                 continue
#         else:
#             try:
#                 final_square = select_target_square(piece, desired_square, target_occupancy)
#             except Exception as e:
#                 print(e)
#                 continue

#         # Mark the target square as occupied.
#         target_occupancy[final_square] = piece

#         # Convert squares to physical coordinates.
#         start_coords = square_to_coords(square)
#         dest_coords  = square_to_coords(final_square)

#         if not start_coords == dest_coords:

#             # Generate a collision-free movement path.
#             path = generate_path(start_coords, dest_coords, offset=25)
            
#             move_paths[square] = {
#                 "piece": piece,
#                 "final_square": final_square,
#                 "path": path
#             }
    
#     return move_paths

# # Example usage:
# if __name__ == "__main__":
#     # Use the standard starting position for both current and target configurations.
#     current_fen = "4r3/8/2kPnK2/8/8/2QpNq2/8/4R3"
#     target_fen  = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
    
#     move_paths = plan_board_reset(current_fen, target_fen, piece_alternatives)
    
#     for start_square, info in move_paths.items():
#         print(f"Move {info['piece']} from {start_square} to {info['final_square']} via path:")
#         # The first element is the absolute start, followed by relative moves.
#         print(info["path"])




# # def clamp(value, minimum, maximum):
# #     """Clamp the value between minimum and maximum."""
# #     return max(minimum, min(value, maximum))

# # def safe_rank(x):
# #     """
# #     Returns a safe intermediate x coordinate (for rank movement)
# #     ensuring that x is between 25 and 325.
# #     """
# #     return clamp(x, 25, 325)

# # def safe_file(y, center):
# #     """
# #     Returns a safe intermediate y coordinate (for file movement).
# #     For most files, y is clamped between 25 and 325.
# #     However, if the square’s center is at 350 (file a), then 350 is allowed.
# #     """
# #     if center == 350:
# #         return clamp(y, 25, 350)
# #     else:
# #         return clamp(y, 25, 325)

# # def generate_path(start, dest, offset=25):
# #     """
# #     Generates an L-shaped, collision-free path from start to dest.
    
# #     Coordinates:
# #       - x: rank direction (0 at rank 1 up to 350 at rank 8)
# #       - y: file direction (0 at file h up to 350 at file a)
    
# #     The function returns a list where:
# #       - The first element is the absolute starting coordinate.
# #       - Each subsequent element is a relative move (delta_x, delta_y)
# #         representing the movement from the previous waypoint.
# #     """
# #     start_x, start_y = start
# #     dest_x, dest_y = dest

# #     # Horizontal (file) movement: adjust the y coordinate.
# #     if dest_y > start_y:
# #         # Moving in the positive y direction (toward file a)
# #         start_safe_y = safe_file(start_y + offset, start_y)
# #         dest_safe_y = safe_file(dest_y - offset, dest_y)
# #     else:
# #         # Moving in the negative y direction (toward file h)
# #         start_safe_y = safe_file(start_y - offset, start_y)
# #         dest_safe_y = safe_file(dest_y + offset, dest_y)

# #     # Vertical (rank) movement: adjust the x coordinate.
# #     if dest_x > start_x:
# #         # Moving upward (from rank 1 to rank 8)
# #         start_safe_x = safe_rank(start_x + offset)
# #         dest_safe_x = safe_rank(dest_x - offset)
# #     else:
# #         # Moving downward (from a higher rank to a lower rank)
# #         start_safe_x = safe_rank(start_x - offset)
# #         dest_safe_x = safe_rank(dest_x + offset)

# #     # Define waypoints:
# #     # P0: Starting center.
# #     # P1: Horizontal move: adjust y to safe file coordinate, keep x constant.
# #     # P2: Vertical move: adjust x to destination safe rank, keep y from P1.
# #     # P3: Horizontal move: adjust y to destination safe file coordinate.
# #     # P4: Final move: absolute destination.
# #     P0 = (start_x, start_y)
# #     P1 = (start_x, start_safe_y)
# #     P2 = (dest_safe_x, start_safe_y)
# #     P3 = (dest_safe_x, dest_safe_y)
# #     P4 = (dest_x, dest_y)

# #     waypoints = [P0, P1, P2, P3, P4]

# #     # Convert waypoints to relative moves.
# #     relative_moves = []
# #     for i in range(1, len(waypoints)):
# #         prev = waypoints[i - 1]
# #         curr = waypoints[i]
# #         delta = (curr[0] - prev[0], curr[1] - prev[1])
# #         relative_moves.append(delta)

# #     # Return a list with the absolute starting coordinate followed by the relative moves.
# #     return [P0] + relative_moves

# # def parse_fen(fen):
# #     """
# #     Parses a FEN string and returns a dictionary mapping board squares (e.g., "e4")
# #     to piece characters (e.g., "P", "n", etc.).
    
# #     FEN rows are processed from rank 8 to rank 1.
# #     """
# #     board = {}
# #     # The FEN part before the first space represents piece placement.
# #     fen_rows = fen.split()[0].split('/')
# #     # FEN rows go from rank 8 (first row) to rank 1 (last row)
# #     for i, row in enumerate(fen_rows):
# #         rank = 8 - i  # rank number (8 down to 1)
# #         file_index = 0
# #         for ch in row:
# #             if ch.isdigit():
# #                 # Skip empty squares.
# #                 file_index += int(ch)
# #             else:
# #                 # Files in FEN are labeled from 'a' to 'h'
# #                 file_letter = chr(ord('a') + file_index)
# #                 square = file_letter + str(rank)
# #                 board[square] = ch
# #                 file_index += 1
# #     return board

# # def square_to_coords(square):
# #     """
# #     Converts a board square (e.g., "h1" or "a8") to physical coordinates.
    
# #     Coordinate system:
# #       - x: rank coordinate, with rank 1 at x = 0 and rank 8 at x = 350.
# #       - y: file coordinate, with file h at y = 0 and file a at y = 350.
    
# #     For example:
# #       "h1" -> (0, 0)
# #       "a8" -> (350, 350)
# #     """
# #     # Extract file and rank from the square string.
# #     file_letter = square[0]
# #     rank_digit = int(square[1])
# #     # For x: (rank - 1) * 50 (since rank 1 should be 0, rank 8 should be 350)
# #     x = (rank_digit - 1) * 50
# #     # For y: files go from a to h but our coordinate system increases from file h to file a.
# #     # Compute index with 'a' as 0, then reverse: y = (7 - index) * 50.
# #     file_index = ord(file_letter) - ord('a')
# #     y = (7 - file_index) * 50
# #     return (x, y)

# # def select_target_square(piece, desired_square, occupancy, alternative_squares=None):
# #     """
# #     Given a piece and its desired target square, this function checks if the square is empty.
# #     For pieces like pawns that have multiple acceptable target squares, an alternative list can be provided.
    
# #     Parameters:
# #       piece: the piece character (e.g., 'P' for pawn)
# #       desired_square: the primary target square (e.g., "e2")
# #       occupancy: a dictionary mapping squares to the occupying piece (or None if empty)
# #       alternative_squares: a list of alternative square names (if applicable)
    
# #     Returns:
# #       The selected target square (string).
    
# #     Raises:
# #       Exception if no acceptable square is available.
# #     """
# #     if occupancy.get(desired_square) is None:
# #         return desired_square
# #     elif alternative_squares:
# #         for alt in alternative_squares:
# #             if occupancy.get(alt) is None:
# #                 return alt
# #     raise Exception(f"No available target square for {piece} from {desired_square}")

# # def plan_board_reset(current_fen, target_fen, pawn_alternatives):
# #     """
# #     Plans the moves required to reset the board.
    
# #     Parameters:
# #       current_fen: FEN string representing the current board state.
# #       target_fen: FEN string representing the desired final board configuration.
# #       pawn_alternatives: a dictionary mapping pawn starting squares to lists of alternative
# #                          target squares (if a pawn has multiple acceptable placements).
    
# #     Returns:
# #       A dictionary mapping each piece's starting square to its move plan, which includes:
# #          - piece: the piece character
# #          - final_square: the target square
# #          - path: a list where the first element is the absolute starting coordinate and
# #                  subsequent elements are relative moves (delta_x, delta_y).
# #     """
# #     current_mapping = parse_fen(current_fen)  # e.g., {"e2": "P", "e7": "p", ...}
# #     target_mapping = parse_fen(target_fen)      # e.g., final positions for each piece
    
# #     # Build an occupancy dictionary for the target squares (all start empty).
# #     target_occupancy = {square: None for square in target_mapping.keys()}
    
# #     move_paths = {}
    
# #     # For every piece on the current board:
# #     for square, piece in current_mapping.items():
# #         # Only consider pieces that should remain on the board.
# #         if square in target_mapping:
# #             desired_square = square  # In this simple example, desired square is the same.
# #         else:
# #             # Skip captured pieces.
# #             continue

# #         # For pawns, allow multiple potential targets.
# #         if piece.upper() == 'P':
# #             alternatives = pawn_alternatives.get(square, [])
# #             try:
# #                 final_square = select_target_square(piece, desired_square, target_occupancy, alternatives)
# #             except Exception as e:
# #                 print(e)
# #                 continue
# #         else:
# #             try:
# #                 final_square = select_target_square(piece, desired_square, target_occupancy)
# #             except Exception as e:
# #                 print(e)
# #                 continue

# #         # Mark the target square as occupied.
# #         target_occupancy[final_square] = piece

# #         # Convert squares to physical coordinates.
# #         start_coords = square_to_coords(square)
# #         dest_coords  = square_to_coords(final_square)

# #         if not start_coords == dest_coords:

# #             # Generate a collision-free movement path.
# #             path = generate_path(start_coords, dest_coords, offset=25)
        
# #             move_paths[square] = {
# #                 "piece": piece,
# #                 "final_square": final_square,
# #                 "path": path
# #             }
    
# #     return move_paths

# # # Example usage:
# # if __name__ == "__main__":
# #     # Use the standard starting position for both current and target configurations.
# #     current_fen = "4r3/8/2kPnK2/8/8/2QpNq2/8/4R3"
# #     target_fen  = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
    
# #     # For pawns, specify alternative acceptable target squares if needed.
# #     piece_alternatives = {
# #         # Example: For a pawn starting on "e2", acceptable targets might include "d2" or "f2".
# #         "e2": ["a2", "b2", "c2", "d2", "e2", "f2", "g2", "h2"],
# #         # Add additional pawn alternatives here if necessary.
# #     }
    
# #     move_paths = plan_board_reset(current_fen, target_fen, piece_alternatives)
    
# #     for start_square, info in move_paths.items():
# #         print(f"Move {info['piece']} from {start_square} to {info['final_square']} via path:")
# #         # The first element is the absolute start, followed by relative moves.
# #         print(info["path"])






# # # def clamp(value, minimum, maximum):
# # #     return max(minimum, min(value, maximum))

# # # def safe_rank(coordinate):
# # #     # For rank (x), always stay within 25 and 325.
# # #     return clamp(coordinate, 25, 325)

# # # def safe_file(coordinate, square_center_y):
# # #     # For file (y), normally use [25, 325].
# # #     # But if the square is on file a (center y == 350), allow 350.
# # #     if square_center_y == 350:
# # #         return clamp(coordinate, 25, 350)
# # #     else:
# # #         return clamp(coordinate, 25, 325)

# # # def generate_path(start, dest, offset=25):
# # #     """
# # #     start, dest: tuples (x, y) where:
# # #         x is the rank coordinate (0 at h1, 350 at rank8)
# # #         y is the file coordinate (0 at file h, 350 at file a)
    
# # #     Returns a list where:
# # #         - The first element is the absolute starting coordinate.
# # #         - Each subsequent element is a relative move (delta x, delta y)
# # #           to get to the next waypoint.
# # #     """
# # #     start_x, start_y = start
# # #     dest_x, dest_y = dest

# # #     # For horizontal moves, we adjust the file (y) coordinate.
# # #     if dest_y > start_y:
# # #         # Moving from a lower y (closer to file h) toward a higher y (closer to file a)
# # #         start_safe_y = safe_file(start_y + offset, start_y)
# # #         dest_safe_y  = safe_file(dest_y - offset, dest_y)
# # #     else:
# # #         start_safe_y = safe_file(start_y - offset, start_y)
# # #         dest_safe_y  = safe_file(dest_y + offset, dest_y)

# # #     # For vertical moves, we adjust the rank (x) coordinate.
# # #     if dest_x > start_x:
# # #         # Moving upward from rank 1 (x=0) toward rank 8 (x=350)
# # #         start_safe_x = safe_rank(start_x + offset)
# # #         dest_safe_x  = safe_rank(dest_x - offset)
# # #     else:
# # #         start_safe_x = safe_rank(start_x - offset)
# # #         dest_safe_x  = safe_rank(dest_x + offset)

# # #     # Construct waypoints:
# # #     # P0: Absolute start.
# # #     P0 = (start_x, start_y)
# # #     # P1: Horizontal move (file direction) from start to safe file.
# # #     P1 = (start_x, start_safe_y)
# # #     # P2: Vertical move (rank direction) to destination's safe rank, retaining safe file.
# # #     P2 = (dest_safe_x, start_safe_y)
# # #     # P3: Horizontal move to destination's safe file.
# # #     P3 = (dest_safe_x, dest_safe_y)
# # #     # P4: Final vertical move into destination center.
# # #     P4 = (dest_x, dest_y)

# # #     # List of waypoints.
# # #     waypoints = [P0, P1, P2, P3, P4]

# # #     # Convert waypoints into relative moves.
# # #     relative_moves = []
# # #     for i in range(1, len(waypoints)):
# # #         prev = waypoints[i - 1]
# # #         curr = waypoints[i]
# # #         # Each relative move is (delta_x, delta_y)
# # #         relative_moves.append((curr[0] - prev[0], curr[1] - prev[1]))

# # #     # Return a list where the first element is the absolute starting coordinate,
# # #     # followed by the sequence of relative moves.
# # #     return [P0] + relative_moves

# # # # Example usage:
# # # # Let's generate a path from h1 at (0,0) to a8 at (350,350) in your system.
# # # path = generate_path((0, 0), (350, 350))
# # # print("Path:", path)
