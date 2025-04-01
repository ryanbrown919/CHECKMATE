#!/usr/bin/env python3
import lgpio
import time

class NFC:
    def __init__(self, i2c_bus=1, i2c_addr=0x48):
        self.i2c_addr = i2c_addr
        self.i2c_bus = i2c_bus
        
        self.handle = lgpio.i2c_open(i2c_bus, i2c_addr)
        if self.handle < 0:
            raise IOError(f"Failed to open I2C connection to address 0x{i2c_addr:02X} on bus {i2c_bus}")
        
        print(f"Connected to NFC device at address 0x{i2c_addr:02X}")
        
    def read_register(self, reg_addr):
        try:
            return lgpio.i2c_read_byte_data(self.handle, reg_addr)
        except Exception as e:
            print(f"Error reading from register 0x{reg_addr:02X}: {e}")
            return None
            
    def write_register(self, reg_addr, value):
        try:
            lgpio.i2c_write_byte_data(self.handle, reg_addr, value)
            return True
        except Exception as e:
            print(f"Error writing to register 0x{reg_addr:02X}: {e}")
            return False
    
    def read_block(self, reg_addr, num_bytes):
        try:
            return lgpio.i2c_read_i2c_block_data(self.handle, reg_addr, num_bytes)
        except Exception as e:
            print(f"Error reading block from register 0x{reg_addr:02X}: {e}")
            return None
    
    def write_block(self, reg_addr, data):
        try:
            lgpio.i2c_write_i2c_block_data(self.handle, reg_addr, data)
            return True
        except Exception as e:
            print(f"Error writing block to register 0x{reg_addr:02X}: {e}")
            return False
    
    def close(self):
        try:
            lgpio.i2c_close(self.handle)
            print("NFC device connection closed")
        except Exception as e:
            print(f"Error closing I2C connection: {e}")

# Example usage
if __name__ == "__main__":
    try:
        # Create an instance of the NFC class
        nfc_device = NFC()
        
        # Read a register (example)
        value = nfc_device.read_register(0x00)
        if value is not None:
            print(f"Register 0x00 value: 0x{value:02X}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Make sure to close the connection
        if 'nfc_device' in locals():
            nfc_device.close()