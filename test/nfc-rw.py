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

        elif mode == "r" or "read":
            tag_present, fen_piece = nfc.read()

            if tag_present:
                print("Tag present, piece: ", fen_piece)
            else:
                print("No tag present")
        
        else:
            print("Invalid mode")


if __name__ == "__main__":
    setup()
    while True:
        main()

        