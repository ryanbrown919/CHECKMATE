import time
import binascii
import math

from pn532pi import Pn532, pn532, Pn532I2c

class NFC():
    def __init__(self):
        # Instantiate using I2C interface
        self.nfc = Pn532(Pn532I2c(1))

    def begin(self):
        self.nfc.begin()
        # Optionally, you can print firmware info here if needed.
    
    def read(self):
        # Wait for an ISO14443A card (Mifare, etc.).
        success, uid = self.nfc.readPassiveTargetID(pn532.PN532_MIFARE_ISO14443A_106KBPS)

        if success:
            print("\nFound an ISO14443A card")
            print("UID Length: {:d}".format(len(uid)))
            print("UID Value: {}".format(binascii.hexlify(uid)))

            if len(uid) == 4:
                print("Appears to be a Mifare Classic card (4 byte UID)")
                print("Trying to authenticate block 4 with default KEYA value")
                keya = bytearray([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
                success = self.nfc.mifareclassic_AuthenticateBlock(uid, 4, 0, keya)
                if success:
                    print("Sector 1 (Blocks 4..7) authenticated")
                    success, data = self.nfc.mifareclassic_ReadDataBlock(4)
                    if success:
                        # Decode the raw data to a string assuming UTF-8 encoding.
                        tag_str = data.decode('utf-8', errors='ignore')
                        print("Read tag string: {}".format(tag_str))
                    else:
                        print("Unable to read block 4. Try another key?")
                else:
                    print("Authentication failed: Try another key?")
            elif len(uid) == 7:
                print("Appears to be a Mifare Ultralight tag (7 byte UID)")
                print("Reading page 4")
                success, data = self.nfc.mifareultralight_ReadPage(4)
                if success:
                    # Decode the raw data from page 4 to a UTF-8 string.
                    tag_str = data.decode('utf-8', errors='ignore')
                    print("Read tag string: {}".format(tag_str))
                else:
                    print("Unable to read page 4")
        else:
            print(".", end="")  # Print a dot to indicate waiting

    def write(self, fen_piece):
        data = fen_piece.encode('utf-8')
        print("Waiting for a tag...")
        tag_present = False

        while not tag_present:
            time.sleep(0.1)
            tag_present, uid = self.nfc.readPassiveTargetID(pn532.PN532_MIFARE_ISO14443A_106KBPS)
    
        print("Tag detected!")
    
        # Read Tag capacity from page 3 (NTAG21x spec)
        status, buf = self.nfc.mifareultralight_ReadPage(3)
        if not status:
            print("Failed to read tag capacity from page 3")
            return
        # The third byte of page 3 gives the size in multiples of 8 bytes
        capacity_bytes = int(buf[2]) * 8
        print("Tag capacity is {} bytes".format(capacity_bytes))
    
        # Calculate total number of writable pages (pages start at 4)
        total_pages = capacity_bytes // 4
        writable_pages = total_pages - 4  # pages 0-3 are reserved
    
        # Calculate number of pages needed
        pages_needed = math.ceil(len(data) / 4)
        if pages_needed > writable_pages:
            print("Error: The string is too long for this tag!")
            return

        print("Writing {} byte(s) over {} page(s)...".format(len(data), pages_needed))
    
        # Write data starting at page 4
        for i in range(pages_needed):
            page_num = 4 + i
            # Get the slice for this page (4 bytes)
            chunk = data[i*4:(i+1)*4]
            # Pad chunk to 4 bytes if needed
            if len(chunk) < 4:
                chunk = chunk.ljust(4, b'\x00')
            status = self.nfc.mifareultralight_WritePage(page_num, chunk)
            if status:
                print("Wrote to page {}: {}".format(page_num, binascii.hexlify(chunk)))
            else:
                print("Failed to write to page {}".format(page_num))
    
        print("Write completed. Remove tag to try again.")

def setup():
    global nfc_global
    nfc_global = NFC()
    nfc_global.begin()
    print("NFC device initialized. Waiting for an ISO14443A Card ...")

if __name__ == '__main__':
    setup()
    # In a loop, continuously try reading a tag.
    while True:
        nfc_global.read()
        time.sleep(0.2)