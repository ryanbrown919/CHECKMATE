from pn532pi import Pn532, pn532, Pn532I2c


# @TODO: verify read/write
class NFC():
    def __init__(self):
        # Attach to I2C bus 1 on the pi
        self.nfc = Pn532(Pn532I2c(1))

    def begin(self):
        self.nfc.begin()
    
    def read(self):
        tag_present = self.nfc.readPassiveTargetID(pn532.PN532_MIFARE_ISO14443A_106KBPS, 1000)
        if not tag_present:
            return False
        
        read_ok, data = self.nfc.mifareultralight_ReadPage(4)
        if not read_ok:
            return False
        
        fen_piece = data.decode('utf-8', errors='ignore')
        
        return True, fen_piece
        

    def write(self, fen_piece):
        fen_pieces = ["K", "Q", "R", "B", "N", "P", # white pieces
                      "k", "q", "r", "b", "n", "p"] # black pieces

        if fen_piece not in fen_pieces:
            return False 
        
        data = fen_piece.encode('utf-8')
        tag_present= self.nfc.readPassiveTargetID(pn532.PN532_MIFARE_ISO14443A_106KBPS, 1000)
    
        if not tag_present:
            return False
    
        # For a single byte, pad data to 4 bytes
        if len(data) < 4:
            data = data.ljust(4, b'\x00')
    
        write_ok = self.nfc.mifareultralight_WritePage(4, data)
        if not write_ok:
            return False
        else:
            return True
