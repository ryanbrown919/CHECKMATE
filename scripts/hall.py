from ctypes import CDLL, c_uint32, POINTER

class SenseLayer:
    def __init__(self):
        # ryan: change path to firmware
        self._lib = CDLL("../firmware/build/hall_firmware.so", mode=ctypes.RTLD_GLOBAL)
        self.rows = 8
        self.cols = 8

        self._lib.hall_get_squares.argtypes = []
        self._lib.hall_get_squares.restype = POINTER(POINTER(c_uint32))
        
        self._lib.hall_get_square.argtypes = [c_uint32, c_uint32]
        self._lib.hall_get_square.restype = c_uint32

    def begin(self):
        self._lib.hall_init()

    def get_squares(self):
        board_ptr = self._lib.hall_get_squares()
        
        board = []
        for i in range(self.rows):
            row_ptr = board_ptr[i]
            row = []
            for j in range(self.cols):
                row.append(row_ptr[j])
            board.append(row)
        return board

    def get_square(self, x, y):
        board = self.get_squares()
        return board[7 - x][y]
