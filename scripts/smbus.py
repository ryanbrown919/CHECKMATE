from smbus2 import SMBus

PN532_I2C_ADDRESS = 0x24 

try:
    with SMBus(1) as bus:
        data = bus.read_byte(PN532_I2C_ADDRESS)
        print("Data read:", data)
except Exception as e:
    print("I2C communication error:", e)