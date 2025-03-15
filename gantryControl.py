'''
Contains wwidget to conenct and control gantry, as well as interface for manual gantry control and debug log

'''


import glob
import serial
import time
import threading

from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label

from customWidgets import HorizontalLine, VerticalLine, IconButton, headerLayout, ChessBoardWidget

# Constant feedrate as in your original code
FEEDRATE = 10000  # mm/min

class gantryControl:
        def __init__(self):
            self.feed_rate = FEEDRATE

            # Internal state variables
            self.jog_step = 4
            self.step = 1
            self.simulate = False
            self.serial_lock = threading.Lock()
            self.board_coordinates =   {"a1": (0, 14), "a2": (2,14), "a3": (4,14), "a4": (6,14), "a5": (8,14), "a6": (10,14), "a7": (12,14), "a8": (14, 14),
                                        "b1": (0, 12), "b2": (2,12), "b3": (4,12), "b4": (6,12), "b5": (8,12), "b6": (10,12), "b7": (12,12), "b8": (14, 12),
                                        "c1": (0, 10), "c2": (2,10), "c3": (4,10), "c4": (6,10), "c5": (8,10), "c6": (10,10), "c7": (12,10), "c8": (14 ,10),
                                        "d1": (0, 8),  "d2": (2, 8), "d3": (4, 8), "d4": (6, 8), "d5": (8, 8), "d6": (10, 8), "d7": (12, 8), "d8": (14, 8),
                                        "e1": (0, 6),  "e2": (2, 6), "e3": (4, 6), "e4": (6, 6), "e5": (8, 6), "e6": (10, 6), "e7": (12, 6), "e8": (14, 6),
                                        "f1": (0, 4),  "f2": (2, 4), "f3": (4, 4), "f4": (6, 4), "f5": (8, 4), "f6": (10, 4), "f7": (12, 4), "f8": (14, 4),
                                        "g1": (0, 2),  "g2": (2, 2), "g3": (4, 2), "g4": (6, 2), "g5": (8, 2), "g6": (10, 2), "g7": (12, 2), "g8": (14, 2),
                                        "h1": (0, 0),  "h2": (2, 0), "h3": (4, 0), "h4": (6, 0), "h5": (8, 0), "h6": (10, 0), "h7": (12, 0), "h8": (14, 0)}
            


        def home_gantry(self):
            self.send_gcode("$H")

        def connect_to_grbl(self):
            """
            Attempt to connect to a GRBL device via serial.
            If no device is found or an error occurs, simulation mode is enabled.
            """
            grbl_port = self.find_grbl_port()
            if not grbl_port:
                print("No GRBL device found, switching to simulation mode.")
                self.simulate = True
                return

            try:
                self.ser = serial.Serial(grbl_port, 115200, timeout=1)
                time.sleep(2)  # Allow GRBL to initialize.
                self.send_gcode("$X")  # Clear alarms.
                print(f"Connected to GRBL on {grbl_port}")
            except Exception as e:
                print(f"Error connecting to GRBL: {e}")
                self.simulate = True

        def find_grbl_port(self):
            ports = glob.glob("/dev/ttyUSB*")
            return ports[0] if ports else None

        def send_gcode(self, command):
            """
            Send a G-code command to GRBL.
            In simulation mode, the command is logged to the debug log.
            Errors during write/read are caught and handled.
            """
            print(f"Sending: {command}")
            if self.simulate:
                return

            with self.serial_lock:
                try:
                    self.ser.write(f"{command}\n".encode())
                except Exception as e:
                    error_msg = f"Error writing command: {e}"
                    print(error_msg)
                    self.handle_serial_error(e)
                    return

                try:
                    while True:
                        response = self.ser.readline().decode('utf-8', errors='replace').strip()
                        if response:
                            print(f"GRBL Response: {response}")
                        if response == "ok":
                            break
                        elif response == "ALARM:1":
                            self.log_debug("ALARM:1 - Resetting GRBL")
                            self.send_gcode("$X")
                            break   
                        
                except Exception as e:
                    error_msg = f"Error reading response: {e}"
                    print(error_msg)
                    self.handle_serial_error(e)
                    return

        def handle_serial_error(self, error):
            """
            Handle serial communication errors by logging the error,
            closing the serial port if necessary, and scheduling a reconnect.
            """
            self.log_debug(f"Serial error occurred: {error}. Attempting to reconnect...")
            try:
                if hasattr(self, 'ser') and self.ser:
                    self.ser.close()
            except Exception as close_err:
                pass
            # Schedule a reconnect attempt after a short delay.
            Clock.schedule_once(lambda dt: self.connect_to_grbl(), 1)

        def send_jog_command(self, dx, dy):
            """
            Construct and send the jog command based on dx, dy, and the current jog step size.
            """
            step = self.jog_step
            cmd = "$J=G21G91"
            if dx:
                cmd += f"X{dx * step}"
            if dy:
                cmd += f"Y{dy * step}"
            cmd += f"F{FEEDRATE}"
            self.send_gcode("$X") 
            self.send_gcode(cmd)

        def send_coordinates_command(self, x, y):
            """
            Construct and send the jog command based on dx, dy, and the current jog step size.
            Figure out the gcode move command
            """
            step = self.step
            cmd = "$J=G21G90G1"
            if x:
                cmd += f"X{x * step}"
            if y:
                cmd += f"Y{y * step}"
            cmd += f"F{FEEDRATE}"
            self.send_gcode("$X") 
            self.send_gcode(cmd)


        def on_step_change(self, instance, value):
            """
            Update the jog step size when the user modifies the TextInput.
            """
            try:
                self.jog_step = int(value)
            except ValueError:
                self.jog_step = 1

        def on_reconnect(self, instance):
            """
            Manually trigger a reconnect to the GRBL device.
            This can be useful if a flag is raised (e.g., a limit switch is triggered)
            and you need to reinitialize the connection.
            """
            # Attempt to reconnect immediately.
            self.connect_to_grbl()














class GantryControlScreen(Screen):
    def __init__(self, **kwargs):
        super(GantryControlScreen, self).__init__(**kwargs)

       # General Structure of Gameplay Screen
        root_layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        header_layout = headerLayout()
        playarea_layout = BoxLayout(orientation='horizontal', spacing=20, size_hint=(1, 0.9))

        controls_layout=GridLayout(cols=3, rows=4, spacing=5, size_hint=(0.7, 1))
        boardLayout = BoxLayout(orientation='vertical', spacing=20, size_hint=(0.3, 1))
        boardLayout.add_widget(ChessBoardWidget())


        root_layout.add_widget(header_layout)
        root_layout.add_widget(HorizontalLine())
        root_layout.add_widget(playarea_layout)
        playarea_layout.add_widget(controls_layout)
        playarea_layout.add_widget(boardLayout)
        self.add_widget(root_layout)


        self.gantry_control= gantryControl()


        # ---------------------
        # LEFT PANEL: Directional Buttons
        # ---------------------
        left_panel = GridLayout(cols=3, rows=4, spacing=5, size_hint=(0.7, 1))
        # Define directional buttons with text indicating x/y movements.
        buttons = [
            {"text": "X- Y-", "dx": -1, "dy": -1},
            {"text": "Y-",   "dx":  0, "dy": -1},
            {"text": "X+ Y-", "dx":  1, "dy": -1},
            {"text": "X-",   "dx": -1, "dy":  0},
            {"text": "",     "dx":  0, "dy":  0},  # Center is left blank.
            {"text": "X+",   "dx":  1, "dy":  0},
            {"text": "X- Y+", "dx": -1, "dy":  1},
            {"text": "Y+",   "dx":  0, "dy":  1},
            {"text": "X+ Y+", "dx":  1, "dy":  1}
            
        ]
        for b in buttons:
            if b["text"] == "":
                left_panel.add_widget(Label(font_size=32))
            else:
                btn = Button(text=b["text"], font_size=24)
                btn.dx = b["dx"]
                btn.dy = b["dy"]
                # Bind only on_release so that each tap sends one command.
                btn.bind(on_release=self.on_button_release)
                left_panel.add_widget(btn)

        left_panel.add_widget(Button(text="Activate Magnet", font_size=24))

        controls_layout.add_widget(left_panel)


        # ---------------------
        # RIGHT PANEL: Controls & Debug Log
        # ---------------------
        right_panel = BoxLayout(orientation='vertical', spacing=10, size_hint=(0.3, 1))

        # Step size controls.
        step_label = Label(text="Step Size (mm):", size_hint_y=0.1, font_size=24)
        self.step_input = TextInput(text=str(self.gantry_control.jog_step), multiline=False,
                                    input_filter='int', size_hint_y=0.1)
        self.step_input.bind(text=self.gantry_control.on_step_change)

        # Reconnect button (extra action) to manually reconnect to the device.
        reconnect_button = Button(text="Reconnect", size_hint_y=0.2, font_size=32)
        reconnect_button.bind(on_release=self.gantry_control.on_reconnect)

        # Debug log area (visible in simulation mode or upon errors).
        debug_label = Label(text="Debug Log:", size_hint_y=0.1, font_size=32)
        self.debug_log = TextInput(text="", readonly=True, multiline=True, size_hint_y=0.6, font_size=24)

        right_panel.add_widget(step_label)
        right_panel.add_widget(self.step_input)
        right_panel.add_widget(reconnect_button)
        right_panel.add_widget(debug_label)
        right_panel.add_widget(self.debug_log)

      

        # Schedule the GRBL connection attempt after initialization.
        Clock.schedule_once(lambda dt: self.gantry_control.connect_to_grbl(), 0)


    def on_button_release(self, instance):
        """
        Handle a directional button tap by sending a single jog command.
        """
        dx = instance.dx
        dy = instance.dy
        self.gantry_control.send_jog_command(dx, dy)


 


# ---------------------
# Example Integration
# ---------------------
if __name__ == '__main__':
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout

    class TestApp(App):
        def build(self):
            root = BoxLayout(orientation='vertical')
            gantry_widget = GantryControlScreen()
            root.add_widget(gantry_widget)
            return root

    TestApp().run()

