import time
from nfc import NFC

nfc = NFC()

def setup()
    nfc.begin()
    print("NFC reader initialized")

def main():
    while True:
        mode = input("Enter mode (read, write): ")
        
        if mode == "w":
            piece = input("Enter piece: ")
            write_ok = nfc.write(piece)
            if write_ok:
                print("Write successful")
            else:
                print("Write failed")

        elif mode == "r":
            tag_present, fen_piece = nfc.read()
            if tag_present:
                print("Tag present, piece: ", fen_piece)
            else:
                print("No tag present")


        