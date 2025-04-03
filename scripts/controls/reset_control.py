import math
import time


class BoardReset:
    def __init__(self, board, gantry, hall, captured_pieces):    
        self.gantry = gantry
        self.board = board
        self.hall = hall
        self.captured_pieces = captured_pieces

    def distance(self, x, y):
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

    def nearest_neighbor(self, start, targets):
        """
        Compute the nearest neighbor path starting at 'start' through all target squares.
        Returns a list of board coordinates representing the visiting order.
        """
        unvisited = targets[:]
        path = [start]
        current = start

        while unvisited:
            nearest = min(unvisited, key=lambda x: self.distance(current, x))
            path.append(nearest)
            unvisited.remove(nearest)
            current = nearest

        return path

    def square_to_coord(self, square):
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

    def coord_to_chess_square(self, coord):
        """
        Convert board coordinate (x, y) into a chess square label.
        Assumption: Board row 0 is rank 8 and row 7 is rank 1.
        """
        x, y = coord

        file = chr(ord('H') + x)
        rank = str(8 - y)
        return file + rank
    
    def symbol_to_valid_coodinates(self):
        valid_gantry_coords = {
            'R': [self.square_to_coord(f'{file}1') for file in 'ah'],  # White Rook
            'N': [self.square_to_coord(f'{file}1') for file in 'bg'],  # White Knight
            'B': [self.square_to_coord(f'{file}1') for file in 'cf'],  # White Bishop
            'Q': [self.square_to_coord('d1')],  # White Queen
            'K': [self.square_to_coord('e1')],  # White King
            'P': [self.square_to_coord(f'{file}2') for file in 'abcdefgh'],  # White Pawn
            'r': [self.square_to_coord(f'{file}8') for file in 'ah'],  # Black Rook
            'n': [self.square_to_coord(f'{file}8') for file in 'bg'],  # Black Knight
            'b': [self.square_to_coord(f'{file}8') for file in 'cf'],  # Black Bishop
            'q': [self.square_to_coord('d8')],  # Black Queen
            'k': [self.square_to_coord('e8')],  # Black King
            'p': [self.square_to_coord(f'{file}7') for file in 'abcdefgh']  # Black Pawn
        }
        return valid_gantry_coords
    
    def symbol_to_valid_coodinates(self, symbol):
        """
        Given a chess piece symbol, return the valid coordinates for that specific symbol.
        """
        valid_gantry_coords = {
            'R': [self.square_to_coord(f'{file}1') for file in 'ah'],  # White Rook
            'N': [self.square_to_coord(f'{file}1') for file in 'bg'],  # White Knight
            'B': [self.square_to_coord(f'{file}1') for file in 'cf'],  # White Bishop
            'Q': [self.square_to_coord('d1')],  # White Queen
            'K': [self.square_to_coord('e1')],  # White King
            'P': [self.square_to_coord(f'{file}2') for file in 'abcdefgh'],  # White Pawn
            'r': [self.square_to_coord(f'{file}8') for file in 'ah'],  # Black Rook
            'n': [self.square_to_coord(f'{file}8') for file in 'bg'],  # Black Knight
            'b': [self.square_to_coord(f'{file}8') for file in 'cf'],  # Black Bishop
            'q': [self.square_to_coord('d8')],  # Black Queen
            'k': [self.square_to_coord('e8')],  # Black King
            'p': [self.square_to_coord(f'{file}7') for file in 'abcdefgh']  # Black Pawn
        }
        return valid_gantry_coords.get(symbol, [])

    def reset_playing_area_white(self):
        """
        Reset all WHITE pieces NOT on ranks 1, 2 or in the deadzone.
        Assumes that the starting locations are either unoccupied or filled with the correct piece.
        """
        pieces = self.fen_to_coords("4r3/8/2kPnK2/8/8/2QpNq2/8/4Rb2")

        for piece in pieces:
            symbol, coords = piece
            x, y = coords

            # Only process pieces in the playable area (not in the deadzone)
            if x < 75 and y < 375:
                # Get valid starting coordinates for the piece type
                valid_coords = self.symbol_to_valid_coodinates(symbol)

                # Check which of those valid coordinates are already occupied
                occupied_coords = self.get_occupied_squares(self.control_system.board)
                unoccupied_coords = []
                for coord in valid_coords:
                    if coord not in occupied_coords:
                        unoccupied_coords.append(coord)

                if unoccupied_coords:
                    # Select the first unoccupied valid coordinate
                    # make this intelligent later...
                    target_coord = unoccupied_coords[0]

                    # Update the white_captured list with the new coordinates
                    self.gantry.white_captured.remove(piece) # add logic for duplicate pieces
                    self.gantry.white_captured.append((symbol, target_coord))

                    # Update the board state to reflect the move
                    old_rank, old_file = coords[1] // 50, coords[0] // 50
                    new_rank, new_file = target_coord[1] // 50, target_coord[0] // 50
                    self.board[old_rank][old_file] = 0  # Mark old square as empty
                    self.board[new_rank][new_file] = 1  # Mark new square as occupied

                    # Execute the movement using the gantry
                    print(f"Moving {symbol} from {coords} to {target_coord}")
                    path = [coords, target_coord]  # Simple direct path
                    movements = self.gantry.parse_path_to_movement(path)
                    commands = self.gantry.movement_to_gcode(movements)
                    self.gantry.send_commands(commands)

    def fen_to_coords(self,fen):
        """
        Given a fen string, output a list with the piece and its coordinates.
        Following the convention: (symbol, (x,y))
        """
        
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
                    coord = self.square_to_coord(square)
                    self.pieces.append((char, (coord[0]*25, coord[1]*25)))
                    file_idx += 1  # Move to the next file

        return pieces

        

      
        

    def reset_board_from_game(self):
        # Add logic here for dealign with resetting as well as deadzone pieces
        # DEAL WITH EXISITING FIRST 

        # Parse the FEN string to extract list of pieces and their coordinates
        board_state = self.fen_to_coords(self.control_system.board.fen())
    
        ## White captured and black captured are current coords of all pieces after end of game
        # Filter and append all pieces to self.gantry.white_captured or self.gantry.black_captured
        for piece in board_state:
            symbol, coords = piece  
            if symbol.isupper():  # White piece
                self.gantry.white_captured.append((symbol, coords))  
            elif symbol.islower(): # Black piece
                self.gantry.black_captured.append((symbol, coords))
                
        # Poll hall for empty squares and create an 8x8 matrix
        empty_squares = self.hall.sense_layer.get_squares_game()

        # Flip the y-axis to match chess notation (h1 as (0,0), a8 as (7,7))
        empty_squares = empty_squares[::-1]

        # Initialize white_restart_state with 16 slots
        # white_restart_state = [(0, (0, 0)) for _ in range(16)]

        ##moveblack piece out of white endzone    
        for piece in self.control_system.gantry.black_captured:
            symbol, coords = piece
            x, y = coords
            if x < 75 and y < 375:
                # move is contains initial and final cords of black piece
                ''' change empty squares to remove ranks 1 and 2 '''
                move = self.nearest_neighbor(coords, empty_squares) 
                vector_move = (move[1][0] - move[0][0], move[1][1] - move[0][1])
                path = [move[0], (0, 25), (vector_move-25, 0), (0, vector_move - 25), (25, 0)]

                # Update the black_captured list with the new coordinates
                self.gantry.black_captured.remove(piece) # me no likey
                self.gantry.black_captured.append((symbol, move[1]))

                # Update the empty_squares matrix
                old_rank, old_file = coords[1] // 50, coords[0] // 50  # Convert old coords to matrix indices
                new_rank, new_file = move[1][0] // 50, move [1][1] // 50  # Convert new coords to matrix indices
                empty_squares[old_rank][old_file] = 0  # Mark the old square as empty
                empty_squares[new_rank][new_file] = 1  # Mark the new square as occupied

                # Execute the movement using the gantry
                print(f"Moving black piece {symbol} from {coords} to {new_coords} via path: {path}")
                movements = self.gantry.parse_path_to_movement(path)
                commands = self.gantry.movement_to_gcode(movements)
                print(f"Last move: {commands}")
                self.gantry.send_commands(commands)

        for piece in self.gantry.white_captured:
            symbol, coords = piece
            x, y = coords
            if x < 75 and y < 375:
                reset_coords=self.symbol_to_valid_coordinates(symbol)
                
                # Filter out occupied coordinates from reset_coords
                unoccupied_reset_coords = []
                for coord in reset_coords:
                    is_occupied = False
                    for state in self.gantry.white_captured:
                        if state[1] == coord:  # Check if the coordinate is already in white_captured
                            is_occupied = True
                            break
                    if not is_occupied:  # If the coordinate is not occupied, add it to unoccupied_reset_coords
                        unoccupied_reset_coords.append(coord)

                #find which of the new_cords is closest                
                move = self.nearest_neighbor(coords, unoccupied_reset_coords)
                if move[0][0] < 25 :
                    path = [move[0], (25, 0), (0, move[1][1]), (move[1][0] - 25, 0)]
                else:
                    path = [move[0], (-25, 0), (0, move[1][1]), (move[1][0] + 25, 0)]
        
                # Update white_captured list with new coordinates of the piece just moved
                self.gantry.white_captured.remove(piece)  # Remove the old entry
                self.gantry.white_captured.append((symbol, move[1]))  # Add the updated entry with new coordinates

                # Update the empty_squares matrix
                old_rank, old_file = coords[1] // 50, coords[0] // 50  # Convert old coords to matrix indices
                new_rank, new_file = move[1][0] // 50, move [1][1] // 50  # Convert new coords to matrix indices
                empty_squares[old_rank][old_file] = 0  # Mark the old square as empty
                empty_squares[new_rank][new_file] = 1  # Mark the new square as occupied

                        
            print(f"arranging white in rank 1 & 2: {path}")
            movements = self.gantry.parse_path_to_movement(path)
            commands = self.gantry.movement_to_gcode(movements)
            print(f"Last move: {commands}")
            self.gantry.send_commands(commands)
            
                
    def full_reset(self):

    
        # piece_alternatives = {
        # # White pieces alternatives (for demonstration)
        # "a1": ["h1"],
        # "h1": ["a1"],
        # "b1": ["g1"],
        # "g1": ["b1"],
        # "c1": ["f1"],
        # "f1": ["c1"],
        # # Pawns: allow adjacent files on the same rank.
        # "a2": ["b2"],
        # "b2": ["a2", "c2"],
        # "c2": ["b2", "d2"],
        # "d2": ["c2", "e2"],
        # "e2": ["d2", "f2"],
        # "f2": ["e2", "g2"],
        # "g2": ["f2", "h2"],
        # "h2": ["g2"],
        # # Black pieces alternatives (for demonstration)
        # "a8": ["h8"],
        # "h8": ["a8"],
        # "b8": ["g8"],
        # "g8": ["b8"],
        # "c8": ["f8"],
        # "f8": ["c8"],
        # "a7": ["b7"],
        # "b7": ["a7", "c7"],
        # "c7": ["b7", "d7"],
        # "d7": ["c7", "e7"],
        # "e7": ["d7", "f7"],
        # "f7": ["e7", "g7"],
        # "g7": ["f7", "h7"],
        # "h7": ["g7"]
        # }

         # # Define alternatives for pieces that might have more than one acceptable target.
            # For non-pawn pieces (example for rooks, knights, bishops):
        piece_alternatives = {
            # White pieces alternatives
            "a1": ["h1"],
            "h1": ["a1"],
            "b1": ["g1"],
            "g1": ["b1"],
            "c1": ["f1"],
            "f1": ["c1"],
            # Black pieces alternatives
            "a8": ["h8"],
            "h8": ["a8"],
            "b8": ["g8"],
            "g8": ["b8"],
            "c8": ["f8"],
            "f8": ["c8"],
        }

        # Automatically fill out pawn alternatives for all possible pawn squares.
        white_pawn_squares = ["a2", "b2", "c2", "d2", "e2", "f2", "g2", "h2"]
        black_pawn_squares = ["a7", "b7", "c7", "d7", "e7", "f7", "g7", "h7"]

        for square in white_pawn_squares:
            piece_alternatives[square] = [s for s in white_pawn_squares if s != square]

        for square in black_pawn_squares:
            piece_alternatives[square] = [s for s in black_pawn_squares if s != square]

        current_fen = "r1bqnr2/1pp2kpQ/p1np1bB1/8/8/5N2/PB1P2PP/RN2R1K1"
        # Target configuration FEN: swap the white queen and white rook.
        target_fen  = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"

        moves = self.plan_board_reset(current_fen, target_fen, piece_alternatives)

        for start_square, info in moves.items():
            print(f"Move {info['piece']} from {start_square} to {info['final_square']} via path:")
            print(info["path"])

            cmds = self.gantry.path_to_gcode(info["path"])
            self.gantry.send_commands(cmds)


        # occupancy = self.occupancy_list_to_dict(self.hall.sense_layer.get_squares_game())

        white_recovery, black_recovery = self.plan_captured_piece_recovery(self.captured_pieces)

        for idx, info in white_recovery.items():
            print(f"Piece {info['piece']} from stored {info['start_coord']} to {info['final_square']}:")
            print(info["path"])

            cmds = self.gantry.path_to_gcode(info["path"])
            self.gantry.send_commands(cmds)

        for idx, info in black_recovery.items():
            print(f"Piece {info['piece']} from stored {info['start_coord']} to {info['final_square']}:")
            print(info["path"])

            cmds = self.gantry.path_to_gcode(info["path"])
            self.gantry.send_commands(cmds)


        # ''' Felipe's code '''
        # self.reset_board_from_game()
        # ''' Jack's code '''
        # self.reset_playing_area_white()
        # ''' Felipe's code '''
        # self.reset_board_from_game()

    

    def clamp(self, value, minimum, maximum):
        """Clamp the value between minimum and maximum."""
        return max(minimum, min(value, maximum))

    def safe_rank(self, x):
        """
        Returns a safe intermediate x coordinate (for rank movement)
        ensuring that x is between 25 and 325.
        """
        return self.clamp(x, 25, 325)

    def safe_file(self, y, center):
        """
        Returns a safe intermediate y coordinate (for file movement).
        For most files, y is clamped between 25 and 325.
        However, if the square’s center is at 350 (file a), then 350 is allowed.
        """
        if center == 350:
            return self.clamp(y, 25, 350)
        else:
            return self.clamp(y, 25, 325)

    def generate_path(self, start, dest, offset=25):
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
            start_safe_y = self.safe_file(start_y + offset, start_y)
            dest_safe_y = self.safe_file(dest_y - offset, dest_y)
        else:
            # Moving in the negative y direction (toward file h)
            start_safe_y = self.safe_file(start_y - offset, start_y)
            dest_safe_y = self.safe_file(dest_y + offset, dest_y)

        # Vertical (rank) movement: adjust the x coordinate.
        if dest_x > start_x:
            # Moving upward (from rank 1 to rank 8)
            start_safe_x = self.safe_rank(start_x + offset)
            dest_safe_x = self.safe_rank(dest_x - offset)
        else:
            # Moving downward (from a higher rank to a lower rank)
            start_safe_x = self.safe_rank(start_x - offset)
            dest_safe_x = self.safe_rank(dest_x + offset)

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

    def parse_fen(self, fen):
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

    def square_to_coords_ry(self, square):
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

    def select_target_square(self, piece, candidates, occupancy):
        """
        Given a piece and a list of candidate target squares, returns the first candidate
        that is not yet occupied.
        """
        for candidate in candidates:
            if occupancy.get(candidate) is None:
                return candidate
        return None

    # # Define alternatives for pieces that might have more than one acceptable target.
    # # For non-pawn pieces (example for rooks, knights, bishops):
    # piece_alternatives = {
    #     # White pieces alternatives
    #     "a1": ["h1"],
    #     "h1": ["a1"],
    #     "b1": ["g1"],
    #     "g1": ["b1"],
    #     "c1": ["f1"],
    #     "f1": ["c1"],
    #     # Black pieces alternatives
    #     "a8": ["h8"],
    #     "h8": ["a8"],
    #     "b8": ["g8"],
    #     "g8": ["b8"],
    #     "c8": ["f8"],
    #     "f8": ["c8"],
    # }

    # # Automatically fill out pawn alternatives for all possible pawn squares.
    # white_pawn_squares = ["a2", "b2", "c2", "d2", "e2", "f2", "g2", "h2"]
    # black_pawn_squares = ["a7", "b7", "c7", "d7", "e7", "f7", "g7", "h7"]

    # for square in white_pawn_squares:
    #     piece_alternatives[square] = [s for s in white_pawn_squares if s != square]

    # for square in black_pawn_squares:
    #     piece_alternatives[square] = [s for s in black_pawn_squares if s != square]

    # def plan_board_reset(self, current_fen, target_fen, piece_alternatives):
    #     """
    #     Plans moves to reset the board from a current configuration to a target configuration.
        
    #     This version matches pieces by type and processes the moves in two passes.
    #     In the first pass, all pieces except the king and queen are assigned target squares.
    #     In the second pass, the king and queen are processed last to minimize conflicts.
        
    #     Returns a dictionary mapping the current square (for pieces that need to move)
    #     to a move plan. Each move plan includes:
    #     - "piece": the piece character
    #     - "final_square": the target square
    #     - "path": a list starting with the absolute starting coordinate followed by relative moves.
    #     """
    #     current_mapping = self.parse_fen(current_fen)
    #     target_mapping = self.parse_fen(target_fen)
        
    #     # Build a dictionary: piece letter -> list of squares from target configuration.
    #     target_positions = {}
    #     for square, piece in target_mapping.items():
    #         target_positions.setdefault(piece, []).append(square)
        
    #     # Occupancy for target squares (initially all free)
    #     target_occupancy = {square: None for square in target_mapping.keys()}
        
    #     move_paths = {}

    #     # Split pieces into two groups: non-king/queen and king/queen.
    #     first_pass = {}
    #     second_pass = {}
    #     for square, piece in current_mapping.items():
    #         if piece.upper() in ('K', 'Q'):
    #             second_pass[square] = piece
    #         else:
    #             first_pass[square] = piece

    #     # Helper function to process a given mapping.
    #     def process_pieces(mapping):
    #         for square, piece in mapping.items():
    #             # Skip if already correctly placed.
    #             if square in target_mapping and target_mapping[square] == piece:
    #                 continue

    #             # Get candidate target squares for this piece type.
    #             candidates = target_positions.get(piece, [])
    #             # Remove candidates that are the same as the current square or already occupied.
    #             candidates = [sq for sq in candidates if sq != square and target_occupancy.get(sq) is None]
                
    #             # Add alternatives from the piece_alternatives dictionary if available.
    #             if square in piece_alternatives:
    #                 candidates.extend(piece_alternatives[square])
                
    #             chosen = self.select_target_square(piece, candidates, target_occupancy)
    #             if chosen is None:
    #                 print(f"No available target square for {piece} from {square}")
    #                 continue
                
    #             target_occupancy[chosen] = piece
                
    #             start_coords = self.square_to_coords_ry(square)
    #             dest_coords = self.square_to_coords_ry(chosen)
    #             path = self.generate_path(start_coords, dest_coords, offset=25)
                
    #             move_paths[square] = {
    #                 "piece": piece,
    #                 "final_square": chosen,
    #                 "path": path
    #             }
        
    #     # Process first all non-king/queen pieces.
    #     process_pieces(first_pass)
    #     # Then process the king and queen.
    #     process_pieces(second_pass)
        
    #     return move_paths

    # def occupancy_list_to_dict(occ_list):
    #     """
    #     Converts an 8x8 occupancy list into a dictionary mapping board squares
    #     (e.g., "a8", "b8", …, "h1") to occupancy values (1 for occupied, 0 for empty).
        
    #     Assumptions:
    #     - occ_list is a list of 8 lists.
    #     - The first inner list corresponds to rank 8,
    #         the second to rank 7, …, and the last to rank 1.
    #     - Within each inner list, the first element corresponds to file a,
    #         the second to file b, …, and the last to file h.
    #     """
    #     occ_dict = {}
    #     for i, row in enumerate(occ_list):
    #         rank = 8 - i  # first row is rank 8, last row is rank 1.
    #         for j, val in enumerate(row):
    #             file_letter = chr(ord('a') + j)
    #             square = file_letter + str(rank)
    #             occ_dict[square] = val
    #     return occ_dict

    def plan_board_reset(self, current_fen, target_fen, piece_alternatives):
        """
        Plans moves to reset the board from a current configuration to a target configuration,
        using an externally provided occupancy list for candidate selection.
        
        This version matches pieces by type and processes the moves in two passes.
        In the first pass, all pieces except the king and queen are assigned target squares.
        In the second pass, the king and queen are processed last to minimize conflicts.
        
        The occupancy is provided as an 8x8 list (each inner list representing a rank starting from file a),
        which is converted to a dictionary mapping squares to 0 (empty) or 1 (occupied).
        
        Returns a dictionary mapping the current square (for pieces that need to move)
        to a move plan. Each move plan includes:
        - "piece": the piece character
        - "final_square": the target square
        - "path": a list starting with the absolute starting coordinate followed by relative moves.
        """
        # Parse FEN strings.
        current_mapping = self.parse_fen(current_fen)
        target_mapping = self.parse_fen(target_fen)
        
        # Build a dictionary: piece letter -> list of squares from target configuration.
        target_positions = {}
        for square, piece in target_mapping.items():
            target_positions.setdefault(piece, []).append(square)
        
        # Convert the provided occupancy list into a dictionary.
        target_occupancy = self.occupancy_list_to_dict(self.hall.sense_layer.get_squares_game())
        # (target_occupancy now holds keys for all board squares with values 0 or 1.)
        
        move_paths = {}

        # Split pieces into two groups: non-king/queen and king/queen.
        first_pass = {}
        second_pass = {}
        for square, piece in current_mapping.items():
            if piece.upper() in ('K', 'Q'):
                second_pass[square] = piece
            else:
                first_pass[square] = piece

        def process_pieces(mapping):
            for square, piece in mapping.items():
                # Skip if already correctly placed.
                if square in target_mapping and target_mapping[square] == piece:
                    continue

                # Get candidate target squares for this piece type.
                candidates = target_positions.get(piece, [])
                # Remove candidates that are the same as the current square or already occupied.
                # Here, a square is available only if target_occupancy[sq] == 0.
                candidates = [sq for sq in candidates if sq != square and target_occupancy.get(sq, 0) == 0]
                
                # Add alternatives from the piece_alternatives dictionary if available.
                if square in piece_alternatives:
                    # Also filter alternatives by occupancy.
                    alt_candidates = [sq for sq in piece_alternatives[square] if target_occupancy.get(sq, 0) == 0]
                    candidates.extend(alt_candidates)
                
                chosen = self.select_target_square(piece, candidates, target_occupancy)
                if chosen is None:
                    print(f"No available target square for {piece} from {square}")
                    continue
                
                # Mark the chosen square as occupied (set to 1).
                target_occupancy[chosen] = 1
                
                start_coords = self.square_to_coords_ry(square)
                dest_coords = self.square_to_coords_ry(chosen)
                path = self.generate_path(start_coords, dest_coords, offset=25)
                
                move_paths[square] = {
                    "piece": piece,
                    "final_square": chosen,
                    "path": path
                }
        
        # Process non-king/queen pieces first.
        process_pieces(first_pass)
        # Then process the king and queen.
        process_pieces(second_pass)
        
        return move_paths
    


    def coords_to_square_ry(self, coord):
        """
        Converts physical coordinates (assumed to be board-center values in multiples of 50)
        to a board square (e.g., "e4"). 
        Assumes:
        - x (rank coordinate): 0 corresponds to rank 1, 350 to rank 8.
        - y (file coordinate): 0 corresponds to file h, 350 to file a.
        """
        x, y = coord
        rank = int(x / 50) + 1
        file_index = 7 - int(y / 50)
        file_letter = chr(ord('a') + file_index)
        return file_letter + str(rank)

    def recover_captured_piece_path(self, captured_coord, piece, occupancy):
        """
        Generates a movement path for a captured piece to re-enter the board.
        
        The plan is:
        1. From its stored coordinate (captured_coord), move so that its y becomes 375.
        2. Then move horizontally so that its x becomes 25 (for white pieces, uppercase)
            or 325 (for black pieces, lowercase) while keeping y = 375.
        3. Then slide vertically (in steps of -50 in y) until an unoccupied board square is found.
            (Board-square centers are at y = 350, 300, 250, ... down to 0.)
        
        The function returns a tuple (path, final_square), where:
        - path is a list in the format: [absolute start, relative move1, relative move2, relative move3].
        - final_square is the board square (e.g., "e4") where the piece will finally be placed.
        
        The occupancy dictionary maps board squares (like "e4") to a piece (or None if empty).
        """
        # Determine target x based on color.
        if piece.isupper():
            target_x = 25   # white pieces go to x = 25
        else:
            target_x = 325  # black pieces go to x = 325

        # Waypoint 1: Set y to 375 while keeping x the same.
        wp1 = (captured_coord[0], 375)
        # Waypoint 2: Move horizontally to target_x (keeping y = 375).
        wp2 = (target_x, 375)
        
        # Now, slide vertically downward (decreasing y) in 50-unit steps to find an empty square.
        candidate_y = 350  # start with the highest board square center
        final_coord = None
        final_square = None
        while candidate_y >= 0:
            candidate_coord = (target_x, candidate_y)
            square_candidate = self.coords_to_square(candidate_coord)
            if occupancy.get(square_candidate) is None:
                final_coord = candidate_coord
                final_square = square_candidate
                break
            candidate_y -= 50
        if final_coord is None:
            print("No available board square for captured piece", piece)
            return None, None

        # Now build the path.
        # The path will be a list where:
        #   - The first element is the absolute starting coordinate (captured_coord).
        #   - Each subsequent element is a relative move (delta_x, delta_y) from the previous waypoint.
        # Move 1: captured_coord -> wp1
        delta1 = (wp1[0] - captured_coord[0], wp1[1] - captured_coord[1])
        # Move 2: wp1 -> wp2
        delta2 = (wp2[0] - wp1[0], wp2[1] - wp1[1])
        # Move 3: wp2 -> final_coord
        delta3 = (final_coord[0] - wp2[0], final_coord[1] - wp2[1])
        
        path = [captured_coord, delta1, delta2, delta3]
        return path, final_square

    def plan_captured_piece_recovery(self, captured_pieces):
        """
        Processes a list of captured pieces and generates recovery move plans for each.
        
        The function first sorts the captured pieces into white and black based on the case of the symbol.
        It then assigns stored endzone coordinates from a fixed alternating pattern:
        
        For white pieces (stored off-board on the right):
            Pattern: (350,435), (350,410), (325,435), (325,410)
        For black pieces (stored off-board on the left):
            Pattern: (0,435), (0,410), (25,435), (25,410)
        
        For each captured piece, the function calls recover_captured_piece_path to generate a path.
        The path format is the same as before: first element is the absolute coordinate, then relative moves.
        
        Returns two dictionaries (one for white and one for black) mapping an index (or order)
        to the recovery plan. Each recovery plan includes:
        - "piece": the piece symbol,
        - "start_coord": the stored coordinate (in the endzone),
        - "final_square": the board square where it will be placed,
        - "path": the movement path.
        """
        # Define the stored coordinate patterns for white and black captured pieces.
        white_pattern = [(350, 435), (350, 410), (325, 435), (325, 410), (300, 435), (300, 410), (275, 435), (275, 410), (250, 435), (250, 410), (225, 435), (225, 410), (200, 435), (200, 410), (175, 435), (175, 410)]
        black_pattern = [(0, 435), (0, 410), (25, 435), (25, 410), (50, 435), (50, 410), (75, 435), (75, 410), (100, 435), (100, 410), (125, 435), (125, 410), (150, 435), (150, 410), (175, 435), (175, 410)]
        
        white_moves = {}
        black_moves = {}
        white_index = 0
        black_index = 0
        
        for i, piece in enumerate(captured_pieces):
            occupancy = self.occupancy_list_to_dict(self.hall.sense_layer.get_squares_game())
            if piece.isupper():
                stored_coord = white_pattern[white_index % len(white_pattern)]
                white_index += 1
                path, final_square = self.recover_captured_piece_path(stored_coord, piece, occupancy)
                white_moves[i] = {
                    "piece": piece,
                    "start_coord": stored_coord,
                    "final_square": final_square,
                    "path": path
                }
            else:
                stored_coord = black_pattern[black_index % len(black_pattern)]
                black_index += 1
                path, final_square = self.recover_captured_piece_path(stored_coord, piece, occupancy)
                black_moves[i] = {
                    "piece": piece,
                    "start_coord": stored_coord,
                    "final_square": final_square,
                    "path": path
                }
        
        return white_moves, black_moves
    
    def occupancy_list_to_dict(self, occ_list):
        """
        Converts an occupancy list (8 rows, each an 8-element list of 1s or 0s)
        into a dictionary mapping squares (like "a8", "b8", …, "h1") to occupancy.

        Assumptions:
        - occ_list is a list of 8 lists.
        - Each inner list represents a rank.
        - The first inner list corresponds to rank 8, the second to rank 7, ..., the last to rank 1.
        - Within each inner list, the first element corresponds to file a, the second to file b, ..., the last to file h.

        Returns:
        A dictionary with keys as square strings and values as occupancy (1 or 0).
        """
        occ_dict = {}
        for i, row in enumerate(occ_list):
            # Determine rank: first row is rank 8, second is rank 7, etc.
            rank = 8 - i  
            for j, val in enumerate(row):
                # File letters: j=0 -> a, j=1 -> b, ..., j=7 -> h.
                file_letter = chr(ord('a') + j)
                square = file_letter + str(rank)
                occ_dict[square] = val
        return occ_dict

                

        
######## Board recovery

#     def clamp(self, value, minimum, maximum):
#         """Clamp the value between minimum and maximum."""
#         return max(minimum, min(value, maximum))

#     def safe_rank(self, x):
#         """
#         Returns a safe intermediate x coordinate (for rank movement)
#         ensuring that x is between 25 and 325.
#         """
#         return self.clamp(x, 25, 325)

#     def safe_file(self, y, center):
#         """
#         Returns a safe intermediate y coordinate (for file movement).
#         For most files, y is clamped between 25 and 325.
#         However, if the square’s center is at 350 (file a), then 350 is allowed.
#         """
#         if center == 350:
#             return self.clamp(y, 25, 350)
#         else:
#             return self.clamp(y, 25, 325)

#     def generate_path(self, start, dest, offset=25):
#         """
#         Generates an L-shaped, collision-free path from start to dest.
        
#         Coordinate system:
#         - x: rank coordinate (0 at rank 1 up to 350 at rank 8)
#         - y: file coordinate (0 at file h up to 350 at file a)
        
#         Returns a list where:
#         - The first element is the absolute starting coordinate.
#         - Each subsequent element is a relative move (delta_x, delta_y).
#         """
#         start_x, start_y = start
#         dest_x, dest_y = dest

#         # Horizontal (file) movement: adjust the y coordinate.
#         if dest_y > start_y:
#             start_safe_y = self.safe_file(start_y + offset, start_y)
#             dest_safe_y = self.safe_file(dest_y - offset, dest_y)
#         else:
#             start_safe_y = self.safe_file(start_y - offset, start_y)
#             dest_safe_y = self.safe_file(dest_y + offset, dest_y)

#         # Vertical (rank) movement: adjust the x coordinate.
#         if dest_x > start_x:
#             start_safe_x = self.safe_rank(start_x + offset)
#             dest_safe_x = self.safe_rank(dest_x - offset)
#         else:
#             start_safe_x = self.safe_rank(start_x - offset)
#             dest_safe_x = self.safe_rank(dest_x + offset)

#         # Define waypoints:
#         # P0: Starting center.
#         # P1: Horizontal move to safe y coordinate.
#         # P2: Vertical move to destination safe x.
#         # P3: Horizontal move to destination safe y.
#         # P4: Final move: absolute destination.
#         P0 = (start_x, start_y)
#         P1 = (start_x, start_safe_y)
#         P2 = (dest_safe_x, start_safe_y)
#         P3 = (dest_safe_x, dest_safe_y)
#         P4 = (dest_x, dest_y)

#         waypoints = [P0, P1, P2, P3, P4]

#         # Convert waypoints to relative moves.
#         relative_moves = []
#         for i in range(1, len(waypoints)):
#             prev = waypoints[i - 1]
#             curr = waypoints[i]
#             delta = (curr[0] - prev[0], curr[1] - prev[1])
#             relative_moves.append(delta)

#         return [P0] + relative_moves

#     def parse_fen(self, fen):
#         """
#         Parses a FEN string and returns a dictionary mapping board squares (e.g., "e4")
#         to piece characters.
        
#         FEN rows are processed from rank 8 to rank 1.
#         """
#         board = {}
#         fen_rows = fen.split()[0].split('/')
#         for i, row in enumerate(fen_rows):
#             rank = 8 - i  # ranks 8 to 1
#             file_index = 0
#             for ch in row:
#                 if ch.isdigit():
#                     file_index += int(ch)
#                 else:
#                     file_letter = chr(ord('a') + file_index)
#                     square = file_letter + str(rank)
#                     board[square] = ch
#                     file_index += 1
#         return board

#     def square_to_coords_ry(self, square):
#         """
#         Converts a board square (e.g., "h1" or "a8") to physical coordinates.
        
#         Coordinate system:
#         - x: rank coordinate (rank 1 at x=0, rank 8 at x=350)
#         - y: file coordinate (file h at y=0, file a at y=350)
#         """
#         file_letter = square[0]
#         rank_digit = int(square[1])
#         x = (rank_digit - 1) * 50
#         file_index = ord(file_letter) - ord('a')
#         y = (7 - file_index) * 50
#         return (x, y)

#     def coords_to_square(self, coords):
#         """
#         Converts physical coordinates back into a board square.
#         Assumes coordinates are at board-square centers (multiples of 50).
#         """
#         x, y = coords
#         rank = int(x / 50) + 1
#         file_index = 7 - int(y / 50)
#         file_letter = chr(ord('a') + file_index)
#         return file_letter + str(rank)

#     def select_target_square(self, piece, candidates, occupancy):
#         """
#         Given a piece and a list of candidate target squares, returns the first candidate
#         that is not yet occupied.
#         """
#         for candidate in candidates:
#             if occupancy.get(candidate) is None:
#                 return candidate
#         return None

#     # --- (Board Reset Functions such as piece_alternatives and plan_board_reset would be here.)
#     # For brevity, assume these functions are already defined as in the previous code.

#     # --- Captured Piece Recovery Functions ---

#     def recover_captured_piece_path(self, captured_coord, piece, occupancy):
#         """
#         Generates a movement path for a captured piece to re-enter the board.
        
#         The path consists of:
#         1. Moving from its captured coordinate to set its y to 375.
#         2. Moving horizontally to set its x to 25 if white, or 325 if black.
#         3. Sliding vertically (in the -y direction) in 50-unit steps until it reaches
#             an empty board square.
        
#         Returns a tuple (path, final_square) where:
#         - path is a list starting with the absolute starting coordinate followed by relative moves.
#         - final_square is the board square (e.g., "e4") where the piece will be placed.
#         """
#         # Determine color: white if uppercase, black if lowercase.
#         if piece.isupper():
#             target_x = 25  # White pieces re-enter near x=25.
#         else:
#             target_x = 325  # Black pieces re-enter near x=325.
        
#         # Waypoint 1: Move from captured_coord to y = 375 (keeping original x).
#         wp1 = (captured_coord[0], 375)
#         # Waypoint 2: Move horizontally to set x to target_x (keeping y = 375).
#         wp2 = (target_x, 375)
        
#         # Now, slide vertically downward along the -y direction.
#         # Board-square centers in y are: 350, 300, 250, 200, 150, 100, 50, 0.
#         candidate_y = 350
#         final_coord = None
#         final_square = None
#         while candidate_y >= 0:
#             candidate_coord = (target_x, candidate_y)
#             square_candidate = self.coords_to_square(candidate_coord)
#             if occupancy.get(square_candidate) is None:
#                 final_coord = candidate_coord
#                 final_square = square_candidate
#                 break
#             candidate_y -= 50
#         if final_coord is None:
#             print("No available board square for captured piece", piece)
#             return None, None

#         # Construct the full path:
#         #  - From captured_coord to wp1,
#         #  - then from wp1 to wp2,
#         #  - then from wp2 to final_coord.
#         delta1 = (wp1[0] - captured_coord[0], wp1[1] - captured_coord[1])
#         delta2 = (wp2[0] - wp1[0], wp2[1] - wp1[1])
#         delta3 = (final_coord[0] - wp2[0], final_coord[1] - wp2[1])
#         path = [captured_coord, delta1, delta2, delta3]
#         return path, final_square

#     def plan_captured_piece_recovery(captured_pieces, occupancy):
#         """
#         Processes the captured pieces (stored off-board) and generates recovery paths.
        
#         Captured pieces are assumed to be stored in an alternating pattern by colour.
#         For white pieces, the pattern is (in order):
#             (350,435), (350,410), (325,435), (325,410)
#         For black pieces, the pattern is:
#             (0,435), (0,410), (25,435), (25,410)
#         This function splits the captured pieces by colour and assigns each a stored coordinate
#         (cycling through the pattern if there are more pieces than pattern positions).
        
#         For each piece, it calls recover_captured_piece_path to generate the path.
        
#         Returns two dictionaries (one for white and one for black) mapping an index to the recovery plan.
#         Each recovery plan includes:
#         - "piece": the piece symbol,
#         - "start_coord": the stored (captured) coordinate,
#         - "final_square": the board square where it will be placed,
#         - "path": the movement path.
#         """
#         # Define the stored coordinate patterns.
#         white_pattern = [(350, 435), (350, 410), (325, 435), (325, 410)]
#         black_pattern = [(0, 435), (0, 410), (25, 435), (25, 410)]
        
#         white_moves = {}
#         black_moves = {}
#         white_index = 0
#         black_index = 0
        
#         for i, piece in enumerate(captured_pieces):
#             if piece.isupper():
#                 # White captured piece.
#                 stored_coord = white_pattern[white_index % len(white_pattern)]
#                 white_index += 1
#                 path, final_square = recover_captured_piece_path(stored_coord, piece, occupancy)
#                 white_moves[i] = {
#                     "piece": piece,
#                     "start_coord": stored_coord,
#                     "final_square": final_square,
#                     "path": path
#                 }
#             else:
#                 # Black captured piece.
#                 stored_coord = black_pattern[black_index % len(black_pattern)]
#                 black_index += 1
#                 path, final_square = recover_captured_piece_path(stored_coord, piece, occupancy)
#                 black_moves[i] = {
#                     "piece": piece,
#                     "start_coord": stored_coord,
#                     "final_square": final_square,
#                     "path": path
#                 }
        
#         return white_moves, black_moves

# # --- Example Usage ---

# if __name__ == "__main__":
#     # For demonstration, assume the board has been reset already.
#     # The occupancy dictionary maps board squares (e.g., "e4") to pieces.
#     # For simplicity in this example, we'll start with an empty board occupancy.
#     board_occupancy = {sq: None for sq in [
#         file + str(rank) for rank in range(1, 9) for file in "abcdefgh"
#     ]}
    
#     # You might update board_occupancy based on the board-reset moves.
#     # For this example, assume some squares are already filled.
#     board_occupancy["e1"] = "Q"  # for instance, white queen is placed.
#     board_occupancy["c3"] = "R"  # white rook is placed.
    
#     # List of captured pieces (for example, a mix of white and black).
#     captured_pieces = ["P", "N", "B", "p", "q", "r"]
    
#     white_recovery, black_recovery = plan_captured_piece_recovery(captured_pieces, board_occupancy)
    
#     print("White Captured Piece Recovery Moves:")
#     for idx, info in white_recovery.items():
#         print(f"Piece {info['piece']} from stored {info['start_coord']} to {info['final_square']}:")
#         print(info["path"])
    
#     print("\nBlack Captured Piece Recovery Moves:")
#     for idx, info in black_recovery.items():
#         print(f"Piece {info['piece']} from stored {info['start_coord']} to {info['final_square']}:")
#         print(info["path"])
