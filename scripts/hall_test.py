import time
from hall import SenseLayer

layer = SenseLayer()

def setup():
    layer.begin()

def main():
    square = input("Enter square: to read: ")
    print(layer.get_square_from_notation(square))


if __name__ == "__main__":
    setup()
    while True:
        main()