import time
from nfc import NFC

nfc = NFC()

def setup():
    nfc.begin()
    print("NFC reader initialized")

def main():
    while True:
        mode = input("Enter mode (read, write): ")
        
        if mode == "w" or mode == "write":
            while True:
                piece = input("Enter piece: ")
                if piece in ["K", "Q", "R", "B", "N", "P", "k", "q", "r", "b", "n", "p"]:
                    break
                else:
                    print("Invalid piece. Please try again.")

            write_ok = nfc.write(piece)
            if write_ok:
                print("Write successful")
            else:
                print("Write failed")

        elif mode == "r" or mode == "read":
            read_ok, piece = nfc.read()
            if read_ok:
                print("Read successful")
                print("Piece: " + piece)
            else:
                print("Read failed")

        else:
            print("Invalid mode. Please try again.")


if __name__ == "__main__":
    setup()
    while True:
        main()

        