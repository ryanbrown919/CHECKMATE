from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.clock import Clock
import threading
import time
import sys
from kivy.app import App

# Check platform for compatibility
running_on_pi = sys.platform.startswith("linux")
FONT_SIZE = 32

if running_on_pi:
    import board
    import busio
    from adafruit_pn532.i2c import PN532_I2C

# Mock NFC Code-to-Icon Mapping
NFC_TAG_MAP = {
    "0000": "figures/black_pawn.png",
    "0001": "figures/black_knight.png",
    "0010": "figures/black_bishop.png",
    "0011": "figures/black_rook.png",
    "0100": "figures/black_queen.png",
    "0101": "figures/black_king.png",
    "0110": "figures/white_pawn.png",
    "0111": "figures/white_knight.png",
    "1000": "figures/white_bishop.png",
    "1001": "figures/white_rook.png",
    "1010": "figures/white_queen.png",
    "1011": "figures/white_king.png",
    "1111": "figures/logo.png",
}

class NFCWidget(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.layout = GridLayout(cols=2)
        
        # Left side layout for the log
        log_layout = BoxLayout(orientation='vertical', size_hint=(0.4, 1))
        self.log_label = Label(text="Scan Log:\n", size_hint=(1, 1), halign="left", valign="top", font_size=FONT_SIZE)
        self.log_label.bind(size=self.log_label.setter('text_size'))
        scroll_view = ScrollView()
        scroll_view.add_widget(self.log_label)
        log_layout.add_widget(scroll_view)
        self.layout.add_widget(log_layout)
        
        # Right side layout
        right_layout = BoxLayout(orientation='vertical', size_hint=(0.6, 1))
        
        # Icon display in the top-right
        self.icon_display = Image(source="figures/white_pawn.png", size_hint=(1, 0.5))  # Default to pawn
        right_layout.add_widget(self.icon_display)
        
        # Buttons in the bottom-left
        button_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.2))
        self.read_button = Button(text="Read NFC", size_hint=(0.5, 1), font_size=FONT_SIZE)
        self.read_button.bind(on_press=self.read_nfc)
        button_layout.add_widget(self.read_button)
        
        self.reconnect_button = Button(text="Reconnect", size_hint=(0.5, 1), font_size=FONT_SIZE)
        self.reconnect_button.bind(on_press=self.connect_reader)
        button_layout.add_widget(self.reconnect_button)
        
        right_layout.add_widget(button_layout)
        self.layout.add_widget(right_layout)
        
        self.add_widget(self.layout)
        
        if running_on_pi:
            self.i2c = busio.I2C(board.SCL, board.SDA)
            self.pn532 = None
            self.connect_reader()
        else:
            self.pn532 = None
            self.log("Running on non-Pi system. NFC scanning is simulated.")

    def connect_reader(self, instance=None):
        if running_on_pi:
            try:
                self.pn532 = PN532_I2C(self.i2c, debug=False)
                self.pn532.SAM_configuration()
                self.log("PN532 Reader connected successfully.")
            except Exception as e:
                self.log(f"Failed to connect: {e}")
                self.pn532 = None
        else:
            self.log("NFC Reader unavailable on this system.")

    def read_nfc(self, instance):
        if self.pn532:
            threading.Thread(target=self.scan_nfc, daemon=True).start()
        else:
            self.log("No NFC detected.")
            self.update_display("1111")
    
    def scan_nfc(self):
        if self.pn532:
            self.log("Waiting for an NFC tag...")
            uid = self.pn532.read_passive_target(timeout=0.5)
            if uid:
                self.log("Tag detected, reading data...")
                data = self.pn532.ntag2xx_read_block(4)  # Read data from block 4 (Modify as needed)
                if data:
                    tag_info = data.decode('utf-8').strip()  # Decode and clean up
                    self.log(f"Tag contains: {tag_info}")
                    self.update_display(tag_info)
                else:
                    self.log("Failed to read tag data.")
            else:
                self.log("No tag found.")

    def update_display(self, tag_info):
        icon_source = NFC_TAG_MAP.get(tag_info, "pawn.png")  # Default to pawn if unknown
        self.icon_display.source = icon_source
        self.icon_display.reload()
        self.log(f"Updated display to {icon_source}")

    def log(self, message):
        self.log_label.text += f"\n{message}"


class NFCApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(NFCWidget(name='nfc_reader'))
        return sm

if __name__ == "__main__":
    NFCApp().run()