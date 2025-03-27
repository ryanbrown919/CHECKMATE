import time
from grbl_streamer import GrblStreamer

class Gantry():
    board_mapping = {
        # Rank 1 (x = 0)
        "H1": (0, 0),    "G1": (0, 50),   "F1": (0, 100),  "E1": (0, 150),
        "D1": (0, 200),  "C1": (0, 250),  "B1": (0, 300),  "A1": (0, 350),

        # Rank 2 (x = 50)
        "H2": (50, 0),   "G2": (50, 50),  "F2": (50, 100), "E2": (50, 150),
        "D2": (50, 200), "C2": (50, 250), "B2": (50, 300), "A2": (50, 350),

        # Rank 3 (x = 100)
        "H3": (100, 0),  "G3": (100, 50), "F3": (100, 100), "E3": (100, 150),
        "D3": (100, 200), "C3": (100, 250), "B3": (100, 300), "A3": (100, 350),

        # Rank 4 (x = 150)
        "H4": (150, 0),  "G4": (150, 50), "F4": (150, 100), "E4": (150, 150),
        "D4": (150, 200), "C4": (150, 250), "B4": (150, 300), "A4": (150, 350),

        # Rank 5 (x = 200)
        "H5": (200, 0),  "G5": (200, 50), "F5": (200, 100), "E5": (200, 150),
        "D5": (200, 200), "C5": (200, 250), "B5": (200, 300), "A5": (200, 350),

        # Rank 6 (x = 250)
        "H6": (250, 0),  "G6": (250, 50), "F6": (250, 100), "E6": (250, 150),
        "D6": (250, 200), "C6": (250, 250), "B6": (250, 300), "A6": (250, 350),

        # Rank 7 (x = 300)
        "H7": (300, 0),  "G7": (300, 50), "F7": (300, 100), "E7": (300, 150),
        "D7": (300, 200), "C7": (300, 250), "B7": (300, 300), "A7": (300, 350),

        # Rank 8 (x = 350)
        "H8": (350, 0),  "G8": (350, 50), "F8": (350, 100), "E8": (350, 150),
        "D8": (350, 200), "C8": (350, 250), "B8": (350, 300), "A8": (350, 350),
    }
    
    def __init__(self):
        self.grbl = GrblStreamer(self.my_callback)
        self.grbl.cnect("/dev/ttyACM0", 115200)
        self.grbl.poll_start()

    def my_callback(self, eventstring, *data):
        args = [str(d) for d in data]
        print("MY CALLBACK: event={} data={}".format(eventstring.ljust(30), ", ".join(args)))

    def home(self):
        self.grbl.send_immediately("$H\n")
        self.grbl.send_immediately("G90 X-475 Y-486\n")
        self.grbl.send_immediately("G92 X0 Y0\n")
    
    def move(self, x, y):
        self.grbl.send_immediately(f"G0 X{x} Y{y}\n")

    def move_to_square(self, square):
        if square not in self.board_mapping:
            return False
        
        x, y = self.board_mapping[square]
        self.grbl.send_immediately(f"G0 X{x} Y{y}\n")
        return True






