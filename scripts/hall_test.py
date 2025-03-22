import time
from hall import SenseLayer

layer = SenseLayer()

def setup():
    layer.begin()

def main():
    board = layer.get_squares()
    for row in board:
        print(row)
    print() 


if __name__ == "__main__"
    setup()
    while True:
        main()
        time.sleep(0.1)