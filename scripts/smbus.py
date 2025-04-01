from smbus2 import SMBus
import time

PN532_I2C_ADDRESS = 0x24  # Verify this is your device's address

try:
    with SMBus(1) as bus:
        time.sleep(0.1)
        data = bus.read_byte(PN532_I2C_ADDRESS)
        print("Data read:", data)
except Exception as e:
    print("I2C communication error:", e)
