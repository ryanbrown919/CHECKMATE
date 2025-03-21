import ctypes
from ctypes import c_uint32, POINTER

class HallFirmware:
    def __init__(self, lib_path="./firmware/build/hall_firmware.so", rows=8, cols=8):
        # Load the shared library
        self._lib = ctypes.CDLL(lib_path)
        
        # Save expected board dimensions (adjust as needed)
        self.rows = rows
        self.cols = cols
        
        # Configure the function prototypes.
        # For hall_get_squares, we expect a uint32_t**.
        self._lib.hall_get_squares.argtypes = []
        self._lib.hall_get_squares.restype = POINTER(POINTER(c_uint32))
        
        # For hall_get_square, as before:
        self._lib.hall_get_square.argtypes = [c_uint32, c_uint32]
        self._lib.hall_get_square.restype = c_uint32

    def get_squares(self):
        """
        Calls the firmware function hall_get_squares and returns the board
        as a Python list of lists.
        """
        # Call the firmware function.
        board_ptr = self._lib.hall_get_squares()
        
        board = []
        # Assuming an 'rows' x 'cols' board.
        for i in range(self.rows):
            # Access the pointer to row i from board_ptr.
            # board_ptr[i] is of type POINTER(c_uint32)
            row_ptr = board_ptr[i]
            row = []
            for j in range(self.cols):
                # Access jth element in this row.
                row.append(row_ptr[j])
            board.append(row)
        return board

    def get_square(self, x, y):
        """
        Returns a single board value at coordinate (x,y) from firmware.
        """
        return self._lib.hall_get_square(x, y)

if __name__ == "__main__":
    firmware = HallFirmware()
    board = firmware.get_squares()
    print("Board state as a 2D array:")
    for row in board:
        print(row)
    
    # Example of getting a single square:
    sq = firmware.get_square(3, 5)
    print("Square (3,5) value:", sq)