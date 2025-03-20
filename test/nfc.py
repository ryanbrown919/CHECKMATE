# SPDX-FileCopyrightText: <text> 2015 Tony DiCola, Roberto Laricchia,
# and Francesco Crisafulli, for Adafruit Industries </text>
# SPDX-License-Identifier: MIT

"""
Example of detecting and reading a block from a MiFare classic NFC card using SPI.
This example shows connecting to the PN532 over SPI and writing & reading a MiFare classic RFID tag.
"""

import board
import busio
from digitalio import DigitalInOut
from adafruit_pn532.adafruit_pn532 import MIFARE_CMD_AUTH_B
from adafruit_pn532.spi import PN532_SPI

# SPI connection:
spi = busio.SPI(board.D11, board.D10, board.D9)
cs_pin = DigitalInOut(board.D26)
pn532 = PN532_SPI(spi, cs_pin, debug=False)

# Optionally, perform a hardware reset if needed:
# reset_pin = DigitalInOut(board.D6)
# pn532.hard_reset(reset_pin)

ic, ver, rev, support = pn532.firmware_version
print("Found PN532 with firmware version: {0}.{1}".format(ver, rev))

# Configure PN532 to communicate with MiFare cards
pn532.SAM_configuration()

print("Waiting for RFID/NFC card to write to!")

key = b"\xFF\xFF\xFF\xFF\xFF\xFF"

while True:
    # Check if a card is available to read, timeout set to 0.5 seconds.
    uid = pn532.read_passive_target(timeout=0.5)
    print(".", end="")
    # Break out of loop if a card is detected.
    if uid is not None:
        break

print("")
print("Found card with UID:", [hex(i) for i in uid])
print("Authenticating block 4 ...")

authenticated = pn532.mifare_classic_authenticate_block(uid, 4, MIFARE_CMD_AUTH_B, key)
if not authenticated:
    print("Authentication failed!")
else:
    # Prepare 16 bytes of data: set to 0xFEEDBEEF and pad with zeros.
    data = bytearray(16)
    data[0:16] = b"\xFE\xED\xBE\xEF\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    
    # Write the data block.
    pn532.mifare_classic_write_block(4, data)
    
    # Read back block 4.
    read_data = pn532.mifare_classic_read_block(4)
    print("Wrote to block 4, now trying to read that data:", [hex(x) for x in read_data])