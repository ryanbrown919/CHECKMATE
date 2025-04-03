import math
import time

from hall_control import Hall
from gantry_control import GantryControl

class BoardReset:
    def __init__(self, gantry, hall):    
        self.gantry = gantry
        self.hall = hall

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

    def reset_playing_area_white(self):
        """
        Reset all WHITE pieces NOT on ranks 1, 2 or in the deadzone.
        Assumes that the starting locations are either unoccupied or filled with the correct piece.
        """
        
        print("Test: STARTING METHOD 'reset_playing_area_white'")
       
        pieces = self.fen_to_coords("4r3/8/2kPnK2/8/8/2QpNq2/8/4Rb2")

        for piece in pieces:
            symbol, coords = piece
            x, y = coords

            # Only process pieces in the playable area (not in the deadzone)
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
                    # make this intelligent later...
                    target_coord = unoccupied_coords[0]

                    # Update the white_captured list with the new coordinates
                    self.gantry.white_captured.remove(piece) # add logic for duplicate pieces
                    self.gantry.white_captured.append((symbol, target_coord))

                    # Update the board state to reflect the move
                    old_rank, old_file = coords[1] // 50, coords[0] // 50
                    new_rank, new_file = target_coord[1] // 50, target_coord[0] // 50
                    # self.board[old_rank][old_file] = 0  # Mark old square as empty
                    # self.board[new_rank][new_file] = 1  # Mark new square as occupied

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
                print(f"White piece: {symbol} at {coords}") 
            elif symbol.islower(): # Black piece
                self.gantry.black_captured.append((symbol, coords))
                print(f"Black piece: {symbol} at {coords}")
                
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

        
                

        # Initialize white_restart_state with 16 slots
        # white_restart_state = [(0, (0, 0)) for _ in range(16)]

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
                filtered_empty_squares = []
                for i in range(len(empty_squares)):
                    for j in range(len(empty_squares[i])):
                        if empty_squares[i][j] == 1:  # Check if the square is empty
                            # Exclude squares in ranks 1 and 2 (y-coordinates 0 and 50)
                            if not (j * 50 < 75 and i * 50 < 375):  # Exclude x = 0, 50 and y = 0, 50
                                filtered_empty_squares.append((j * 50, i * 50))

                # print(f"[Test] Filtered empty squares (excluding ranks 1 and 2): {filtered_empty_squares}")
                move = self.nearest_neighbor(coords, filtered_empty_squares) 
                vector_move = (move[1][0] - move[0][0], move[1][1] - move[0][1])
                path = [move[0], (0, 25), (vector_move[0]-25, 0), (0, vector_move[1] - 25), (25, 0)]

                # Update the black_captured list with the new coordinates
                self.gantry.black_captured.remove(piece) # me no likey
                self.gantry.black_captured.append((symbol, move[1]))

                # Update the empty_squares matrix
                old_rank, old_file = coords[1] // 50, coords[0] // 50  # Convert old coords to matrix indices
                new_rank, new_file = move[1][0] // 50, move [1][1] // 50  # Convert new coords to matrix indices
                empty_squares[old_rank][old_file] = 0  # Mark the old square as empty
                empty_squares[new_rank][new_file] = 1  # Mark the new square as occupied

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
                if move[0][0] < 25 :
                    path = [move[0], (25, 0), (0, move[1][1]), (move[1][0] - 25, 0)]
                else:
                    path = [move[0], (-25, 0), (0, move[1][1]), (move[1][0] + 25, 0)]
        
                print(f"[Test] Moving white piece {symbol} from {move[0]} to {move[1]} via path: {path}")

                # Update white_captured list with new coordinates of the piece just moved
                self.gantry.white_captured.remove(piece)  # Remove the old entry
                self.gantry.white_captured.append((symbol, move[1]))  # Add the updated entry with new coordinates

                # Update the empty_squares matrix
                old_rank, old_file = coords[1] // 50, coords[0] // 50  # Convert old coords to matrix indices
                new_rank, new_file = move[1][0] // 50, move [1][1] // 50  # Convert new coords to matrix indices
                empty_squares[old_rank][old_file] = 0  # Mark the old square as empty
                empty_squares[new_rank][new_file] = 1  # Mark the new square as occupied

                        
                # print(f"arranging white in rank 1 & 2: {path}")
                movements = self.gantry.parse_path_to_movement(path)
                commands = self.gantry.movement_to_gcode(movements)
                print(f"Last move: {commands}")
                self.gantry.send_commands(commands)
            
                
    def full_reset(self):
        ''' Felipe's code '''
        print("[Test] Trying felipe 1")
        self.reset_board_from_game()
        ''' Jack's code '''
        print("[Test] Trying jack 1")
        self.reset_playing_area_white()
        ''' Felipe's code '''
        print("[Test] Trying felipe 2")
        self.reset_board_from_game()


if __name__ == "__main__":
    gantry = GantryControl()
    hall = Hall()
    board_reset = BoardReset(gantry, hall)

    # Example usage
    board_reset.full_reset()      

    