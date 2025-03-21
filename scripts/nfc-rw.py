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
            success, uid = nfc.readPassiveTargetID(pn532.PN532_MIFARE_ISO14443A_106KBPS, 1000)

            if (success):
                #  Display some basic information about the card
                print("Found an ISO14443A card")
                print("UID Length: {:d}".format(len(uid)))
                print("UID Value: {}".format(binascii.hexlify(uid)))

            else:
                print("Ooops ... something went wrong while trying to read card")
                break

            if (len(uid) == 4):
            #  We probably have a Mifare Classic card ...
                print("Seems to be a Mifare Classic card (4 byte UID)")

                #  Now we need to try to authenticate it for read/write access
                #  Try with the factory default KeyA: 0xFF 0xFF 0xFF 0xFF 0xFF 0xFF
                print("Trying to authenticate block 4 with default KEYA value")
                keya = bytearray([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])

                #  Start with block 4 (the first block of sector 1) since sector 0
                #  contains the manufacturer data and it's probably better just
                #  to leave it alone unless you know what you're doing
                success = nfc.mifareclassic_AuthenticateBlock(uid, 4, 0, keya)

                if (success):
                    print("Sector 1 (Blocks 4..7) has been authenticated")

                    #  If you want to write something to block 4 to test with, uncomment
                    #  the following line and this text should be read back in a minute
                    # data = bytearray([ b'a', b'd', b'a', b'f', b'r', b'u', b'i', b't', b'.', b'c', b'o', b'm', 0, 0, 0, 0])
                    # success = nfc.mifareclassic_WriteDataBlock (4, data)

                    #  Try to read the contents of block 4
                    success, data = nfc.mifareclassic_ReadDataBlock(4)

                    if (success):
                        #  Data seems to have been read ... spit it out
                        print("Reading Block 4: {}".format(binascii.hexlify(data)))
                        return True

                    else:
                        print("Ooops ... unable to read the requested block.  Try another key?")
                else:
                    print("Ooops ... authentication failed: Try another key?")

            elif (len(uid) == 7):
                #  We probably have a Mifare Ultralight card ...
                print("Seems to be a Mifare Ultralight tag (7 byte UID)")

                #  Try to read the first general-purpose user page (#4)
                print("Reading page 4")
                success, data = nfc.mifareultralight_ReadPage(4)
                if (success):
                    #  Data seems to have been read ... spit it out
                    binascii.hexlify(data)
                    return True

                else:
                    print("Ooops ... unable to read the requested page!?")
        
        else:
            print("Invalid mode")


if __name__ == "__main__":
    setup()
    while True:
        main()

        