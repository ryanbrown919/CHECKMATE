from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.clock import Clock
import threading
import sys
from kivy.app import App
from kivy.graphics import Color, Rectangle

# Check platform for compatibility
running_on_pi = sys.platform.startswith("linux")
FONT_SIZE = 32

if running_on_pi:
    import board
    import busio
    from adafruit_pn532.i2c import PN532_I2C

# Define a mapping for chess pieces using integer codes.
# 0-5: Black Pawn, Knight, Bishop, Rook, Queen, King
# 6-11: White Pawn, Knight, Bishop, Rook, Queen, King
# Code 15 is used as a default (logo) if needed.
PIECE_MAP = {
    0: "figures/black_pawn.png",
    1: "figures/black_knight.png",
    2: "figures/black_bishop.png",
    3: "figures/black_rook.png",
    4: "figures/black_queen.png",
    5: "figures/black_king.png",
    6: "figures/white_pawn.png",
    7: "figures/white_knight.png",
    8: "figures/white_bishop.png",
    9: "figures/white_rook.png",
    10: "figures/white_queen.png",
    11: "figures/white_king.png",
    15: "figures/logo.png",
}

class NFCWidget(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.layout = GridLayout(cols=2)
        
        # Left side layout for the log
        log_layout = BoxLayout(orientation='vertical', size_hint=(0.4, 1))
        self.log_label = Label(text="Scan Log:\n", size_hint=(1, 1),
                               halign="left", valign="top", font_size=FONT_SIZE)
        self.log_label.bind(size=self.log_label.setter('text_size'))
        scroll_view = ScrollView()
        scroll_view.add_widget(self.log_label)
        log_layout.add_widget(scroll_view)
        self.layout.add_widget(log_layout)
        
        # Right side layout
        right_layout = BoxLayout(orientation='vertical', size_hint=(0.6, 1))
        
        # Icon display in the top-right (for displaying the piece read from the tag)
        self.icon_display = Image(source=PIECE_MAP[15], size_hint=(1, 0.5))
        right_layout.add_widget(self.icon_display)
        
        # Unified Action Area with a light blue background
        action_area = BoxLayout(orientation='vertical', size_hint=(1, 0.5))
        with action_area.canvas.before:
            Color(0.8, 0.9, 1, 1)  # Light blue color
            self.action_rect = Rectangle(pos=action_area.pos, size=action_area.size)
        action_area.bind(pos=self.update_action_rect, size=self.update_action_rect)
        
        # Read and Reconnect Buttons layout
        button_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.4))
        self.read_button = Button(text="Read NFC", size_hint=(0.5, 1), font_size=FONT_SIZE)
        self.read_button.bind(on_press=self.read_nfc)
        button_layout.add_widget(self.read_button)
        
        self.reconnect_button = Button(text="Reconnect", size_hint=(0.5, 1), font_size=FONT_SIZE)
        self.reconnect_button.bind(on_press=self.connect_reader)
        button_layout.add_widget(self.reconnect_button)
        action_area.add_widget(button_layout)
        
        # Write NFC Section layout
        write_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.6))
        piece_select_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.6))
        self.left_arrow = Button(text="<", font_size=FONT_SIZE, size_hint=(0.2, 1))
        self.left_arrow.bind(on_press=self.decrement_piece)
        piece_select_layout.add_widget(self.left_arrow)
        
        # Current piece to write (using integer codes 0 to 11)
        self.current_piece_code = 0  
        self.write_piece_display = Image(source=PIECE_MAP[self.current_piece_code],
                                         size_hint=(0.6, 1))
        piece_select_layout.add_widget(self.write_piece_display)
        
        self.right_arrow = Button(text=">", font_size=FONT_SIZE, size_hint=(0.2, 1))
        self.right_arrow.bind(on_press=self.increment_piece)
        piece_select_layout.add_widget(self.right_arrow)
        write_layout.add_widget(piece_select_layout)
        
        self.write_button = Button(text="Write NFC", size_hint=(1, 0.4), font_size=FONT_SIZE)
        self.write_button.bind(on_press=self.write_nfc)
        write_layout.add_widget(self.write_button)
        
        action_area.add_widget(write_layout)
        right_layout.add_widget(action_area)
        self.layout.add_widget(right_layout)
        
        self.add_widget(self.layout)
        
        if running_on_pi:
            self.i2c = busio.I2C(board.SCL, board.SDA)
            self.pn532 = None
            self.connect_reader()
        else:
            self.pn532 = None
            self.log("Running on non-Pi system. NFC scanning is simulated.")

    def update_action_rect(self, instance, value):
        self.action_rect.pos = instance.pos
        self.action_rect.size = instance.size

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
            self.update_display(15)  # Default to logo

    def scan_nfc(self):
        if self.pn532:
            self.log("Waiting for an NFC tag...")
            uid = self.pn532.read_passive_target(timeout=0.5)
            if uid:
                self.log("Tag detected, reading data...")
                data = self.pn532.ntag2xx_read_block(0)  # Read block 0 (4 bytes)
                if data and len(data) >= 1:
                    # Use the first byte as the piece code
                    piece_code = data[0]
                    self.log(f"Tag contains piece code: {piece_code}")
                    self.update_display(piece_code)
                else:
                    self.log("Failed to read tag data.")
            else:
                self.log("No tag found.")
                self.update_display(15)
    
    def update_display(self, piece_code):
        # Update the main display icon based on the piece code.
        icon_source = PIECE_MAP.get(piece_code, PIECE_MAP[15])
        self.icon_display.source = icon_source
        self.icon_display.reload()
        self.log(f"Updated display to {icon_source} for piece code {piece_code}")

    def log(self, message):
        self.log_label.text += f"\n{message}"
    
    # Methods for the Write NFC Section.
    def increment_piece(self, instance):
        # Cycle through chess piece types (0 to 11).
        self.current_piece_code = (self.current_piece_code + 1) % 12
        self.update_write_display()
    
    def decrement_piece(self, instance):
        self.current_piece_code = (self.current_piece_code - 1) % 12
        self.update_write_display()
    
    def update_write_display(self):
        icon_source = PIECE_MAP.get(self.current_piece_code, PIECE_MAP[15])
        self.write_piece_display.source = icon_source
        self.write_piece_display.reload()
        self.log(f"Selected piece updated to {icon_source} for piece code {self.current_piece_code}")
    
    def write_nfc(self, instance):
        if self.pn532:
            try:
                # Pack the current piece code as one byte and pad with three zero bytes.
                data_to_write = bytes([self.current_piece_code, 0, 0, 0])
                self.pn532.ntag2xx_write_block(0, data_to_write)
                self.log(f"Successfully wrote piece code: {self.current_piece_code}")
            except Exception as e:
                self.log(f"Error writing tag: {e}")
        else:
            self.log("No NFC reader available to write tag.")

class NFCApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(NFCWidget(name='nfc_reader'))
        return sm

if __name__ == "__main__":
    NFCApp().run()
