#!/usr/bin/env python3
import lgpio
import time
import errno


class I2CMaster():
    PN532_PREAMBLE                = (0x00)
    PN532_STARTCODE1              = (0x00)
    PN532_STARTCODE2              = (0xFF)
    PN532_POSTAMBLE               = (0x00)
    PN532_HOSTTOPN532             = (0xD4)
    PN532_PN532TOHOST             = (0xD5)
    PN532_ACK_WAIT_TIME           = (10)  # ms, timeout of waiting for ACK
    PN532_INVALID_ACK             = (-1)
    PN532_TIMEOUT                 = (-2)
    PN532_INVALID_FRAME           = (-3)
    PN532_NO_SPACE                = (-4)

    def __init__(self, i2c_bus=1, i2c_addr=0x48):
        self.i2c_addr = i2c_addr
        self.i2c_bus = i2c_bus
        
        self.handle = lgpio.i2c_open(self.i2c_bus, self.i2c_addr)
        if self.handle < 0:
            raise IOError(f"Failed to open I2C connection to address 0x{self.i2c_addr:02X} on bus {self.i2c_bus}")
        
        print(f"Connected to NFC device at address 0x{self.i2c_addr:02X}")

    def writeCommand(self, header: bytearray, body: bytearray = bytearray()):
        self._command = header[0]
        data_out = [self.PN532_PREAMBLE, self.PN532_STARTCODE1, self.PN532_STARTCODE2]

        length = len(header) + len(body) + 1 # length of data field: TFI + DATA
        data_out.append(length)
        data_out.append((~length & 0xFF) + 1) # checksum of length

        data_out.append(self.PN532_HOSTTOPN532)
        dsum = self.PN532_HOSTTOPN532 + sum(header) + sum(body)  # sum of TFI + DATA

        data_out += list(header)
        data_out += list(body)
        checksum = ((~dsum & 0xFF) + 1) & 0xFF # checksum of TFI + DATA

        data_out += [checksum, self.PN532_POSTAMBLE]

        print(f"writeCommand: {header}    {body}    {data_out}")

        try:
            # send data using lgpio - maximum 32 bytes per transfer
            data_bytes = bytearray(data_out)
            max_size = 32  # I2C typical maximum packet size
            
            if len(data_bytes) <= max_size:
                result = lgpio.i2c_write_i2c_block_data(self.handle, 0x00, data_bytes)
                if result < 0:
                    print(f"Error writing command: {result}")
                    return self.PN532_INVALID_FRAME
            else:
                # Split into chunks if needed
                for i in range(0, len(data_bytes), max_size):
                    chunk = data_bytes[i:i+max_size]
                    result = lgpio.i2c_write_i2c_block_data(self.handle, 0x00, chunk)
                    if result < 0:
                        print(f"Error writing command chunk: {result}")
                        return self.PN532_INVALID_FRAME
                    time.sleep(0.001)  # Small delay between chunks
        except Exception as e:
            print(e)
            print("\nError in I2C communication")
            return self.PN532_INVALID_FRAME

        return self._readAckFrame()

    def _getResponseLength(self, timeout: int):
        PN532_NACK = [0, 0, 0xFF, 0xFF, 0, 0]
        timer = 0

        while True:
            try:
                # Read 6 bytes using lgpio
                data = lgpio.i2c_read_i2c_block_data(self.handle, 0x00, 6)
                if data is None or len(data) < 6:
                    print("Failed to read response length")
                    time.sleep(0.001)
                    timer += 1
                    if (0 != timeout) and (timer > timeout):
                        return -1
                    continue
                
                data = bytearray(data)
                print(f'_getResponseLength length frame: {data!r}')
                
                if data[0] & 0x1:
                    # check first byte --- status
                    break  # PN532 is ready

                time.sleep(0.001)    # sleep 1 ms
                timer += 1
                if (0 != timeout) and (timer > timeout):
                    return -1
            except Exception as e:
                print(f"Error reading response: {e}")
                time.sleep(0.001)
                timer += 1
                if (0 != timeout) and (timer > timeout):
                    return -1

        if (self.PN532_PREAMBLE != data[1] or  # PREAMBLE
            self.PN532_STARTCODE1 != data[2] or  # STARTCODE1
            self.PN532_STARTCODE2 != data[3]):   # STARTCODE2
            print(f'Invalid Length frame: {data}')
            return self.PN532_INVALID_FRAME

        length = data[4]
        print(f'_getResponseLength length is {length:d}')

        # request for last respond msg again
        print(f'_getResponseLength writing nack: {PN532_NACK!r}')
        try:
            lgpio.i2c_write_i2c_block_data(self.handle, 0x00, bytearray(PN532_NACK))
        except Exception as e:
            print(f"Error writing NACK: {e}")
            return self.PN532_INVALID_FRAME

        return length

    def readResponse(self, timeout: int = 1000) -> (int, bytearray):
        t = 0
        length = self._getResponseLength(timeout)
        buf = bytearray()

        if length < 0:
            return length, buf

        # [RDY] 00 00 FF LEN LCS (TFI PD0 ... PDn) DCS 00
        while True:
            try:
                read_length = 6 + length + 2  # 6 header bytes + payload + 2 footer bytes
                data = lgpio.i2c_read_i2c_block_data(self.handle, 0x00, read_length)
                if data is None or len(data) < read_length:
                    print(f"Failed to read complete response, got {len(data) if data else 0} bytes, expected {read_length}")
                    time.sleep(0.001)
                    t += 1
                    if (0 != timeout) and (t > timeout):
                        return -1, buf
                    continue
                
                data = bytearray(data)
                if data[0] & 1:
                    # check first byte --- status
                    break  # PN532 is ready

                time.sleep(0.001)     # sleep 1 ms
                t += 1
                if (0 != timeout) and (t > timeout):
                    return -1, buf
            except Exception as e:
                print(f"Error reading response: {e}")
                time.sleep(0.001)
                t += 1
                if (0 != timeout) and (t > timeout):
                    return -1, buf

        if (self.PN532_PREAMBLE != data[1] or  # PREAMBLE
            self.PN532_STARTCODE1 != data[2] or  # STARTCODE1
            self.PN532_STARTCODE2 != data[3]):   # STARTCODE2
            print(f'Invalid Response frame: {data}')
            return self.PN532_INVALID_FRAME, buf

        length = data[4]

        if (0 != (length + data[5] & 0xFF)):
            # checksum of length
            print(f'Invalid Length Checksum: len {length:d} checksum {data[5]:d}')
            return self.PN532_INVALID_FRAME, buf

        cmd = self._command + 1  # response command
        if (self.PN532_PN532TOHOST != data[6] or (cmd) != data[7]):
            return self.PN532_INVALID_FRAME, buf

        length -= 2

        print(f"readResponse read command: {cmd:x}")

        dsum = self.PN532_PN532TOHOST + cmd
        buf = data[8:-2]
        print(f'readResponse response: {buf!r}\n')
        dsum += sum(buf)

        checksum = data[-2]
        if (0 != (dsum + checksum) & 0xFF):
            print(f"checksum is not ok: sum {dsum:d} checksum {checksum:d}\n")
            return self.PN532_INVALID_FRAME, buf
        # POSTAMBLE data [-1]

        return length, buf

    def _readAckFrame(self) -> int:
        PN532_ACK = [0, 0, 0xFF, 0, 0xFF, 0]

        print(f"wait for ack at: {time.time()}\n")

        t = 0
        while t <= self.PN532_ACK_WAIT_TIME:
            try:
                ack_length = len(PN532_ACK) + 1
                data = lgpio.i2c_read_i2c_block_data(self.handle, 0x00, ack_length)
                if data and len(data) >= ack_length:
                    data = bytearray(data)
                    if (data[0] & 1):
                        # check first byte --- status
                        break  # PN532 is ready
            except IOError as e:
                # As of Python 3.3 IOError is the same as OSError so we should check the error code
                if hasattr(e, 'errno') and e.errno != errno.EIO:
                    raise  # Reraise the error   
                # Otherwise do nothing, sleep and try again
            except Exception as e:
                print(f"Error reading ACK: {e}")
            
            time.sleep(0.001)    # sleep 1 ms
            t += 1
        else:
            print("Time out when waiting for ACK")
            return self.PN532_TIMEOUT

        print(f"ready at: {time.time()}\n")

        ackBuf = list(data[1:7])  # Get the 6 bytes that should be the ACK

        if ackBuf != PN532_ACK:
            print(f"Invalid ACK {ackBuf}")
            return self.PN532_INVALID_ACK

        return 0
        
    def close(self):
        try:
            lgpio.i2c_close(self.handle)
            print("NFC device connection closed")
        except Exception as e:
            print(f"Error closing I2C connection: {e}")



class NFC():
    PN532_COMMAND_SAMCONFIGURATION = (0x14)

    def __init__(self):
        self.i2c = I2CMaster()
        self.SAMConfig()

    def SAMConfig(self) -> bool:
        """
        Configures the SAM (Secure Access Module)
        :returns: True if success, False if error
        """
        header = bytearray([self.PN532_COMMAND_SAMCONFIGURATION,
                            0x01,   # normal mode
                            0x14,   # timeout 50ms * 20 = 1 second
                            0x01])  # use IRQ pin!

        self.i2c.writeCommand(header)
        return True

    def read(self):
        return None
            
    def write(self, fen_piece):
        return None
        
    def close(self):
        """Close the I2C connection."""
        if hasattr(self, 'i2c'):
            self.i2c.close()



# Example usage
if __name__ == "__main__":
    try:
        # Create an instance of the NFC class
        nfc_device = NFC()
        print("NFC device initialized.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Make sure to close the connection
        if 'nfc_device' in locals():
            nfc_device.close()