import math
import time

class BoardReset:
    def __init__(self, control_system):
        
        self.control_system = control_system
        self.gantry = self.control_system.gantry
        self.nfc = self.control_system.nfc

        self.nfc.begin()


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


    # def setup():
    #     nfc.begin()
    #     time.sleep(2)
    #     gantry.home()

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
        Reset all WHITE pieces NOT on ranks 1,2 or 7,8 OR in the deadzone 
        Assumes that the starting locations are either a) unoccupied or b) filled with the correct piece. 
        """
        # Loop over captured white pieces
        for piece in self.gantry.white_captured:
            symbol, current_coord = piece  # Extract symbol and current coordinates

            # Get valid coordinates for the symbol
            valid_coords = self.symbol_to_valid_coodinates().get(symbol, [])

            # Check which of those valid coordinates are already occupied
            # How does the diaz function work? 

            occupied_coords = self.get_occupied_squares(self.control_system.board)
            unoccupied_coords = []
            for coord in valid_coords:
                if coord not in occupied_coords:
                    unoccupied_coords.append(coord)

            if unoccupied_coords:
                # Generate path to the first unoccupied valid coordinate
                target_coord = unoccupied_coords[0]
                path = self.nearest_neighbor(current_coord, [target_coord])

                # Move the piece to the target coordinate
                for step in path:
                    self.gantry.send_coordinates_command(step)
                    time.sleep(1)  # Simulate movement delay

    def fen_to_coords(self,fen):
        """
        Given a fen string, output a list with the piece and its coordinates.
        Following the convention: (symbol, (x,y))
        """
        
        # Extract board setup from the FEN string
        board_part = fen.split()[0]
        ranks = board_part.split("/")  # Split into ranks

        self.pieces = []
        
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

      
        

    def reset_board_from_game(self):
        # Add logic here for dealign with resetting as well as deadzone pieces
        # DEAL WITH EXISITING FIRST 

        # Parse the FEN string to extract list of pieces and their coordinates
        board_state = self.fen_to_coords(self.control_system.board.fen())
    
        ## White captured and black captured are current coords of all pieces after end of game
        # Filter and append all pieces to self.gantry.white_captured or self.gantry.black_captured
        for piece in board_state:
            symbol, coords = piece  # Unpack the tuple
            if symbol.isupper():  # Check if the symbol is uppercase (white piece)
                self.gantry.white_captured.append((symbol, coords))  # Append to white_captured
            elif symbol.islower():
                self.gantry.black_captured.append((symbol, coords))\
                
        # Poll hall for empty squares and create an 8x8 matrix
        empty_squares = self.control_system.hall.sense_layer.get_squares_game()

        # Flip the y-axis to match chess notation (h1 as (0,0), a8 as (7,7))
        empty_squares = empty_squares[::-1]

        # Initialize white_restart_state with 16 slots
        white_restart_state = [(0, (0, 0)) for _ in range(16)]

        ##moveblack piece out of white endzone    
        for piece in self.gantry.black_captured:
            symbol, coords = piece
            x, y = coords
            if x < 75 and y < 375:
                # move is contains initial and final cords of black piece
                move = self.nearest_neighbor(coords, empty_squares)
                vector_move = (move[1][0] - move[0][0], move[1][1] - move[0][1])
                path = [move[0], (0, 25), (vector_move-25, 0), (0, vector_move - 25), (25, 0)]

                # Update the black_captured list with the new coordinates
                self.gantry.black_captured.remove(piece)
                self.gantry.black_captured.append((symbol, move[1]))

                # Update the empty_squares matrix
                old_rank, old_file = coords[1] // 50, coords[0] // 50  # Convert old coords to matrix indices
                new_rank, new_file = move[1][0] // 50, move [1][1] // 50  # Convert new coords to matrix indices
                empty_squares[old_rank][old_file] = 0  # Mark the old square as empty
                empty_squares[new_rank][new_file] = 1  # Mark the new square as occupied

                # Execute the movement using the gantry
                print(f"Moving black piece {symbol} from {coords} to {new_coords} via path: {path}")
                movements = self.parse_path_to_movement(path)
                commands = self.movement_to_gcode(movements)
                print(f"Last move: {commands}")
                self.send_commands(commands)

        for piece in self.gantry.white_captured:
            symbol, coords = piece
            x, y = coords
            if x < 75 and y < 375:
                new_coords=self.symbol_to_valid_coordinates(symbol)
                #check which of the new cords 

                '''Check jacks function to know where this piece CAN move to'
                'check white_restart_state to deterine which of those sqaures are free'
                'Move white to closest free starting square' 
                'update white_captured list with new coords of piece just moved'
                'update white_restart_state list with new coords of piece just moved'''

        
            print(f"arranging white in rank 1 & 2: {path}")

            movements = self.parse_path_to_movement(path)
            commands = self.movement_to_gcode(movements)
            print(f"Last move: {commands}")
            self.send_commands(commands)
            
                
                
            

         
        

        #DEAL WITH DEAD ZONE SECOND 

        # extract symbol and coodrinate of LAST white piece from dictionaory 
        self.gantry.white_captured
        # for i, val in enumerate(self.control_system.captured_pieces):

        #     if val.is_lower():
        
        

        

        ## STEP 3: PIECES IN DEADZONE RESET AFTER PIECES ON BOARD ARE REST. 


        start = (0, 0)

        # Get the occupied squares and compute the nearest neighbor path.
        occupied_squares = board_reset.get_occupied_squares(board)
        path = board_reset.nearest_neighbor(start, occupied_squares)

        # Map board coordinates to chess square labels.
        chess_path = {coord: board_reset.coord_to_chess_square(coord) for coord in path}
        # Map chess square labels to physical (x, y) coordinates using the static mapping.

        print("Nearest Neighbor Path (board coordinates):")
        print(path)
        print("\nMapping to Chess Squares:")
        print(chess_path)
        print("\nChess Squares to Physical Coordinates:")
        print(physical_mapping)

        for square in path:
            board_reset.gantry.send_coordinates_command(square)
            piece = board_reset.nfc.read()
            print(f"Read piece: {piece}")
            time.sleep(1)








    def reset_board_from_menu(self):
        start = (0, 0)

        # Get the occupied squares and compute the nearest neighbor path.
        occupied_squares = board_reset.get_occupied_squares(board)
        path = board_reset.nearest_neighbor(start, occupied_squares)

        # Map board coordinates to chess square labels.
        chess_path = {coord: board_reset.coord_to_chess_square(coord) for coord in path}
        # Map chess square labels to physical (x, y) coordinates using the static mapping.

        print("Nearest Neighbor Path (board coordinates):")
        print(path)
        print("\nMapping to Chess Squares:")
        print(chess_path)
        print("\nChess Squares to Physical Coordinates:")
        print(physical_mapping)

        for square in path:
            board_reset.gantry.send_coordinates_command(square)
            piece = board_reset.nfc.read()
            print(f"Read piece: {piece}")
            time.sleep(1)















