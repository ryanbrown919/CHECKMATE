"""
This script writes a user-supplied string to an NTAG21x tag over I2C.
The string is split into 4-byte chunks and written starting at page 4.
If the string is longer than the available capacity, an error is issued.
"""

import time
import binascii
import math

from pn532pi import Pn532, pn532
from pn532pi import Pn532I2c
from pn532pi import Pn532Spi
from pn532pi import Pn532Hsu

# Set the desired interface: Only one should be True.
SPI = False
I2C = True
HSU = False  # change to False if you want only I2C

if SPI:
    PN532_SPI = Pn532Spi(Pn532Spi.SS0_GPIO8)
    nfc = Pn532(PN532_SPI)
elif HSU:
    PN532_HSU = Pn532Hsu(0)
    nfc = Pn532(PN532_HSU)
elif I2C:
    PN532_I2C = Pn532I2c(1)
    nfc = Pn532(PN532_I2C)

def setup():
    print("NTAG21x R/W")
    print("-------Looking for PN532--------")

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

    # configure board to read RFID tags
    nfc.SAMConfig()

def loop():
    print("Waiting for a tag...")
    tag_present = False
    while not tag_present:
        time.sleep(0.1)
        tag_present, uid = nfc.readPassiveTargetID(pn532.PN532_MIFARE_ISO14443A_106KBPS)
    
    print("Tag detected!")
    
    # Read Tag capacity from page 3 (NTAG21x spec)
    status, buf = nfc.mifareultralight_ReadPage(3)
    if not status:
        print("Failed to read tag capacity from page 3")
        return
    # The third byte of page 3 gives the size in multiples of 8 bytes
    capacity_bytes = int(buf[2]) * 8
    print("Tag capacity is {} bytes".format(capacity_bytes))
    
    # Calculate total number of writable pages (pages start at 4)
    total_pages = capacity_bytes // 4
    writable_pages = total_pages - 4  # pages 0-3 are reserved
    
    # Get input string from user
    s = input("Enter the string to write to the tag: ")
    data = s.encode('utf-8')
    
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
        status = nfc.mifareultralight_WritePage(page_num, chunk)
        if status:
            print("Wrote to page {}: {}".format(page_num, binascii.hexlify(chunk)))
        else:
            print("Failed to write to page {}".format(page_num))
    
    print("Write completed. Remove tag to try again.")
    # Wait until tag is removed before next iteration
    while True:
        time.sleep(0.1)
        tag_present, uid = nfc.readPassiveTargetID(pn532.PN532_MIFARE_ISO14443A_106KBPS)
        if not tag_present:
            break

if __name__ == '__main__':
    setup()
    while True:
        loop()