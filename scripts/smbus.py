import time
from smbus2 import SMBus, i2c_msg
import errno

PN532_PREAMBLE                = (0x00)
PN532_STARTCODE1              = (0x00)
PN532_STARTCODE2              = (0xFF)
PN532_POSTAMBLE               = (0x00)
PN532_HOSTTOPN532             = (0xD4)
PN532_PN532TOHOST             = (0xD5)
PN532_ACK_WAIT_TIME           = (100)  # ms, timeout of waiting for ACK
PN532_INVALID_ACK             = (-1)
PN532_TIMEOUT                 = (-2)
PN532_INVALID_FRAME           = (-3)
PN532_NO_SPACE                = (-4)

PN532_COMMAND_SAMCONFIGURATION      = (0x14)

PN532_I2C_ADDRESS = (0x48 >> 1)

class Pn532I2c():
    def __init__(self, bus: int):
        self._smbus = None
        self._command = 0

    def begin(self):
        self._smbus = SMBus(1)
        time.sleep(1)

    def wakeup(self):
        time.sleep(0.05)  # wait for all ready to manipulate pn532
        try:
            msg = i2c_msg.write(PN532_I2C_ADDRESS, [0])
            self._smbus.i2c_rdwr(msg)
        except Exception as e:
            print("Error in wakeup:", e)
        return

    def writeCommand(self, header: bytearray, body: bytearray = bytearray()):
        self._command = header[0]
        data_out = [PN532_PREAMBLE, PN532_STARTCODE1, PN532_STARTCODE2]
        # length = TFI + DATA (header and body)
        length = len(header) + len(body) + 1
        data_out.append(length)
        data_out.append((~length & 0xFF) + 1)  # checksum of length

        data_out.append(PN532_HOSTTOPN532)
        dsum = PN532_HOSTTOPN532 + sum(header) + sum(body)

        data_out += list(header)
        data_out += list(body)
        checksum = ((~dsum & 0xFF) + 1) & 0xFF  # checksum of TFI + DATA

        data_out += [checksum, PN532_POSTAMBLE]

        print("writeCommand: header:", header, "body:", body, "data_out:", data_out)

        try:
            msg = i2c_msg.write(PN532_I2C_ADDRESS, data_out)
            self._smbus.i2c_rdwr(msg)
        except Exception as e:
            print("Error during writeCommand:", e)
            print("Too many data to send, I2C doesn't support such a big packet")
            return PN532_INVALID_FRAME

        return self._readAckFrame()

    def _getResponseLength(self, timeout: int):
        PN532_NACK = [0, 0, 0xFF, 0, 0, 0]
        timer = 0

        while True:
            msg = i2c_msg.read(PN532_I2C_ADDRESS, 6)
            self._smbus.i2c_rdwr(msg)
            data = list(msg)
            print("_getResponseLength length frame:", data)
            if data[0] & 0x1:
                # first byte indicates status: PN532 is ready
                break
            time.sleep(0.001)  # sleep 1 ms
            timer += 1
            if timeout != 0 and timer > timeout:
                return -1

        if (data[1] != PN532_PREAMBLE or
            data[2] != PN532_STARTCODE1 or
            data[3] != PN532_STARTCODE2):
            print("Invalid Length frame:", data)
            return PN532_INVALID_FRAME

        length = data[4]
        print("_getResponseLength: length is", length)

        # Send nack message for the last response
        print("_getResponseLength writing nack:", PN532_NACK)
        nack_msg = i2c_msg.write(PN532_I2C_ADDRESS, PN532_NACK)
        self._smbus.i2c_rdwr(nack_msg)

        return length

    def readResponse(self, timeout: int = 1000) -> (int, bytearray):
        t = 0
        length = self._getResponseLength(timeout)
        buf = bytearray()

        if length < 0:
            return length, buf

        # Read response: status + frame header, data, checksum, postamble
        frame_length = 6 + length + 2
        while True:
            msg = i2c_msg.read(PN532_I2C_ADDRESS, frame_length)
            self._smbus.i2c_rdwr(msg)
            data = list(msg)
            if data[0] & 0x1:
                break  # PN532 is ready
            time.sleep(0.001)  # sleep 1 ms
            t += 1
            if timeout != 0 and t > timeout:
                return -1, buf

        if (data[1] != PN532_PREAMBLE or
            data[2] != PN532_STARTCODE1 or
            data[3] != PN532_STARTCODE2):
            print("Invalid Response frame:", data)
            return PN532_INVALID_FRAME, buf

        length = data[4]

        # Verify length checksum
        if (length + data[5]) & 0xFF != 0:
            print("Invalid Length Checksum: len", length, "checksum", data[5])
            return PN532_INVALID_FRAME, buf

        # Response command is expected to be command+1
        cmd = self._command + 1
        if (data[6] != PN532_PN532TOHOST or data[7] != cmd):
            return PN532_INVALID_FRAME, buf

        # Reduce length by TFI and CMD bytes
        length -= 2

        print("readResponse: read command:", hex(cmd))

        dsum = PN532_PN532TOHOST + cmd
        buf = bytearray(data[8:-2])
        print("readResponse: response:", buf)
        dsum += sum(buf)

        checksum = data[-2]
        if ((dsum + checksum) & 0xFF) != 0:
            print("Checksum is not ok: sum", dsum, "checksum", checksum)
            return PN532_INVALID_FRAME, buf

        # data[-1] is the POSTAMBLE; no further validation here

        return length, buf

    def _readAckFrame(self) -> int:
        PN532_ACK = [0, 0, 0xFF, 0, 0xFF, 0]

        print("Waiting for ACK at:", time.time())

        t = 0
        while t <= PN532_ACK_WAIT_TIME:
            try:
                msg = i2c_msg.read(PN532_I2C_ADDRESS, len(PN532_ACK) + 1)
                self._smbus.i2c_rdwr(msg)
                data = list(msg)
                if data[0] & 0x1:
                    break  # PN532 is ready
            except IOError as e:
                if e.errno != errno.EIO:
                    raise
                # Otherwise, ignore and try again
            time.sleep(0.001)  # sleep 1 ms
            t += 1
        else:
            print("Time out when waiting for ACK")
            return PN532_TIMEOUT

        print("Ready at:", time.time())

        ackBuf = data[1:]
        if ackBuf != PN532_ACK:
            print("Invalid ACK", ackBuf)
            return PN532_INVALID_ACK

        return 0

if __name__ == "__main__":
    bus = Pn532I2c(1)
    bus.begin()
    bus.wakeup()
    header = bytearray([PN532_COMMAND_SAMCONFIGURATION,
                            0x01,   # normal mode
                            0x14,   # timeout 50ms * 20 = 1 second
                            0x01])  # use IRQ pin!

    bus.writeCommand(header)
    length, response = bus.readResponse()
    print("Response length:", length)
    print("Response data:", response)