try:
    from scripts.hall import SenseLayer
except:
    from hall import SenseLayer

from ctypes import CDLL, c_uint32, POINTER, RTLD_GLOBAL
import threading
import time


# class SenseLayer:
#     square_mapping = {f"{file}{rank}": (ord(file) - ord('a'), int(rank) - 1)
#                       for file in "abcdefgh" for rank in "12345678"}

#     def __init__(self):
#         # ryan: change path to firmware
#         self._lib = CDLL("../firmware/build/hall_firmware.so", mode=RTLD_GLOBAL)
#         self.rows = 8
#         self.cols = 8

#         self._lib.hall_get_squares.argtypes = []
#         self._lib.hall_get_squares.restype = POINTER(POINTER(c_uint32))
        
#         self._lib.hall_get_square.argtypes = [c_uint32, c_uint32]
#         self._lib.hall_get_square.restype = c_uint32

#     def begin(self):
#         self._lib.hall_init()

#     def get_squares(self):
#         board_ptr = self._lib.hall_get_squares()
        
#         board = []
#         for i in range(self.rows):
#             row_ptr = board_ptr[i]
#             row = []
#             for j in range(self.cols):
#                 row.append(row_ptr[j])
#             board.append(row)
#         return board

#     def get_square_cartesian(self, x, y):
#         return self._lib.hall_get_square(x, y)

#     def get_square_from_notation(self, square):
#         if square not in self.square_mapping:
#             return False

#         x, y = self.square_mapping[square]
#         return self.get_square_cartesian(x, y)



class Hall:

    def __init__(self):

        self.sense_layer = SenseLayer()
        self.sense_layer.begin()
        self.initial_board = self.sense_layer.get_squares()
        self.reference_board = None
        self.first_change = None
        self.second_change = None
        self.move = None

    def board_to_chess_notation(self, row, col):
        return f"{chr(97 + col)}{8 - row}"

    def compare_boards(self, board):
        # if self.initial_board is None:
        #     self.initial_board = board
        #     self.reference_board = board
        #     return None, None

        # Compare with the reference board
        for row in range(8):
            for col in range(8):
                if self.reference_board[row][col] != board[row][col]:
                    
                    change = self.board_to_chess_notation(row, col)
                    return change  # Update reference board after first change

        return None

    def process_boards(self, boards):
        first_change = None
        second_change = None

        self.reference_board = boards[0]

        for i, board in enumerate(boards):
            # print(f"Board {i + 1}:")
            if first_change is None:
                # print("Checking first change")
                first_change = self.compare_boards(board)
                if first_change and not second_change:
                    print(f"First change detected: {first_change}")
                    self.reference_board = boards[i]
            elif second_change is None:
                # print("checking second change")
                second_change = self.compare_boards(board)
                
            else:
                print(f"Move detected: {first_change}{second_change}")
                return f"{first_change}{second_change}"
        print("No changes detected")
        return None
    
    def poll_board_for_change(self, board):

        # print(f"Board {i + 1}:")
        if self.first_change is None:
            # print("Checking first change")
            self.first_change = self.compare_boards(board)
            if self.first_change and not self.second_change:
                print(f"First change detected: {self.first_change}")
                self.reference_board = board
        elif self.second_change is None:
            # print("checking second change")
            self.second_change = self.compare_boards(board)
            
        else:
            print(f"Move detected: {self.first_change}{self.second_change}")
            return f"{self.first_change}{self.second_change}"
        print("No changes detected")
        return None
    

    def poll_board_for_change(self):
        while move is None:
            move = self.poll_board_for_change(self.sense_layer.get_squares())

        return move