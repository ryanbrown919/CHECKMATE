import math
import time

from hall_control import Hall
from gantry_control import GantryControl

class BoardReset:




    starting_positions = {
    "K": ["e1"],                  # White King
    "Q": ["d1"],                  # White Queen
    "R": ["a1", "h1"],            # White Rooks
    "B": ["c1", "f1"],            # White Bishops
    "N": ["b1", "g1"],            # White Knights
    "P": ["a2", "b2", "c2", "d2", "e2", "f2", "g2", "h2"],  # White Pawns

    "k": ["e8"],                  # Black King
    "q": ["d8"],                  # Black Queen
    "r": ["a8", "h8"],            # Black Rooks
    "b": ["c8", "f8"],            # Black Bishops
    "n": ["b8", "g8"],            # Black Knights
    "p": ["a7", "b7", "c7", "d7", "e7", "f7", "g7", "h7"]   # Black Pawns
}



    def __init__(self, gantry, hall):    

        self.gantry = gantry
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
        Returns a tuple: (start, movement vector to the closest target relative to start).
        """
        if not targets:
            return (start, (0, 0))  # No targets, no movement
    
        # Find the nearest target
        nearest = min(targets, key=lambda x: self.distance(start, x))
    
        # Calculate the movement vector relative to the start
        movement_vector = (nearest[0] - start[0], nearest[1] - start[1])
    
        return (start, movement_vector)

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
            return (x, y)

    def coord_to_chess_square(self, coord):
        """
        Convert board coordinate (x, y) into a chess square label.
        Assumption: Board row 0 is rank 8 and row 7 is rank 1.
        """
        x, y = coord

        file = chr(ord('H') + x)
        rank = str(8 - y)
        return file + rank
       
    def symbol_to_valid_coordinates(self, symbol):
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
        print("Test: CALLED METHOD 'symbol_to_valid_coordinates'")
        return valid_gantry_coords.get(symbol, [])

    def TEST_reset_playing_area_white(self):
        """
        TEST METHOD - See if Jack's code works without relying on cleared/sorted starting positions.
        """
        print("Test: STARTING METHOD 'TEST_reset_playing_area_white'")

        pieces = self.fen_to_coords("4r3/8/2kPnK2/8/8/2QpNq2/8/4Rb2")

        for piece in pieces:
            symbol, coords = piece

            # Only process white pieces (uppercase symbols)
            if not symbol.isupper():
                continue

            x, y = coords

            # Only process pieces not in the deadzone
            if y < 375:
                # Get valid starting coordinates for the piece type
                valid_coords = self.symbol_to_valid_coordinates(symbol)
                print(f"Valid coordinates for {symbol}: {valid_coords}")
                # Check which of those valid coordinates are already occupied
                # occupied_coords = self.get_occupied_squares(self.board)
                unoccupied_coords = [coord for coord in valid_coords if coord not in occupied_coords]

                if unoccupied_coords:
                    # Select the first unoccupied valid coordinate
                    target_coord = unoccupied_coords[0]
                else:
                    # If all valid targets are occupied, make space by moving a blocking piece
                    blocking_piece = None
                    for coord in valid_coords:
                        for other_piece in pieces:
                            if other_piece[1] == coord:
                                blocking_piece = other_piece
                                break
                        if blocking_piece:
                            break

                    if blocking_piece:
                        # Move the blocking piece to another valid position
                        blocking_symbol, blocking_coords = blocking_piece
                        blocking_valid_coords = self.symbol_to_valid_coordinates(blocking_symbol)
                        blocking_unoccupied_coords = [
                            coord for coord in blocking_valid_coords if coord not in occupied_coords
                        ]

                        if blocking_unoccupied_coords:
                            blocking_target_coord = blocking_unoccupied_coords[0]
                            print(f"Making space: Moving blocking piece {blocking_symbol} from {blocking_coords} to {blocking_target_coord}")

                            # Update the board state for the blocking piece
                            old_rank, old_file = blocking_coords[1] // 50, blocking_coords[0] // 50
                            new_rank, new_file = blocking_target_coord[1] // 50, blocking_target_coord[0] // 50
                            self.board[old_rank][old_file] = 0  # Mark old square as empty
                            self.board[new_rank][new_file] = 1  # Mark new square as occupied

                            # Update the blocking piece's position
                            self.gantry.white_captured.remove(blocking_piece)
                            self.gantry.white_captured.append((blocking_symbol, blocking_target_coord))

                            # Set the target coordinate for the current piece
                            target_coord = coord

                if target_coord:
                    # Update the white_captured list with the new coordinates
                    self.gantry.white_captured.remove(piece)  # Add logic for duplicate pieces
                    self.gantry.white_captured.append((symbol, target_coord))

                    # Update the board state to reflect the move
                    old_rank, old_file = coords[1] // 50, coords[0] // 50
                    new_rank, new_file = target_coord[1] // 50, target_coord[0] // 50
                    self.board[old_rank][old_file] = 0  # Mark old square as empty
                    self.board[new_rank][new_file] = 1  # Mark new square as occupied

                    # Execute the movement using the gantry
                    print(f"Moving {symbol} from {coords} to {target_coord}")

                    # Uncomment the following lines when debugging is done:
                    # path = [coords, target_coord]  # Simple direct path
                    # movements = self.gantry.parse_path_to_movement(path)
                    # commands = self.gantry.movement_to_gcode(movements)
                    # self.gantry.send_commands(commands)

    def reset_playing_area_white(self):
        """
        Reset all WHITE pieces NOT on ranks 1, 2 or in the deadzone.
        Assumes that the starting locations are either unoccupied or filled with the correct piece.
        """
        
        print("Test: STARTING METHOD 'reset_playing_area_white'")
       
        pieces = self.fen_to_coords("4r3/8/2kPnK2/8/8/2QpNq2/8/4Rb2")

        for piece in pieces:
            symbol, coords = piece

            # Only process white pieces (uppercase symbols)
            if not symbol.isupper():
                continue

            x, y = coords

            # Only process pieces in ranks 3-8 and not in the deadzone
            if x < 75 and y < 375:
                # Get valid starting coordinates for the piece type
                valid_coords = self.symbol_to_valid_coordinates(symbol)

                # Check which of those valid coordinates are already occupied
                # occupied_coords = self.get_occupied_squares(self.board)
                unoccupied_coords = []
                for coord in valid_coords:
                    if coord not in occupied_coords:
                        unoccupied_coords.append(coord)

                if unoccupied_coords:
                    # Select the first unoccupied valid coordinate
                    target_coord = unoccupied_coords[0]

                    # Update the white_captured list with the new coordinates
                    self.gantry.white_captured.remove(piece)  # Add logic for duplicate pieces
                    self.gantry.white_captured.append((symbol, target_coord))

                    # Update the board state to reflect the move
                    old_rank, old_file = coords[1] // 50, coords[0] // 50
                    new_rank, new_file = target_coord[1] // 50, target_coord[0] // 50
                    # self.board[old_rank][old_file] = 0  # Mark old square as empty
                    # self.board[new_rank][new_file] = 1  # Mark new square as occupied

                    # Execute the movement using the gantry
                    print(f"Moving {symbol} from {coords} to {target_coord}")

                    # Uncomment the following lines when debugging is done:
                    # path = [coords, target_coord]  # Simple direct path
                    # movements = self.gantry.parse_path_to_movement(path)
                    # commands = self.gantry.movement_to_gcode(movements)
                    # self.gantry.send_commands(commands)

    def reset_playing_area_black(self):
        # could probably merge this with above method to reduce bloat but oh well, cry about it 
        """
        Reset all BLACK pieces NOT on ranks 7, 8 or in the deadzone.
        Assumes that the starting locations are either unoccupied or filled with the correct piece.
        """
        
        print("Test: STARTING METHOD 'reset_playing_area_black'")
       
        pieces = self.fen_to_coords("4r3/8/2kPnK2/8/8/2QpNq2/8/4Rb2")

        for piece in pieces:
            symbol, coords = piece

            # Only process black pieces (lowercase symbols)
            if not symbol.islower():
                continue

            x, y = coords

            # Only process pieces in ranks 1-6 and not in the deadzone
            if x > 257 and y < 375:
                # Get valid starting coordinates for the piece type
                valid_coords = self.symbol_to_valid_coordinates(symbol)

                # Check which of those valid coordinates are already occupied
                occupied_coords = self.get_occupied_squares(self.board)
                unoccupied_coords = []
                for coord in valid_coords:
                    if coord not in occupied_coords:
                        unoccupied_coords.append(coord)

                if unoccupied_coords:
                    # Select the first unoccupied valid coordinate
                    target_coord = unoccupied_coords[0]

                    # Update the white_captured list with the new coordinates
                    self.gantry.white_captured.remove(piece)  # Add logic for duplicate pieces
                    self.gantry.white_captured.append((symbol, target_coord))

                    # Update the board state to reflect the move
                    old_rank, old_file = coords[1] // 50, coords[0] // 50
                    new_rank, new_file = target_coord[1] // 50, target_coord[0] // 50
                    self.board[old_rank][old_file] = 0  # Mark old square as empty
                    self.board[new_rank][new_file] = 1  # Mark new square as occupied

                    # Execute the movement using the gantry
                    print(f"Moving {symbol} from {coords} to {target_coord}")

                    # Uncomment the following lines when debugging is done:
                    # path = [coords, target_coord]  # Simple direct path
                    # movements = self.gantry.parse_path_to_movement(path)
                    # commands = self.gantry.movement_to_gcode(movements)
                    # self.gantry.send_commands(commands)

    def reset_playing_area_black(self):
        # could probably merge this with above method to reduce bloat but oh well, cry about it 
        """
        Reset all BLACK pieces NOT on ranks 7, 8 or in the deadzone.
        Assumes that the starting locations are either unoccupied or filled with the correct piece.
        """
        
        print("Test: STARTING METHOD 'reset_playing_area_black'")
       
        pieces = self.fen_to_coords("4r3/8/2kPnK2/8/8/2QpNq2/8/4Rb2")

        for piece in pieces:
            symbol, coords = piece

            # Only process black pieces (lowercase symbols)
            if not symbol.islower():
                continue

            x, y = coords

            # Only process pieces in ranks 1-6 and not in the deadzone
            if x > 257 and y < 375:
                # Get valid starting coordinates for the piece type
                valid_coords = self.symbol_to_valid_coordinates(symbol)

                # Check which of those valid coordinates are already occupied
                occupied_coords = self.get_occupied_squares(self.board)
                unoccupied_coords = []
                for coord in valid_coords:
                    if coord not in occupied_coords:
                        unoccupied_coords.append(coord)

                if unoccupied_coords:
                    # Select the first unoccupied valid coordinate
                    target_coord = unoccupied_coords[0]

                    # Update the black_captured list with the new coordinates
                    self.gantry.black_captured.remove(piece)  # Add logic for duplicate pieces
                    self.gantry.black_captured.append((symbol, target_coord))

                    # Update the board state to reflect the move
                    old_rank, old_file = coords[1] // 50, coords[0] // 50
                    new_rank, new_file = target_coord[1] // 50, target_coord[0] // 50
                    self.board[old_rank][old_file] = 0  # Mark old square as empty
                    self.board[new_rank][new_file] = 1  # Mark new square as occupied

                    # Execute the movement using the gantry
                    print(f"Moving {symbol} from {coords} to {target_coord}")

                    # Uncomment the following lines when debugging is done:
                    # path = [coords, target_coord]  # Simple direct path
                    # movements = self.gantry.parse_path_to_movement(path)
                    # commands = self.gantry.movement_to_gcode(movements)
                    # self.gantry.send_commands(commands)
                    
    def reset_playing_area_deadzone(self):
        """
        Reset all pieces in the deadzone.
        """
        print("Test: STARTING METHOD 'reset_playing_area_deadzone'")

        # Process white pieces in the deadzone
        for piece in self.gantry.white_captured:
            symbol, coords = piece
            x, y = coords

            # Check if the piece is in the deadzone (y > 375)
            if y > 375:
                # Get valid starting coordinates for the piece type
                valid_coords = self.symbol_to_valid_coordinates(symbol)

                # Check which of those valid coordinates are already occupied
                occupied_coords = self.get_occupied_squares(self.board)
                unoccupied_coords = [coord for coord in valid_coords if coord not in occupied_coords]

                if unoccupied_coords:
                    # Select the first unoccupied valid coordinate
                    target_coord = unoccupied_coords[0]

                    # Update the white_captured list with the new coordinates
                    self.gantry.white_captured.remove(piece)
                    self.gantry.white_captured.append((symbol, target_coord))

                    # Update the board state to reflect the move
                    old_rank, old_file = coords[1] // 50, coords[0] // 50
                    new_rank, new_file = target_coord[1] // 50, target_coord[0] // 50
                    self.board[old_rank][old_file] = 0  # Mark old square as empty
                    self.board[new_rank][new_file] = 1  # Mark new square as occupied

                    # Execute the movement using the gantry
                    print(f"Moving white piece {symbol} from {coords} to {target_coord}")

                    # need DIAZ to do dead zone path palnning logic

        # Process black pieces in the deadzone
        for piece in self.gantry.black_captured:
            symbol, coords = piece
            x, y = coords

            # Check if the piece is in the deadzone (y > 375)
            if y > 375:
                # Get valid starting coordinates for the piece type
                valid_coords = self.symbol_to_valid_coordinates(symbol)

                # Check which of those valid coordinates are already occupied
                occupied_coords = self.get_occupied_squares(self.board)
                unoccupied_coords = [coord for coord in valid_coords if coord not in occupied_coords]

                if unoccupied_coords:
                    # Select the first unoccupied valid coordinate
                    target_coord = unoccupied_coords[0]

                    # Update the black_captured list with the new coordinates
                    self.gantry.black_captured.remove(piece)
                    self.gantry.black_captured.append((symbol, target_coord))

                    # Update the board state to reflect the move
                    old_rank, old_file = coords[1] // 50, coords[0] // 50
                    new_rank, new_file = target_coord[1] // 50, target_coord[0] // 50
                    self.board[old_rank][old_file] = 0  # Mark old square as empty
                    self.board[new_rank][new_file] = 1  # Mark new square as occupied

                    # Execute the movement using the gantry
                    print(f"Moving black piece {symbol} from {coords} to {target_coord}")

                    # need DIAZ to do dead zone path palnning logic...

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
                if (char.isdigit()):
                    file_idx += int(char)  # Skip empty squares
                else:
                    square = f"{chr(ord('a') + file_idx)}{rank_idx + 1}"
                    coord = self.square_to_coord(square)
                    pieces.append((char, (coord[0]*25, coord[1]*25)))
                    file_idx += 1  # Move to the next file

        print("Test: CALLED METHOD 'fen_to_coords'")
        return pieces

    def reset_board_from_game(self):
        # Add logic here for dealign with resetting as well as deadzone pieces
        # DEAL WITH EXISITING FIRST 

        # Parse the FEN string to extract list of pieces and their coordinates
        board_state = self.fen_to_coords("4r3/8/2kPnK2/8/8/2QpNq2/8/4Rb2")
        print(f"Board state: {board_state}")
    
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
        print(f"[Test] Untransformed Empty squares: {empty_squares}")
        empty_squares = [row[::-1] for row in empty_squares]
        print(f"[Test] Transformed Empty squares: {empty_squares}")

        # Invert 1s and 0s in the empty_squares matrix
        empty_squares = [[1 - cell for cell in row] for row in empty_squares]
        print(f"[Test] Inverted Empty squares: {empty_squares}")

        empty_targets = []
        for i in range(len(empty_squares)):
            for j in range(len(empty_squares[i])): 
                if empty_squares[i][j] == 1:
                    empty_targets.append((j*50, i*50))  
        
        print(f"[Test] Empty targets: {empty_targets}")


        ##moveblack piece out of white endzone    
        print("[Test] Moving black pieces out of white endzone")
        for piece in self.gantry.black_captured:
            symbol, coords = piece
            print(f"Black piece: {symbol} at {coords}")
            x, y = coords
            if x < 75 and y < 375:
                # move is contains initial and final cords of black piece
                ''' remove empty squares to remove ranks 1 and 2 (all empty squares with x =0 and x= 50 ) '''
                # Remove empty squares to exclude ranks 1 and 2 (all empty squares with x = 0 and x = 50)
                # Copy empty_targets to filtered_empty_squares and filter out values with x = 0 or x = 50
                filtered_empty_squares = [coord for coord in empty_targets if coord[1] != 0 and coord[0] != 50]
                
                print(f"[Test] Filtered empty squares (excluding x = 0 and x = 50): {filtered_empty_squares}")



                # print(f"[Test] Filtered empty squares (excluding ranks 1 and 2): {filtered_empty_squares}")
                move = self.nearest_neighbor(coords, filtered_empty_squares) 
                final_cords = (move[0][0] + move[1][0], move[0][1] + move[1][1])
                path = [move[0], (0, 25), (move[1][0]-25, 0), (0, move[1][1] - 25), (25, 0)]

                # Update the black_captured list with the new coordinates
                self.gantry.black_captured.remove(piece) # me no likey
                self.gantry.black_captured.append((symbol, final_cords))

                # Update the empty_targets
                empty_targets.remove(final_cords)
                empty_targets.append(move[0])

                # Execute the movement using the gantry
                print(f"[Test] Moving black piece {symbol} from {move[0]} to {move[1]} via path: {path}")
                # print(f"Moving black piece {symbol} from {coords} to {new_coords} via path: {path}")
                movements = self.gantry.parse_path_to_movement(path)
                commands = self.gantry.movement_to_gcode(movements)
                print(f"Last move: {commands}")
                # self.gantry.send_commands(commands)

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
                final_cords = (move[0][0] + move[1][0], move[0][1] + move[1][1])
                if move[0][0] < 25 :
                    path = [move[0], (25, 0), (0, move[1][1]), (move[1][0] - 25, 0)]
                else:
                    path = [move[0], (-25, 0), (0, move[1][1]), (move[1][0] + 25, 0)]
        
                print(f"[Test] Moving white piece {symbol} from {move[0]} to {move[1]} via path: {path}")

                # Update white_captured list with new coordinates of the piece just moved
                self.gantry.white_captured.remove(piece)  # Remove the old entry
                self.gantry.white_captured.append((symbol, final_cords))  # Add the updated entry with new coordinates

                # Update the empty_targets matrix
                empty_targets.remove(final_cords)
                empty_targets.append(move[0])
                        
                # print(f"arranging white in rank 1 & 2: {path}")
                movements = self.gantry.parse_path_to_movement(path)
                commands = self.gantry.movement_to_gcode(movements)
                print(f"Last move: {commands}")
                self.gantry.send_commands(commands)         
                

    def full_reset(self, captured_pieces):

    
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

        # print(piece_alternatives)

        # occupancy = self.hall.sense_layer.get_squares_game()
        # print(occupancy)

        # occ_dict = self.occupancy_list_to_dict(occupancy)
        # print(occ_dict)

        # # current_fen = "r1bqnr2/1pp2kpQ/p1np1bB1/8/8/5N2/PB1P2PP/RN2R1K1"
        # # current_fen = self.board.fen().split()[0]
        # current_fen  = "rnbqkbnr/ppp1pppp/3p4/8/8/8/PPPP1PPP/RNBQKBNR"

        # self.captured_pieces=['P']


        # # Target configuration FEN: swap the white queen and white rook.
        # target_fen  = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"

        # moves = self.plan_board_reset(current_fen, target_fen, piece_alternatives)

        # for start_square, info in moves.items():
        #     print(f"Move {info['piece']} from {start_square} to {info['final_square']} via path:")
        #     print(info["path"])

        #     cmds = self.gantry.path_to_gcode(info["path"])
        #     self.gantry.send_commands(cmds)


        # # occupancy = self.occupancy_list_to_dict(self.hall.sense_layer.get_squares_game())

        # white_recovery, black_recovery = self.plan_captured_piece_recovery(self.captured_pieces)

        # for idx, info in white_recovery.items():
        #     print(f"Piece {info['piece']} from stored {info['start_coord']} to {info['final_square']}:")
        #     print(info["path"])

        #     cmds = self.gantry.path_to_gcode(info["path"])
        #     self.gantry.send_commands(cmds)

        # for idx, info in black_recovery.items():
        #     print(f"Piece {info['piece']} from stored {info['start_coord']} to {info['final_square']}:")
        #     print(info["path"])

        #     cmds = self.gantry.path_to_gcode(info["path"])
        #     self.gantry.send_commands(cmds)


        # ''' Felipe's code '''
        # self.reset_board_from_game()
        # ''' Jack's code '''
        # self.reset_playing_area_white()
        # ''' Felipe's code '''
        # self.reset_board_from_game()

        # current_fen  = "rnbqkbnr/pppppppp/8/8/8/8/PPP1PPPP/RNBQKBNR"

        current_fen = self.board.fen()
        current_fen = current_fen.split()[0]

        # self.captured_pieces=['P', 'P', 'P', 'P']

        moves = self.simple_reset_to_home(current_fen)

        for start_square, info in moves.items():
            print(f"Move {info['piece']} from {start_square} to {info['final_square']} via path:")
            print(info["path"])

            cmds = self.gantry.path_to_gcode(info["path"])
            self.gantry.send_commands(cmds)

        self.recover_captured_pieces(['P', 'p', 'p', 'P'])

        # white_moves = self.captured_piece_return(self.captured_pieces)
        # print("Assignments")
        # print(white_moves)

        # for start_square, info in white_moves.items():
        #     print(f"Move {info['piece']} from {start_square} to {info['final_square']} via path:")
        #     print(info["path"])

        #     cmds = self.gantry.path_to_gcode(info["path"])
        #     self.gantry.send_commands(cmds)

        # for start_square, info in black_moves.items():
        #     print(f"Move {info['piece']} from {start_square} to {info['final_square']} via path:")
        #     print(info["path"])

        #     cmds = self.gantry.path_to_gcode(info["path"])
        #     self.gantry.send_commands(cmds)


    # def reset_board_to_home_recursive(self, current_mapping, moves_so_far=None):
    #     """
    #     Recursively processes the dictionary of pieces that need to be moved (current_mapping)
    #     and assigns each piece a home square if one of its candidate home squares is free.
    #     At each step, the function polls the current board occupancy via the hall-effect sensors,
    #     so that pieces already moved (and thus occupying their home squares) are taken into account.
        
    #     Parameters:
    #     current_mapping: dict mapping square (string) -> piece symbol for pieces not yet moved.
    #     moves_so_far: dict (accumulated move plans). Each move plan is a dictionary with:
    #         - "piece": piece symbol,
    #         - "final_square": chosen home square,
    #         - "path": list of moves (first element is absolute start, then relative moves).
        
    #     Returns:
    #     A dictionary of move plans for pieces that have been moved.
    #     (If no further progress is possible, any remaining pieces are reported as delayed.)
    #     """
    #     if moves_so_far is None:
    #         moves_so_far = {}

    #     # Base case: if there are no pieces left to move, return the accumulated moves.
    #     if not current_mapping:
    #         return moves_so_far

    #     # Define the standard home squares for each piece type.
    #     starting_positions = {
    #         "K": ["e1"],
    #         "Q": ["d1"],
    #         "R": ["a1", "h1"],
    #         "B": ["c1", "f1"],
    #         "N": ["b1", "g1"],
    #         "P": ["a2", "b2", "c2", "d2", "e2", "f2", "g2", "h2"],
    #         "k": ["e8"],
    #         "q": ["d8"],
    #         "r": ["a8", "h8"],
    #         "b": ["c8", "f8"],
    #         "n": ["b8", "g8"],
    #         "p": ["a7", "b7", "c7", "d7", "e7", "f7", "g7", "h7"]
    #     }

    #     moves_this_round = {}
    #     remaining = {}

    #     # Iterate over a copy of the current mapping.
    #     for square, piece in current_mapping.items():
    #         # Skip if the piece is already at one of its home squares.
    #         if square in starting_positions.get(piece, []):
    #             continue

    #         # Poll the current occupancy from the hall sensors.
    #         occ = self.occupancy_list_to_dict(self.hall.sense_layer.get_squares_game())
    #         candidate_found = None
    #         for candidate in starting_positions.get(piece, []):
    #             if occ.get(candidate, 0) == 0:
    #                 candidate_found = candidate
    #                 break

    #         if candidate_found is not None:
    #             # Generate a natural path from the piece's current square to the chosen candidate.
    #             start_coords = self.square_to_coords_ry(square)
    #             dest_coords = self.square_to_coords_ry(candidate_found)
    #             path = self.generate_natural_path(start_coords, dest_coords)
    #             moves_this_round[square] = {
    #                 "piece": piece,
    #                 "final_square": candidate_found,
    #                 "path": path
    #             }
    #         else:
    #             # No candidate free; keep the piece in the remaining list.
    #             remaining[square] = piece

    #     # If no moves were made this round, then stop recursion.
    #     if not moves_this_round:
    #         print("No further progress can be made. The following moves remain delayed:", remaining)
    #         # Optionally, record the remaining pieces as delayed.
    #         moves_so_far.update({sq: {"piece": p, "final_square": None, "path": []} for sq, p in remaining.items()})
    #         return moves_so_far
    #     else:
    #         # Update moves_so_far with moves from this round.
    #         moves_so_far.update(moves_this_round)
    #         # Remove the moved pieces from the current mapping.
    #         for sq in moves_this_round.keys():
    #             if sq in current_mapping:
    #                 del current_mapping[sq]
    #         # Recurse on the remaining pieces.
    #         return self.reset_board_to_home_recursive(current_mapping, moves_so_far)
        
    def simple_reset_to_home(self, fen):
        """
        Simple function to move pieces from their current positions (parsed from the FEN)
        to their standard home squares.

        It works as follows:
        1. Parses the FEN string into a mapping of square -> piece.
        2. For each piece, checks its list of home squares (from a hard-coded dictionary)
            by polling current occupancy (using self.hall.sense_layer.get_squares_game() and 
            occupancy_list_to_dict).
        3. If a candidate home square is free (occupancy == 0), it generates a natural path
            from the current square to that home square using generate_natural_path.
        4. It then "moves" the piece (removing it from the list) and records the move plan.
        5. This process repeats until all pieces have been moved (or no progress can be made).
        
        Returns a dictionary mapping the original square of each moved piece to its move plan.
        Each move plan is a dictionary with:
        - "piece": the piece symbol,
        - "final_square": the chosen home square,
        - "path": a list starting with the absolute starting coordinate, then relative moves.
        """
        # Define the standard home (starting) positions.
        starting_positions = {
            "K": ["e1"],
            "Q": ["d1"],
            "R": ["a1", "h1"],
            "B": ["c1", "f1"],
            "N": ["b1", "g1"],
            "P": ["a2", "b2", "c2", "d2", "e2", "f2", "g2", "h2"],
            "k": ["e8"],
            "q": ["d8"],
            "r": ["a8", "h8"],
            "b": ["c8", "f8"],
            "n": ["b8", "g8"],
            "p": ["a7", "b7", "c7", "d7", "e7", "f7", "g7", "h7"]
        }

        # Parse the FEN to get a dictionary of current positions.
        current_mapping = self.parse_fen(fen)

        print(current_mapping)
        
        # This will hold our move plans.
        move_plans = {}

        occupancy = self.occupancy_list_to_dict(self.hall.sense_layer.get_squares_game())


        # Loop until current_mapping is empty (all pieces moved) or no progress can be made.
        progress = True
        while current_mapping:
            progress = False
            # Get current occupancy from the hall sensors.
            print("occupancy:")
            print(occupancy)
            # Use a copy of the current mapping so we can modify it during iteration.
            for square, piece in list(current_mapping.items()):
                # If the piece is already at one of its home squares, remove it.
                if square in starting_positions.get(piece, []):
                    del current_mapping[square]
                    continue

                # Look for a free home square candidate.
                candidates = starting_positions.get(piece, [])
                candidate_found = None
                for candidate in candidates:
                    # Check occupancy: free if the value is 0.
                    if occupancy.get(candidate, 0) == 0:
                        candidate_found = candidate
                        break

                if candidate_found:
                    # Get physical coordinates for the current square and candidate square.
                    start_coords = self.square_to_coords_ry(square)
                    dest_coords = self.square_to_coords_ry(candidate_found)
                    # Generate a natural path (assumed to move through the corners of the square).
                    path = self.generate_natural_path(start_coords, dest_coords)
                    occupancy[square] = 0
                    occupancy[candidate] = 1
                    # Record the move plan.
                    move_plans[square] = {
                        "piece": piece,
                        "final_square": candidate_found,
                        "path": path
                    }
                    # "Move" the piece by removing it from current_mapping.
                    del current_mapping[square]
                    progress = True
            # If no progress was made during this iteration, break the loop.
            print("current mapping")
            print(current_mapping)
            if not progress:
                print("No further progress can be made. The following pieces remain unmoved:", current_mapping)
                break

        return move_plans
    
    # def recover_captured_piece_path(self, captured_coord, piece, occupancy):
    #     """
    #     Generates a movement path for a captured piece to re-enter the board.

    #     The plan is:
    #     1. From its stored coordinate (captured_coord), move vertically so that its y becomes 375.
    #     2. Then move horizontally so that its x becomes 25 (for white pieces, uppercase)
    #         or 325 (for black pieces, lowercase) while keeping y = 375.
    #     3. Then, from that intermediate point, select the closest available home square 
    #         (from a predefined home_positions dictionary) based on Euclidean distance.
    #     4. Generate a natural path from the intermediate point to the candidate's center.
        
    #     Returns:
    #     A tuple (path, final_square), where:
    #         - path is a list in the format: [absolute start, relative move1, relative move2, ...]
    #         - final_square is the chosen home square (e.g. "e2") where the piece will be placed.
        
    #     Assumptions:
    #     - occupancy is obtained by self.occupancy_list_to_dict(self.hall.sense_layer.get_squares_game())
    #     - Helper methods self.square_to_coords_ry(square) and self.generate_natural_path(start, dest) exist.
    #     """
    #     # Define home positions (standard starting positions) locally.
    #     home_positions = {
    #         "K": ["e1"],
    #         "Q": ["d1"],
    #         "R": ["a1", "h1"],
    #         "B": ["c1", "f1"],
    #         "N": ["b1", "g1"],
    #         "P": ["a2", "b2", "c2", "d2", "e2", "f2", "g2", "h2"],
    #         "k": ["e8"],
    #         "q": ["d8"],
    #         "r": ["a8", "h8"],
    #         "b": ["c8", "f8"],
    #         "n": ["b8", "g8"],
    #         "p": ["a7", "b7", "c7", "d7", "e7", "f7", "g7", "h7"]
    #     }
        
    #     # Step 1: Move vertically so that y becomes 375.
    #     wp1 = (captured_coord[0], 375)
    #     # Step 2: Move horizontally so that x becomes target_x.
    #     target_x = 25 if piece.isupper() else 325
    #     wp2 = (target_x, 375)
        
    #     # Step 3: From wp2, select the closest available home square.
    #     # Get candidate home squares for this piece.
    #     candidates = home_positions.get(piece, [])
    #     best_candidate = None
    #     best_dist = float('inf')
        
    #     for candidate in candidates:
    #         # Re-read occupancy each time to ensure the candidate is up-to-date.
    #         occ = self.occupancy_list_to_dict(self.hall.sense_layer.get_squares_game())
    #         if occ.get(candidate, 0) != 0:
    #             continue  # Candidate square is occupied.
    #         # Convert candidate square to its center coordinates.
    #         candidate_coord = self.square_to_coords_ry(candidate)
    #         # Compute Euclidean distance from wp2.
    #         dist = math.hypot(candidate_coord[0] - wp2[0], candidate_coord[1] - wp2[1])
    #         if dist < best_dist:
    #             best_candidate = candidate
    #             best_dist = dist

    #     if best_candidate is None:
    #         # According to your design, this should not happen.
    #         print("Error: No free home square available for captured piece", piece)
    #         return None, None

    #     # Convert the chosen candidate to its coordinates.
    #     final_coord = self.square_to_coords_ry(best_candidate)
        
    #     # Step 4: Generate a natural path from wp2 to final_coord.
    #     natural_segment = self.generate_natural_path(wp2, final_coord)
    #     # Build the overall path:
    #     #  - Segment 1: captured_coord -> wp1
    #     delta1 = (wp1[0] - captured_coord[0], wp1[1] - captured_coord[1])
    #     #  - Segment 2: wp1 -> wp2
    #     delta2 = (wp2[0] - wp1[0], wp2[1] - wp1[1])
    #     #  - Segment 3: from wp2 to final_coord using the relative moves from natural_segment.
    #     # natural_segment is assumed to be [wp2, rel_move1, rel_move2, ...]
    #     if len(natural_segment) < 2:
    #         # Fallback if generate_natural_path doesn't return relative moves.
    #         delta3 = (final_coord[0] - wp2[0], final_coord[1] - wp2[1])
    #         segment3 = [delta3]
    #     else:
    #         segment3 = natural_segment[1:]
        
    #     path = [captured_coord, delta1, delta2] + segment3
    #     return path, best_candidate





    
    def recover_captured_pieces(self, captured_pieces):
        """
        Processes a list of captured pieces and assigns each one a home coordinate
        based on its color using a LIFO (stack) order (the last captured piece is processed first).

        It works as follows:
        1. Two candidate coordinate patterns (for white and black) are defined.
        2. Current board occupancy is obtained from self.hall.sense_layer.get_squares_game()
            and converted to a dictionary using occupancy_list_to_dict.
        3. The captured_pieces list is iterated in reverse order.
        4. For each captured piece, the function checks the candidate coordinates in order.
            The first candidate found with occupancy value 0 (free) is assigned.
        5. The occupancy dictionary is updated immediately so that no two pieces are assigned to the same square.
        
        Returns:
        A dictionary mapping the assignment order (0 for the first piece processed, etc.)
        to a dictionary with the piece symbol and its assigned coordinate.
        """
        # Define candidate coordinate patterns.
        white_pattern = [
            (350,435), (350,410), (325,435), (325,410),
            (300,435), (300,410), (275,435), (275,410),
            (250,435), (250,410), (225,435), (225,410),
            (200,435), (200,410), (175,435), (175,410)
        ]
        black_pattern = [
            (0,435), (0,410), (25,435), (25,410),
            (50,435), (50,410), (75,435), (75,410),
            (100,435), (100,410), (125,435), (125,410),
            (150,435), (150,410), (175,435), (175,410)
        ]
        home_squares = {
            "K": ["e1"],
            "Q": ["d1"],
            "R": ["a1", "h1"],
            "B": ["c1", "f1"],
            "N": ["b1", "g1"],
            "P": ["a2", "b2", "c2", "d2", "e2", "f2", "g2", "h2"],
            "k": ["e8"],
            "q": ["d8"],
            "r": ["a8", "h8"],
            "b": ["c8", "f8"],
            "n": ["b8", "g8"],
            "p": ["a7", "b7", "c7", "d7", "e7", "f7", "g7", "h7"]
        }
        
        # Get current occupancy.
        occ = self.occupancy_list_to_dict(self.hall.sense_layer.get_squares_game())

        # white_count = self.count_capital_elements(captured_pieces)
        # black_count = len(captured_pieces) - white_count

        white_count = 0
        black_count = 0
        white_coords = []
        black_coords = []
                
        # Process captured pieces in reverse order (LIFO: newest first).
        for i, piece in enumerate((captured_pieces)):
            
            if piece.isupper():
                white_coords.append([piece, white_pattern[white_count]])
                white_count += 1
                #white
                white_x = 25

            else:
                black_coords.append([piece, black_pattern[black_count]])
                black_count += 1
               
        print(white_coords)
        print(reversed(white_coords))

        # Now we should have all the pieces with thier coordinates in a new list
        white_x = 25
        black_x = 325

        #white clear
        for i, piece in enumerate(reversed(white_coords)):
            symbol, coord = piece
            print(f"coords for {piece}: {coord}")
            path = [coord, (0, (375 - coord[1])), (white_x-coord[0], 0)]
            
            # Find the closest available square for the piece
            closest_square = None
            for square in home_squares.get(symbol, []):
                if occ.get(square, 1) == 0:  # Check if the square is unoccupied
                    closest_square = square
                    break

            if closest_square:
                print(f"Closest square for {symbol} is {closest_square}.")
                # Generate path to the closest square
                target_coords = self.square_to_coords_ry(closest_square)
                if closest_square[1] == '2':
                    path_end =  [(0, (target_coords[1] + 25) - 375), (+25, -25)]
                else:
                    path_end = [(0, (target_coords[1] + 25) - 375), (-25, -25)]
                
                # Update occupancy and move the piece
                occ[closest_square] = 1

                movements = self.gantry.parse_path_to_movement(path + path_end)
                commands = self.gantry.movement_to_gcode(movements)
                self.gantry.send_commands(commands)

        for i, piece in enumerate(reversed(black_coords)):
            symbol, coord = piece
            print(f"coords for {piece}: {coord}")
            path = [coord, (0, 375-coord[1]), (black_x - coord[0], 0)]
            
            # Find the closest available square for the piece
            closest_square = None
            for square in home_squares.get(symbol, []):
                if occ.get(square, 1) == 0:  # Check if the square is unoccupied
                    closest_square = square
                    
                    break

            if closest_square:
                print(f"Closest square for {symbol} is {closest_square}.")
                # Generate path to the closest square
                target_coords = self.square_to_coords_ry(closest_square)
                if closest_square[1] == '7':
                    path_end =  [(0, (target_coords[1] + 25) - 375), (- 25, -25)]
                else:
                    path_end = [(0, (target_coords[1] + 25)-375), (+ 25, -25)]
                
                # Update occupancy and move the piece
                occ[closest_square] = 1

                movements = self.gantry.parse_path_to_movement(path + path_end)
                commands = self.gantry.movement_to_gcode(movements)
                self.gantry.send_commands(commands)
    
    def count_capital_elements(array):
            """
            Count the number of capital elements in an array of strings.
            Each string is assumed to be a single character like "P" or "p".
            """
            return sum(1 for element in array if element.isupper())
    

    
    def recover_captured_piece_path(self, captured_coord, piece, occupancy):
        """
        Generates a movement path for a captured piece to re-enter the board.
        
        The plan is:
        1. From its stored coordinate (captured_coord), move vertically so that its y becomes 375.
        2. Then move horizontally so that its x becomes:
                25 for white pieces (uppercase) or 325 for black pieces (lowercase),
            while keeping y = 375.
        3. Then check the piece’s home squares (from a home_squares dictionary, which for our purposes
            is the same as standard starting positions). For each candidate home square, re-read occupancy
            (via self.hall.sense_layer.get_squares_game() and occupancy_list_to_dict); if one is free,
            choose that candidate.
        4. Generate a natural path from the second waypoint (wp2) to the candidate’s center.
        
        Returns a tuple (path, final_square), where:
        - path is a list: the first element is the absolute starting coordinate, followed by relative move segments.
        - final_square is the chosen home square (e.g., "e2") where the piece will finally be placed.
        
        It is assumed that occupancy is updated by calling self.hall.sense_layer.get_squares_game().
        """
        # Dictionary of home squares (same as standard starting positions)
        home_squares = {
            "K": ["e1"],
            "Q": ["d1"],
            "R": ["a1", "h1"],
            "B": ["c1", "f1"],
            "N": ["b1", "g1"],
            "P": ["a2", "b2", "c2", "d2", "e2", "f2", "g2", "h2"],
            "k": ["e8"],
            "q": ["d8"],
            "r": ["a8", "h8"],
            "b": ["c8", "f8"],
            "n": ["b8", "g8"],
            "p": ["a7", "b7", "c7", "d7", "e7", "f7", "g7", "h7"]
        }
        
        # Determine target x based on piece color.
        target_x = 25 if piece.isupper() else 325

        # Waypoint 1: Adjust y to 375 (vertical move), keep x unchanged.
        wp1 = (captured_coord[0], 375)
        # Waypoint 2: Move horizontally to target_x, keeping y = 375.
        wp2 = (target_x, 375)
        
        # Now, check the piece's home squares.
        candidate_found = None
        # Re-read occupancy for each candidate.
        for candidate in home_squares.get(piece, []):
            occ = self.occupancy_list_to_dict(self.hall.sense_layer.get_squares_game())
            if occ.get(candidate, 0) == 0:  # 0 indicates the square is free.
                candidate_found = candidate
                break
        
        if candidate_found is None:
            print("Error: No free home square found for captured piece", piece)
            return None, None

        # Convert the chosen candidate home square to coordinates.
        final_coord = self.square_to_coords_ry(candidate_found)
        
        # Generate a natural path from wp2 to the final coordinate.
        # We assume generate_natural_path returns a list with the first element equal to wp2,
        # then relative moves.
        natural_segment = self.generate_natural_path(wp2, final_coord)
        # Build the overall path:
        #   Segment 1: from captured_coord to wp1.
        delta1 = (wp1[0] - captured_coord[0], wp1[1] - captured_coord[1])
        #   Segment 2: from wp1 to wp2.
        delta2 = (wp2[0] - wp1[0], wp2[1] - wp1[1])
        #   Segment 3: from wp2 to final_coord, using the natural segment's relative moves (excluding the absolute starting point).
        # natural_segment is assumed to be [wp2, rel_move1, rel_move2, ...]
        if len(natural_segment) < 2:
            # Fallback in case generate_natural_path didn't return relative moves.
            delta3 = (final_coord[0] - wp2[0], final_coord[1] - wp2[1])
            segment3 = [delta3]
        else:
            segment3 = natural_segment[1:]
        
        # Construct the full path as a list: first element is captured_coord (absolute start),
        # then each subsequent element is a relative move.
        path = [captured_coord, delta1, delta2] + segment3
        return path, candidate_found





    # def reset_board_to_home(self, current_fen):
    #     """
    #     Resets the board from the current configuration (given by current_fen)
    #     to the standard home positions.
        
    #     This function:
    #     1. Parses the current FEN to obtain a mapping of squares to pieces.
    #     2. Uses a starting_positions dictionary to define home squares for each piece.
    #     3. Iterates through the pieces and, for each piece, re-reads occupancy
    #         (via self.hall.sense_layer.get_squares_game() and occupancy_list_to_dict)
    #         to check if any candidate home square for that piece is free (occupancy==0).
    #     4. If a free candidate is found, it generates a natural path (via generate_natural_path)
    #         from the piece's current square to that candidate and “moves” the piece.
    #     5. If not, the piece is delayed for later processing.
    #     6. The process repeats until no further moves can be made.
        
    #     Returns:
    #     A dictionary mapping the original square (from which the piece moved) to a move plan.
    #     Each move plan is a dictionary with:
    #         - "piece": the piece symbol,
    #         - "final_square": the chosen home square,
    #         - "path": a list with the absolute starting coordinate followed by relative moves.
    #     """
    #     # Define standard starting positions for each piece.
    #     starting_positions = {
    #         "K": ["e1"],
    #         "Q": ["d1"],
    #         "R": ["a1", "h1"],
    #         "B": ["c1", "f1"],
    #         "N": ["b1", "g1"],
    #         "P": ["a2", "b2", "c2", "d2", "e2", "f2", "g2", "h2"],
    #         "k": ["e8"],
    #         "q": ["d8"],
    #         "r": ["a8", "h8"],
    #         "b": ["c8", "f8"],
    #         "n": ["b8", "g8"],
    #         "p": ["a7", "b7", "c7", "d7", "e7", "f7", "g7", "h7"]
    #     }
        
    #     # Parse the current board FEN.
    #     current_mapping = self.parse_fen(current_fen)
        
    #     # Create a full list of board squares.
    #     board_squares = [f + str(r) for r in range(8, 0, -1) for f in "abcdefgh"]
        
    #     # (We don't update occupancy; each check will use the hall sensor.)
    #     # Initialize move plans and a delayed moves dictionary.
    #     move_paths = {}
    #     delayed_moves = {}
        
    #     progress = True
    #     while progress:
    #         progress = False
    #         # Process each piece in the current mapping.
    #         for square, piece in list(current_mapping.items()):
    #             # Skip if the piece is already in one of its home squares.
    #             if square in starting_positions.get(piece, []):
    #                 continue

    #             # For this piece, get its candidate home squares.
    #             candidates = starting_positions.get(piece, [])
    #             chosen = None
    #             # For each candidate, re-read occupancy to see if it's free.
    #             for candidate in candidates:
    #                 occ = self.occupancy_list_to_dict(self.hall.sense_layer.get_squares_game())
    #                 if occ.get(candidate, 0) == 0:
    #                     chosen = candidate
    #                     break
    #             if chosen:
    #                 # Generate the natural path from current square to the chosen candidate.
    #                 start_coords = self.square_to_coords_ry(square)
    #                 dest_coords = self.square_to_coords_ry(chosen)
    #                 path = self.generate_natural_path(start_coords, dest_coords)
    #                 move_paths[square] = {
    #                     "piece": piece,
    #                     "final_square": chosen,
    #                     "path": path
    #                 }
    #                 # "Move" the piece by updating current_mapping.
    #                 current_mapping[chosen] = piece
    #                 del current_mapping[square]
    #                 progress = True
    #             else:
    #                 # No candidate free; delay this piece.
    #                 delayed_moves[square] = piece
            
    #         # Process delayed moves.
    #         for square, piece in list(delayed_moves.items()):
    #             candidates = starting_positions.get(piece, [])
    #             chosen = None
    #             for candidate in candidates:
    #                 occ = self.occupancy_list_to_dict(self.hall.sense_layer.get_squares_game())
    #                 if occ.get(candidate, 0) == 0:
    #                     chosen = candidate
    #                     break
    #             if chosen:
    #                 start_coords = self.square_to_coords_ry(square)
    #                 dest_coords = self.square_to_coords_ry(chosen)
    #                 path = self.generate_natural_path(start_coords, dest_coords)
    #                 move_paths[square] = {
    #                     "piece": piece,
    #                     "final_square": chosen,
    #                     "path": path
    #                 }
    #                 current_mapping[chosen] = piece
    #                 del current_mapping[square]
    #                 del delayed_moves[square]
    #                 progress = True
    #         # Loop until no further moves can be made.
        
    #     if delayed_moves:
    #         print("The following moves remain delayed (no home square free):", delayed_moves)
        
    #     return move_paths
    
    def captured_piece_return(self, captured_pieces):



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
    
    def recover_captured_piece_path(self, captured_coord, piece):
        """
        Generates a movement path for a captured piece to re-enter the board.
        
        The plan is:
        1. From its stored coordinate (captured_coord), move so that its y becomes 375.
        2. Then move horizontally so that its x becomes 25 (for white pieces, uppercase)
            or 325 (for black pieces, lowercase) while keeping y = 375.
        3. Then slide vertically (in steps of -50 in y) until an unoccupied board square is found.
            (Board-square centers are at y = 350, 300, 250, ... down to 0.)
        
        This version continuously re-reads occupancy from the hall-effect sensors so that newly 
        occupied squares are immediately taken into account.
        
        Returns a tuple (path, final_square), where:
        - path is a list in the format: [absolute start, relative move1, relative move2, relative move3].
        - final_square is the board square (e.g., "e4") where the piece will finally be placed.
        
        The occupancy is updated continuously by calling self.hall.sense_layer.get_squares_game() and 
        converting it via self.occupancy_list_to_dict.
        """

        # occupancy = 

        # Determine target x based on piece color.
        target_x = 25 if piece.isupper() else 325

        # Waypoint 1: Set y to 375 while keeping x unchanged.
        wp1 = (captured_coord[0], 375)
        # Waypoint 2: Move horizontally to target_x (keeping y = 375).
        wp2 = (target_x, 375)

        # Now, slide vertically downward (in 50-unit steps) until an unoccupied square is found.
        candidate_y = 350  # Start with the highest board square center.
        final_coord = None
        final_square = None

        while candidate_y >= 0:
            # Re-fetch occupancy continuously.
            occupancy = self.occupancy_list_to_dict(self.hall.sense_layer.get_squares_game())
            candidate_coord = (target_x, candidate_y)
            square_candidate = self.coords_to_square_ry(candidate_coord)
            if occupancy.get(square_candidate) == 0:
                final_coord = candidate_coord
                final_square = square_candidate
                break
            candidate_y -= 50

        if final_coord is None:
            print("No available board square for captured piece", piece)
            return None, None

        # Build the path:
        # Move 1: captured_coord -> wp1
        delta1 = (wp1[0] - captured_coord[0], wp1[1] - captured_coord[1])
        # Move 2: wp1 -> wp2
        delta2 = (wp2[0] - wp1[0], wp2[1] - wp1[1])
        # Move 3: wp2 -> final_coord
        delta3 = (final_coord[0] - wp2[0], final_coord[1] - wp2[1])

        path = [captured_coord, delta1, delta2, delta3]
        return path, final_square




        # 








    
    def sign(self, x):
        if x < 0:
            return -1
        elif x > 0:
            return 1
        else:
            return 0


    def generate_natural_path(self, start, dest):
        """
        Generates a natural L-shaped path from the center of the start square to the center of the destination square.
        The piece exits its starting square through the corner in the direction of travel and enters the destination square
        through the corresponding corner.
        
        If the movement is strictly lateral or vertical, the piece will default to moving toward the board's center.
        
        Parameters:
        start: (x, y) coordinates of the center of the starting square.
        dest: (x, y) coordinates of the center of the destination square.
        
        Returns:
        A list where the first element is the absolute starting coordinate and subsequent elements are relative moves.
        """

        print(start)
        print(dest)
        start_x, start_y = start
        dest_x, dest_y = dest

        # Compute differences.
        dx = dest_x - start_x
        dy = dest_y - start_y

        # Determine horizontal direction.
        sign_x = self.sign(dx)
        sign_y = self.sign(dy)

        temp_x = (sign_x, sign_x)
        temp_y = (sign_y, sign_y)

        if sign_x == 0:
            if start_x > 180:
                temp_x = (-1, 1)
            else: 
                temp_x = (1, -1)


        if sign_y == 0:
            temp_y = (1, -1)
        
        

        # if sign_x == 0:
        #     # For lateral moves, default to moving toward board center in x.
        #     temp_x = 1 if start_x < 175 else -1

        # Determine vertical direction.
        # if dy > 0:
        #     sign_y = 1
        # elif dy < 0:
        #     sign_y = -1
        # else:
        #     # For vertical moves, default to moving toward board center in y.
        #     sign_y = 1 if start_y < 175 else -1

        # Exit corner for the start square: offset by 25 in the chosen directions.
        exit_corner = (25 * temp_x[0], 25 * temp_y[0])

        move_to_square = [(dx -50 * sign_x, 0), (0, dy -  50 * sign_y)]
        # Entry corner for the destination square: offset from the destination center.
        entry_corner = (25 * temp_x[1], 25 * temp_y[1])

        # # Define waypoints:
        P0 = (start_x, start_y)        # Start center.
        # P1 = exit_corner               # Exit corner of the start square.
        # P2 = entry_corner              # Entry corner of the destination square.
        # P3 = (dest_x, dest_y)          # Destination center.

        # # Compute relative moves between waypoints.
        # waypoints = [P0, P1, P2, P3]
        # relative_moves = []
        # for i in range(1, len(waypoints)):
        #     prev = waypoints[i - 1]
        #     curr = waypoints[i]
        #     delta = (curr[0] - prev[0], curr[1] - prev[1])
        #     relative_moves.append(delta)

        return [P0, exit_corner] +  move_to_square + [entry_corner]


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
            start_safe_y = self.safe_file(start_y + offset, start_y)
            dest_safe_y = self.safe_file(dest_y - offset, dest_y)
        else:
            start_safe_y = self.safe_file(start_y - offset, start_y)
            dest_safe_y = self.safe_file(dest_y + offset, dest_y)

        # Vertical (rank) movement: adjust the x coordinate.
        if dest_x > start_x:
            start_safe_x = self.safe_rank(start_x + offset)
            dest_safe_x = self.safe_rank(dest_x - offset)
        else:
            start_safe_x = self.safe_rank(start_x - offset)
            dest_safe_x = self.safe_rank(dest_x + offset)

        # Define waypoints:
        P0 = (start_x, start_y)
        P1 = (start_x, start_safe_y)
        P2 = (dest_safe_x, start_safe_y)
        P3 = (dest_safe_x, dest_safe_y)
        P4 = (dest_x, dest_y)

        waypoints = [P0, P1, P2, P3, P4]

        relative_moves = []
        for i in range(1, len(waypoints)):
            prev = waypoints[i - 1]
            curr = waypoints[i]
            delta = (curr[0] - prev[0], curr[1] - prev[1])
            relative_moves.append(delta)

        return [P0] + relative_moves

    def parse_fen(self, fen):
        """
        Parses a FEN string and returns a dictionary mapping board squares
        (e.g., "e4") to piece characters.
        
        FEN rows are processed from rank 8 to rank 1.
        """
        board = {}
        fen_rows = fen.split()[0].split('/')
        for i, row in enumerate(fen_rows):
            rank = 8 - i  # rows: 0->rank8, 7->rank1
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
        - x: rank coordinate, with rank 1 at x=0 and rank 8 at x=350.
        - y: file coordinate, with file h at y=0 and file a at y=350.
        
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

    def occupancy_list_to_dict(self, occ_list):
        """
        Converts an 8x8 occupancy list into a dictionary mapping board squares
        (e.g., "a8", "b8", …, "h1") to occupancy values (1 for occupied, 0 for empty).
        
        Assumes:
        - occ_list is a list of 8 lists.
        - The first inner list corresponds to rank 8,
            the second to rank 7, …, and the last to rank 1.
        - Within each inner list, the first element corresponds to file a, etc.
        """
        occ_dict = {}
        for i, row in enumerate(occ_list):
            rank = i + 1 
            for j, val in enumerate(row):
                file_letter = chr(ord('a') + j)
                square = file_letter + str(rank)
                occ_dict[square] = val
        return occ_dict

    def plan_board_reset(self, current_fen, target_fen, piece_alternatives):
        """
        Plans moves to reset the board from a current configuration to a target configuration,
        using an externally provided occupancy list for candidate selection.
        
        This version matches pieces by type and processes the moves in two passes.
        In the first pass, all pieces except the king and queen are assigned target squares.
        In the second pass, the king and queen are processed last to minimize conflicts.
        If no candidate square is available for a piece, its move is delayed for later processing.
        
        The occupancy is obtained from the hall-effect sensors (self.hall.sense_layer.get_squares_game())
        and converted via occupancy_list_to_dict.
        
        Returns a dictionary mapping the current square (for pieces that need to move)
        to a move plan. Each move plan includes:
        - "piece": the piece character
        - "final_square": the target square
        - "path": a list starting with the absolute starting coordinate followed by relative moves.
        """
        # Parse FEN strings.
        current_mapping = self.parse_fen(current_fen)
        target_mapping = self.parse_fen(target_fen)
        
        # # Build a dictionary: piece letter -> list of target squares from target configuration.
        # target_positions = {}
        # for square, piece in target_mapping.items():
        #     target_positions.setdefault(piece, []).append(square)
        
        # Get occupancy from the hall-effect sensors and convert to dictionary.
        target_occupancy = self.occupancy_list_to_dict(self.hall.sense_layer.get_squares_game())
        
        move_paths = {}
        delayed_moves = {}  # For pieces with no available square on first try.

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
                # Filter out candidates that equal the current square or are already occupied.
                candidates = [sq for sq in candidates if sq != square and target_occupancy.get(sq, 0) == 0]

                # Add alternatives from piece_alternatives if available.
                if square in piece_alternatives:
                    alt_candidates = [sq for sq in piece_alternatives[square] if target_occupancy.get(sq, 0) == 0]
                    candidates.extend(alt_candidates)
                
                chosen = self.select_target_square(piece, candidates, target_occupancy)
                if chosen is None:
                    # No candidate available now; mark this move as delayed.
                    delayed_moves[square] = piece
                    continue
                
                # Mark the chosen square as occupied.
                target_occupancy[chosen] = 1
                start_coords = self.square_to_coords_ry(square)
                dest_coords = self.square_to_coords_ry(chosen)
                path = self.generate_path(start_coords, dest_coords, offset=25)
                move_paths[square] = {
                    "piece": piece,
                    "final_square": chosen,
                    "path": path
                }

        # Process non-king/queen pieces.
        process_pieces(first_pass)
        # Process king and queen.
        process_pieces(second_pass)

        # Now try processing delayed moves repeatedly until no further progress is made.
        progress = True
        while delayed_moves and progress:
            progress = False
            # Make a copy of delayed_moves to iterate over.
            for square, piece in list(delayed_moves.items()):
                candidates = target_positions.get(piece, [])
                candidates = [sq for sq in candidates if sq != square and target_occupancy.get(sq, 0) == 0]
                if square in piece_alternatives:
                    alt_candidates = [sq for sq in piece_alternatives[square] if target_occupancy.get(sq, 0) == 0]
                    candidates.extend(alt_candidates)
                chosen = self.select_target_square(piece, candidates, target_occupancy)
                if chosen is not None:
                    target_occupancy[chosen] = 1
                    start_coords = self.square_to_coords_ry(square)
                    dest_coords = self.square_to_coords_ry(chosen)
                    path = self.generate_path(start_coords, dest_coords, offset=25)
                    move_paths[square] = {
                        "piece": piece,
                        "final_square": chosen,
                        "path": path
                    }
                    del delayed_moves[square]
                    progress = True
        # If some moves remain delayed, they can be handled later.
        if delayed_moves:
            print("The following moves remain delayed due to lack of available squares:")
            for square, piece in delayed_moves.items():
                print(f"Piece {piece} from {square}")

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
    

    def plan_captured_piece_recovery(self, captured_pieces):
        """
        Processes a list of captured pieces and generates recovery move plans for each.
        
        The function first sorts the captured pieces into white and black based on the case of the symbol.
        It then assigns stored endzone coordinates from a fixed alternating pattern:
        
        For white pieces (stored off-board on the right):
            Pattern: (350,435), (350,410), (325,435), (325,410), (300,435), (300,410), (275,435), (275,410),
                    (250,435), (250,410), (225,435), (225,410), (200,435), (200,410), (175,435), (175,410)
        For black pieces (stored off-board on the left):
            Pattern: (0,435), (0,410), (25,435), (25,410), (50,435), (50,410), (75,435), (75,410),
                    (100,435), (100,410), (125,435), (125,410), (150,435), (150,410), (175,435), (175,410)
        
        For each captured piece, the function calls recover_captured_piece_path to generate a path.
        If no board square is available (final_square is None), that move is delayed for later processing.
        
        The occupancy is re‑fetched from the hall‑effect sensors continuously so that recovered pieces
        are immediately reflected in the occupancy data.
        
        Returns two dictionaries (one for white and one for black) mapping an index (order) to the recovery plan.
        Each recovery plan includes:
        - "piece": the piece symbol,
        - "start_coord": the stored coordinate (in the endzone),
        - "final_square": the board square where it will be placed,
        - "path": the movement path.
        """
        # Define stored coordinate patterns.
        white_pattern = [
            (350,435), (350,410), (325,435), (325,410),
            (300,435), (300,410), (275,435), (275,410),
            (250,435), (250,410), (225,435), (225,410),
            (200,435), (200,410), (175,435), (175,410)
        ]
        black_pattern = [
            (0,435), (0,410), (25,435), (25,410),
            (50,435), (50,410), (75,435), (75,410),
            (100,435), (100,410), (125,435), (125,410),
            (150,435), (150,410), (175,435), (175,410)
        ]
        
        white_moves = {}
        black_moves = {}
        delayed_white = {}  # key: index, value: (piece, stored_coord)
        delayed_black = {}
        
        white_index = 0
        black_index = 0

        # Initial pass: Process each captured piece.
        for i, piece in enumerate(captured_pieces):
            # Continuously fetch current occupancy.
            occupancy = self.occupancy_list_to_dict(self.hall.sense_layer.get_squares_game())
            if piece.isupper():
                stored_coord = white_pattern[white_index % len(white_pattern)]
                white_index += 1
                path, final_square = self.recover_captured_piece_path(stored_coord, piece, occupancy)
                if final_square is None:
                    delayed_white[i] = (piece, stored_coord)
                else:
                    white_moves[i] = {
                        "piece": piece,
                        "start_coord": stored_coord,
                        "final_square": final_square,
                        "path": path
                    }
                    # Immediately update occupancy.
                    occupancy[final_square] = piece
            else:
                stored_coord = black_pattern[black_index % len(black_pattern)]
                black_index += 1
                path, final_square = self.recover_captured_piece_path(stored_coord, piece, occupancy)
                if final_square is None:
                    delayed_black[i] = (piece, stored_coord)
                else:
                    black_moves[i] = {
                        "piece": piece,
                        "start_coord": stored_coord,
                        "final_square": final_square,
                        "path": path
                    }
                    occupancy[final_square] = piece

        # Reattempt delayed moves until no further progress is made.
        progress = True
        while (delayed_white or delayed_black) and progress:
            progress = False
            # Always re-fetch occupancy before each reattempt.
            occupancy = self.occupancy_list_to_dict(self.hall.sense_layer.get_squares_game())
            for i, (piece, stored_coord) in list(delayed_white.items()):
                path, final_square = self.recover_captured_piece_path(stored_coord, piece, occupancy)
                if final_square is not None:
                    white_moves[i] = {
                        "piece": piece,
                        "start_coord": stored_coord,
                        "final_square": final_square,
                        "path": path
                    }
                    del delayed_white[i]
                    occupancy[final_square] = piece
                    progress = True
            for i, (piece, stored_coord) in list(delayed_black.items()):
                path, final_square = self.recover_captured_piece_path(stored_coord, piece, occupancy)
                if final_square is not None:
                    black_moves[i] = {
                        "piece": piece,
                        "start_coord": stored_coord,
                        "final_square": final_square,
                        "path": path
                    }
                    del delayed_black[i]
                    occupancy[final_square] = piece
                    progress = True

        if delayed_white or delayed_black:
            print("The following captured piece recoveries remain delayed due to lack of available board squares:")
            for i, (piece, stored_coord) in delayed_white.items():
                print(f"White piece {piece} stored at {stored_coord}")
            for i, (piece, stored_coord) in delayed_black.items():
                print(f"Black piece {piece} stored at {stored_coord}")

        return white_moves, black_moves
    
    # def coords_to_square_ry(self, coord):
    #     """
    #     Converts physical coordinates (assumed to be board-center values in multiples of 50)
    #     to a board square (e.g., "e4"). 
    #     Assumes:
    #     - x (rank coordinate): 0 corresponds to rank 1, 350 to rank 8.
    #     - y (file coordinate): 0 corresponds to file h, 350 to file a.
    #     """
    #     x, y = coord
    #     rank = int(x / 50) + 1
    #     file_index = 7 - int(y / 50)
    #     file_letter = chr(ord('a') + file_index)
    #     return file_letter + str(rank)
    
    def recover_captured_piece_path(self, captured_coord, piece, occupancy):
        """
        Generates a movement path for a captured piece to re-enter the board.
        
        The plan is:
        1. From its stored coordinate (captured_coord), move so that its y becomes 375.
        2. Then move horizontally so that its x becomes 25 (for white pieces, uppercase)
            or 325 (for black pieces, lowercase) while keeping y = 375.
        3. Then slide vertically (in steps of -50 in y) until an unoccupied board square is found.
            (Board-square centers are at y = 350, 300, 250, ... down to 0.)
        
        This version continuously re-reads occupancy from the hall-effect sensors so that newly 
        occupied squares are immediately taken into account.
        
        Returns a tuple (path, final_square), where:
        - path is a list in the format: [absolute start, relative move1, relative move2, relative move3].
        - final_square is the board square (e.g., "e4") where the piece will finally be placed.
        
        The occupancy is updated continuously by calling self.hall.sense_layer.get_squares_game() and 
        converting it via self.occupancy_list_to_dict.
        """
        # Determine target x based on piece color.
        target_x = 25 if piece.isupper() else 325

        # Waypoint 1: Set y to 375 while keeping x unchanged.
        wp1 = (captured_coord[0], 375)
        # Waypoint 2: Move horizontally to target_x (keeping y = 375).
        wp2 = (target_x, 375)

        # Now, slide vertically downward (in 50-unit steps) until an unoccupied square is found.
        candidate_y = 350  # Start with the highest board square center.
        final_coord = None
        final_square = None

        while candidate_y >= 0:
            # Re-fetch occupancy continuously.
            occupancy = self.occupancy_list_to_dict(self.hall.sense_layer.get_squares_game())
            candidate_coord = (target_x, candidate_y)
            square_candidate = self.coords_to_square_ry(candidate_coord)
            if occupancy.get(square_candidate) == 0:
                final_coord = candidate_coord
                final_square = square_candidate
                break
            candidate_y -= 50

        if final_coord is None:
            print("No available board square for captured piece", piece)
            return None, None

        # Build the path:
        # Move 1: captured_coord -> wp1
        delta1 = (wp1[0] - captured_coord[0], wp1[1] - captured_coord[1])
        # Move 2: wp1 -> wp2
        delta2 = (wp2[0] - wp1[0], wp2[1] - wp1[1])
        # Move 3: wp2 -> final_coord
        delta3 = (final_coord[0] - wp2[0], final_coord[1] - wp2[1])

        path = [captured_coord, delta1, delta2, delta3]
        return path, final_square



    

    # def clamp(self, value, minimum, maximum):
    #     """Clamp the value between minimum and maximum."""
    #     return max(minimum, min(value, maximum))

    # def safe_rank(self, x):
    #     """
    #     Returns a safe intermediate x coordinate (for rank movement)
    #     ensuring that x is between 25 and 325.
    #     """
    #     return self.clamp(x, 25, 325)

    # def safe_file(self, y, center):
    #     """
    #     Returns a safe intermediate y coordinate (for file movement).
    #     For most files, y is clamped between 25 and 325.
    #     However, if the square’s center is at 350 (file a), then 350 is allowed.
    #     """
    #     if center == 350:
    #         return self.clamp(y, 25, 350)
    #     else:
    #         return self.clamp(y, 25, 325)

    # def generate_path(self, start, dest, offset=25):
    #     """
    #     Generates an L-shaped, collision-free path from start to dest.
        
    #     Coordinate system:
    #     - x: rank coordinate (0 at rank 1 up to 350 at rank 8)
    #     - y: file coordinate (0 at file h up to 350 at file a)
        
    #     Returns a list where:
    #     - The first element is the absolute starting coordinate.
    #     - Each subsequent element is a relative move (delta_x, delta_y)
    #         representing the movement from the previous waypoint.
    #     """
    #     start_x, start_y = start
    #     dest_x, dest_y = dest

    #     # Horizontal (file) movement: adjust the y coordinate.
    #     if dest_y > start_y:
    #         # Moving in the positive y direction (toward file a)
    #         start_safe_y = self.safe_file(start_y + offset, start_y)
    #         dest_safe_y = self.safe_file(dest_y - offset, dest_y)
    #     else:
    #         # Moving in the negative y direction (toward file h)
    #         start_safe_y = self.safe_file(start_y - offset, start_y)
    #         dest_safe_y = self.safe_file(dest_y + offset, dest_y)

    #     # Vertical (rank) movement: adjust the x coordinate.
    #     if dest_x > start_x:
    #         # Moving upward (from rank 1 to rank 8)
    #         start_safe_x = self.safe_rank(start_x + offset)
    #         dest_safe_x = self.safe_rank(dest_x - offset)
    #     else:
    #         # Moving downward (from a higher rank to a lower rank)
    #         start_safe_x = self.safe_rank(start_x - offset)
    #         dest_safe_x = self.safe_rank(dest_x + offset)

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

    # def parse_fen(self, fen):
    #     """
    #     Parses a FEN string and returns a dictionary mapping board squares (e.g., "e4")
    #     to piece characters (e.g., "P", "n", etc.).
        
    #     FEN rows are processed from rank 8 to rank 1.
    #     """
    #     board = {}
    #     fen_rows = fen.split()[0].split('/')
    #     for i, row in enumerate(fen_rows):
    #         rank = 8 - i  # ranks 8 to 1
    #         file_index = 0
    #         for ch in row:
    #             if ch.isdigit():
    #                 file_index += int(ch)
    #             else:
    #                 file_letter = chr(ord('a') + file_index)
    #                 square = file_letter + str(rank)
    #                 board[square] = ch
    #                 file_index += 1
    #     return board

    # def square_to_coords_ry(self, square):
    #     """
    #     Converts a board square (e.g., "h1" or "a8") to physical coordinates.
        
    #     Coordinate system:
    #     - x: rank coordinate, with rank 1 at x = 0 and rank 8 at x = 350.
    #     - y: file coordinate, with file h at y = 0 and file a at y = 350.
        
    #     For example:
    #     "h1" -> (0, 0)
    #     "a8" -> (350, 350)
    #     """
    #     file_letter = square[0]
    #     rank_digit = int(square[1])
    #     x = (rank_digit - 1) * 50
    #     file_index = ord(file_letter) - ord('a')
    #     y = (7 - file_index) * 50
    #     return (x, y)

    # def select_target_square(self, piece, candidates, occupancy):
    #     """
    #     Given a piece and a list of candidate target squares, returns the first candidate
    #     that is not yet occupied.
    #     """
    #     for candidate in candidates:
    #         if occupancy.get(candidate) is None:
    #             return candidate
    #     return None

    # # # Define alternatives for pieces that might have more than one acceptable target.
    # # # For non-pawn pieces (example for rooks, knights, bishops):
    # # piece_alternatives = {
    # #     # White pieces alternatives
    # #     "a1": ["h1"],
    # #     "h1": ["a1"],
    # #     "b1": ["g1"],
    # #     "g1": ["b1"],
    # #     "c1": ["f1"],
    # #     "f1": ["c1"],
    # #     # Black pieces alternatives
    # #     "a8": ["h8"],
    # #     "h8": ["a8"],
    # #     "b8": ["g8"],
    # #     "g8": ["b8"],
    # #     "c8": ["f8"],
    # #     "f8": ["c8"],
    # # }

    # # # Automatically fill out pawn alternatives for all possible pawn squares.
    # # white_pawn_squares = ["a2", "b2", "c2", "d2", "e2", "f2", "g2", "h2"]
    # # black_pawn_squares = ["a7", "b7", "c7", "d7", "e7", "f7", "g7", "h7"]

    # # for square in white_pawn_squares:
    # #     piece_alternatives[square] = [s for s in white_pawn_squares if s != square]

    # # for square in black_pawn_squares:
    # #     piece_alternatives[square] = [s for s in black_pawn_squares if s != square]

    # # def plan_board_reset(self, current_fen, target_fen, piece_alternatives):
    # #     """
    # #     Plans moves to reset the board from a current configuration to a target configuration.
        
    # #     This version matches pieces by type and processes the moves in two passes.
    # #     In the first pass, all pieces except the king and queen are assigned target squares.
    # #     In the second pass, the king and queen are processed last to minimize conflicts.
        
    # #     Returns a dictionary mapping the current square (for pieces that need to move)
    # #     to a move plan. Each move plan includes:
    # #     - "piece": the piece character
    # #     - "final_square": the target square
    # #     - "path": a list starting with the absolute starting coordinate followed by relative moves.
    # #     """
    # #     current_mapping = self.parse_fen(current_fen)
    # #     target_mapping = self.parse_fen(target_fen)
        
    # #     # Build a dictionary: piece letter -> list of squares from target configuration.
    # #     target_positions = {}
    # #     for square, piece in target_mapping.items():
    # #         target_positions.setdefault(piece, []).append(square)
        
    # #     # Occupancy for target squares (initially all free)
    # #     target_occupancy = {square: None for square in target_mapping.keys()}
        
    # #     move_paths = {}

    # #     # Split pieces into two groups: non-king/queen and king/queen.
    # #     first_pass = {}
    # #     second_pass = {}
    # #     for square, piece in current_mapping.items():
    # #         if piece.upper() in ('K', 'Q'):
    # #             second_pass[square] = piece
    # #         else:
    # #             first_pass[square] = piece

    # #     # Helper function to process a given mapping.
    # #     def process_pieces(mapping):
    # #         for square, piece in mapping.items():
    # #             # Skip if already correctly placed.
    # #             if square in target_mapping and target_mapping[square] == piece:
    # #                 continue

    # #             # Get candidate target squares for this piece type.
    # #             candidates = target_positions.get(piece, [])
    # #             # Remove candidates that are the same as the current square or already occupied.
    # #             candidates = [sq for sq in candidates if sq != square and target_occupancy.get(sq) is None]
                
    # #             # Add alternatives from the piece_alternatives dictionary if available.
    # #             if square in piece_alternatives:
    # #                 candidates.extend(piece_alternatives[square])
                
    # #             chosen = self.select_target_square(piece, candidates, target_occupancy)
    # #             if chosen is None:
    # #                 print(f"No available target square for {piece} from {square}")
    # #                 continue
                
    # #             target_occupancy[chosen] = piece
                
    # #             start_coords = self.square_to_coords_ry(square)
    # #             dest_coords = self.square_to_coords_ry(chosen)
    # #             path = self.generate_path(start_coords, dest_coords, offset=25)
                
    # #             move_paths[square] = {
    # #                 "piece": piece,
    # #                 "final_square": chosen,
    # #                 "path": path
    # #             }
        
    # #     # Process first all non-king/queen pieces.
    # #     process_pieces(first_pass)
    # #     # Then process the king and queen.
    # #     process_pieces(second_pass)
        
    # #     return move_paths

    # # def occupancy_list_to_dict(occ_list):
    # #     """
    # #     Converts an 8x8 occupancy list into a dictionary mapping board squares
    # #     (e.g., "a8", "b8", …, "h1") to occupancy values (1 for occupied, 0 for empty).
        
    # #     Assumptions:
    # #     - occ_list is a list of 8 lists.
    # #     - The first inner list corresponds to rank 8,
    # #         the second to rank 7, …, and the last to rank 1.
    # #     - Within each inner list, the first element corresponds to file a,
    # #         the second to file b, …, and the last to file h.
    # #     """
    # #     occ_dict = {}
    # #     for i, row in enumerate(occ_list):
    # #         rank = 8 - i  # first row is rank 8, last row is rank 1.
    # #         for j, val in enumerate(row):
    # #             file_letter = chr(ord('a') + j)
    # #             square = file_letter + str(rank)
    # #             occ_dict[square] = val
    # #     return occ_dict

    # def plan_board_reset(self, current_fen, target_fen, piece_alternatives):
    #     """
    #     Plans moves to reset the board from a current configuration to a target configuration,
    #     using an externally provided occupancy list for candidate selection.
        
    #     This version matches pieces by type and processes the moves in two passes.
    #     In the first pass, all pieces except the king and queen are assigned target squares.
    #     In the second pass, the king and queen are processed last to minimize conflicts.
        
    #     The occupancy is provided as an 8x8 list (each inner list representing a rank starting from file a),
    #     which is converted to a dictionary mapping squares to 0 (empty) or 1 (occupied).
        
    #     Returns a dictionary mapping the current square (for pieces that need to move)
    #     to a move plan. Each move plan includes:
    #     - "piece": the piece character
    #     - "final_square": the target square
    #     - "path": a list starting with the absolute starting coordinate followed by relative moves.
    #     """
    #     # Parse FEN strings.
    #     current_mapping = self.parse_fen(current_fen)
    #     target_mapping = self.parse_fen(target_fen)
        
    #     # Build a dictionary: piece letter -> list of squares from target configuration.
    #     target_positions = {}
    #     for square, piece in target_mapping.items():
    #         target_positions.setdefault(piece, []).append(square)
        
    #     # Convert the provided occupancy list into a dictionary.
    #     target_occupancy = self.occupancy_list_to_dict(self.hall.sense_layer.get_squares_game())
    #     # (target_occupancy now holds keys for all board squares with values 0 or 1.)
        
    #     move_paths = {}

    #     # Split pieces into two groups: non-king/queen and king/queen.
    #     first_pass = {}
    #     second_pass = {}
    #     for square, piece in current_mapping.items():
    #         if piece.upper() in ('K', 'Q'):
    #             second_pass[square] = piece
    #         else:
    #             first_pass[square] = piece

    #     def process_pieces(mapping):
    #         for square, piece in mapping.items():
    #             # Skip if already correctly placed.
    #             if square in target_mapping and target_mapping[square] == piece:
    #                 continue

    #             # Get candidate target squares for this piece type.
    #             candidates = target_positions.get(piece, [])
    #             # Remove candidates that are the same as the current square or already occupied.
    #             # Here, a square is available only if target_occupancy[sq] == 0.
    #             candidates = [sq for sq in candidates if sq != square and target_occupancy.get(sq, 0) == 0]
                
    #             # Add alternatives from the piece_alternatives dictionary if available.
    #             if square in piece_alternatives:
    #                 # Also filter alternatives by occupancy.
    #                 alt_candidates = [sq for sq in piece_alternatives[square] if target_occupancy.get(sq, 0) == 0]
    #                 candidates.extend(alt_candidates)
                
    #             chosen = self.select_target_square(piece, candidates, target_occupancy)
    #             if chosen is None:
    #                 print(f"No available target square for {piece} from {square}")
    #                 continue
                
    #             # Mark the chosen square as occupied (set to 1).
    #             target_occupancy[chosen] = 1
                
    #             start_coords = self.square_to_coords_ry(square)
    #             dest_coords = self.square_to_coords_ry(chosen)
    #             path = self.generate_path(start_coords, dest_coords, offset=25)
                
    #             move_paths[square] = {
    #                 "piece": piece,
    #                 "final_square": chosen,
    #                 "path": path
    #             }
        
    #     # Process non-king/queen pieces first.
    #     process_pieces(first_pass)
    #     # Then process the king and queen.
    #     process_pieces(second_pass)
        
    #     return move_paths
    


    # def coords_to_square_ry(self, coord):
    #     """
    #     Converts physical coordinates (assumed to be board-center values in multiples of 50)
    #     to a board square (e.g., "e4"). 
    #     Assumes:
    #     - x (rank coordinate): 0 corresponds to rank 1, 350 to rank 8.
    #     - y (file coordinate): 0 corresponds to file h, 350 to file a.
    #     """
    #     x, y = coord
    #     rank = int(x / 50) + 1
    #     file_index = 7 - int(y / 50)
    #     file_letter = chr(ord('a') + file_index)
    #     return file_letter + str(rank)

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
            square_candidate = self.coords_to_square_ry(candidate_coord)
            if occupancy.get(square_candidate) == 0:
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
    #         # Reverse the rank allocation: row 0 becomes rank 8, row 1 rank 7, etc.
    #         rank = 8 - i
    #         for j, val in enumerate(row):
    #             file_letter = chr(ord('a') + j)
    #             square = file_letter + str(rank)
    #             occ_dict[square] = val
    #     return occ_dict
                

        
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



