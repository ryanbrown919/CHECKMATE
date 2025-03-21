"""
    This example will wait for any ISO14443A card or tag, and
    depending on the size of the UID it will attempt to read from it.
   
    If the card has a 4-byte UID it is probably a Mifare
    Classic card, and the following steps are taken:
   
    - Authenticate block 4 (the first block of Sector 1) using
      the default KEYA of 0XFF 0XFF 0XFF 0XFF 0XFF 0XFF
    - If authentication succeeds, we can then read any of the
      4 blocks in that sector (though only block 4 is read here)

    If the card has a 7-byte UID it is probably a Mifare
    Ultralight card, and the 4 byte pages can be read directly.
    Page 4 is read by default since this is the first 'general-
    purpose' page on the tags.

    To enable debug message, define DEBUG in nfc/pn532_log.h
"""
import time
import binascii

from pn532pi import Pn532, pn532
from pn532pi import Pn532I2c
from pn532pi import Pn532Spi
from pn532pi import Pn532Hsu

# Set the desired interface to True
SPI = False
I2C = True
HSU = False

if SPI:
    PN532_SPI = Pn532Spi(Pn532Spi.SS0_GPIO8)
    nfc = Pn532(PN532_SPI)
elif HSU:
    PN532_HSU = Pn532Hsu(Pn532Hsu.RPI_MINI_UART)
    nfc = Pn532(PN532_HSU)
elif I2C:
    PN532_I2C = Pn532I2c(1)
    nfc = Pn532(PN532_I2C)

fen_piece_map = {
    'K': 'White King',
    'Q': 'White Queen',
    'R': 'White Rook',
    'B': 'White Bishop',
    'N': 'White Knight',
    'P': 'White Pawn',
    'k': 'Black King',
    'q': 'Black Queen',
    'r': 'Black Rook',
    'b': 'Black Bishop',
    'n': 'Black Knight',
    'p': 'Black Pawn'
}

def translate_fen(fen_str):
    """Translate each FEN character to descriptive piece name.
    Numbers in FEN indicate empty squares and are skipped.
    """
    translation = []
    for char in fen_str:
        if char.isdigit():
            # Skip digits (or handle empty squares as needed)
            continue
        if char in fen_piece_map:
            translation.append(fen_piece_map[char])
            break
        else:
            translation.append(f"Unknown({char})")
    return translation

def setup():
    nfc.begin()

    versiondata = nfc.getFirmwareVersion()
    if not versiondata:
        print("Didn't find PN53x board")
        raise RuntimeError("Didn't find PN53x board")  # halt

    # Got ok data, print it out!
    print("Found chip PN5 {:#x} Firmware ver. {:d}.{:d}".format(
        (versiondata >> 24) & 0xFF,
        (versiondata >> 16) & 0xFF,
        (versiondata >> 8)  & 0xFF))

    # Configure board to read RFID tags
    # nfc.SAMConfig()

    print("Waiting for an ISO14443A Card ...")


def loop():
    # Wait for an ISO14443A card (Mifare, etc.).
    success, uid = nfc.readPassiveTargetID(pn532.PN532_MIFARE_ISO14443A_106KBPS)

    if success:
        print("\nFound an ISO14443A card")
        print("UID Length: {:d}".format(len(uid)))
        print("UID Value: {}".format(binascii.hexlify(uid)))

        if len(uid) == 4:
            print("Appears to be a Mifare Classic card (4 byte UID)")
            print("Trying to authenticate block 4 with default KEYA value")
            keya = bytearray([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
            success = nfc.mifareclassic_AuthenticateBlock(uid, 4, 0, keya)
            if success:
                print("Sector 1 (Blocks 4..7) authenticated")
                success, data = nfc.mifareclassic_ReadDataBlock(4)
                if success:
                    # Decode the raw data to a string assuming UTF-8 encoding.
                    fen_str = data.decode('utf-8', errors='ignore')
                    print("Raw tag data (decoded):", fen_str)
                    # Translate the FEN data using your dictionary
                    translation = translate_fen(fen_str)
                    print("Translated FEN data:")
                    for piece in translation:
                        print(piece)
                else:
                    print("Unable to read block 4. Try another key?")
            else:
                print("Authentication failed: Try another key?")
        elif len(uid) == 7:
            print("Appears to be a Mifare Ultralight tag (7 byte UID)")
            print("Reading page 4")
            success, data = nfc.mifareultralight_ReadPage(4)
            if success:
                # Decode the raw data from page 4 to a UTF-8 string.
                fen_str = data.decode('utf-8', errors='ignore')
                print("Raw tag data (decoded):", fen_str)
                # Translate the FEN string using your dictionary and translation function.
                translation = translate_fen(fen_str)
                print("Translated FEN data:")
                for piece in translation:
                    print(piece)
            else:
                print("Unable to read page 4")
    else:
        print(".", end="")  # Print a dot to indicate waiting
        

if __name__ == '__main__':
    setup()
    while True:
        loop()
        time.sleep(0.2)