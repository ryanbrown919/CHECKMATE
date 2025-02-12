# import glob
# import serial
# import time
# import threading

# from kivy.clock import Clock
# from kivy.uix.boxlayout import BoxLayout
# from kivy.uix.gridlayout import GridLayout
# from kivy.uix.button import Button
# from kivy.uix.textinput import TextInput
# from kivy.uix.label import Label

# # Constant feedrate as in your original code
# FEEDRATE = 10000  # mm/min

# class GantryControlWidget(BoxLayout):
#     def __init__(self, **kwargs):
#         super(GantryControlWidget, self).__init__(**kwargs)
#         self.orientation = 'horizontal'
#         self.spacing = 10
#         self.padding = 10

#         # Internal state variables
#         self.jog_step = 4
#         self.simulate = False  # When True, widget is in simulation mode.
#         self.serial_lock = threading.Lock()

#         # ---------------------
#         # LEFT PANEL: Directional Buttons
#         # ---------------------
#         left_panel = GridLayout(cols=3, rows=3, spacing=5, size_hint=(0.7, 1))
#         # Define directional buttons with text indicating x/y movements.
#         buttons = [
#             {"text": "X- Y+", "dx": -1, "dy":  -1},
#             {"text": "Y+",   "dx":  0, "dy":  -1},
#             {"text": "X+ Y+", "dx":  1, "dy":  -1},
#             {"text": "X-",   "dx": -1, "dy":  0},
#             {"text": "",     "dx":  0, "dy":  0},  # Center is left blank.
#             {"text": "X+",   "dx":  1, "dy":  0},
#             {"text": "X- Y-", "dx": -1, "dy": 1},
#             {"text": "Y-",   "dx":  0, "dy": 1},
#             {"text": "X+ Y-", "dx":  1, "dy": 1}
#         ]
#         for b in buttons:
#             if b["text"] == "":
#                 left_panel.add_widget(Label(font_size=32))
#             else:
#                 btn = Button(text=b["text"], font_size=24)
#                 btn.dx = b["dx"]
#                 btn.dy = b["dy"]
#                 # Bind only on_release so that each tap sends one command.
#                 btn.bind(on_release=self.on_button_release)
#                 left_panel.add_widget(btn)

#         # ---------------------
#         # RIGHT PANEL: Controls & Debug Log
#         # ---------------------
#         right_panel = BoxLayout(orientation='vertical', spacing=10, size_hint=(0.3, 1))

#         # Step size controls.
#         step_label = Label(text="Step Size (mm):", size_hint_y=0.1, font_size=24)
#         self.step_input = TextInput(text=str(self.jog_step), multiline=False,
#                                     input_filter='int', size_hint_y=0.1)
#         self.step_input.bind(text=self.on_step_change)

#         # Reconnect button (extra action) to manually reconnect to the device.
#         reconnect_button = Button(text="Reconnect", size_hint_y=0.2, font_size=32)
#         reconnect_button.bind(on_release=self.on_reconnect)

#         # Debug log area (visible in simulation mode or upon errors).
#         debug_label = Label(text="Debug Log:", size_hint_y=0.1, font_size=32)
#         self.debug_log = TextInput(text="", readonly=True, multiline=True, size_hint_y=0.6, font_size=24)

#         right_panel.add_widget(step_label)
#         right_panel.add_widget(self.step_input)
#         right_panel.add_widget(reconnect_button)
#         right_panel.add_widget(debug_label)
#         right_panel.add_widget(self.debug_log)

#         self.add_widget(left_panel)
#         self.add_widget(right_panel)

#         # Schedule the GRBL connection attempt after initialization.
#         Clock.schedule_once(lambda dt: self.connect_to_grbl(), 0)

#     def connect_to_grbl(self):
#         """
#         Attempt to connect to a GRBL device via serial.
#         If no device is found or an error occurs, simulation mode is enabled.
#         """
#         grbl_port = self.find_grbl_port()
#         if not grbl_port:
#             print("No GRBL device found, switching to simulation mode.")
#             self.simulate = True
#             self.log_debug("Simulation mode enabled: No GRBL device found.")
#             return

#         try:
#             self.ser = serial.Serial(grbl_port, 115200, timeout=1)
#             time.sleep(2)  # Allow GRBL to initialize.
#             self.send_gcode("$X")  # Clear alarms.
#             print(f"Connected to GRBL on {grbl_port}")
#         except Exception as e:
#             print(f"Error connecting to GRBL: {e}")
#             self.simulate = True
#             self.log_debug(f"Simulation mode enabled due to error: {e}")

#     def find_grbl_port(self):
#         ports = glob.glob("/dev/ttyUSB*")
#         return ports[0] if ports else None

#     def send_gcode(self, command):
#         """
#         Send a G-code command to GRBL.
#         In simulation mode, the command is logged to the debug log.
#         Errors during write/read are caught and handled.
#         """
#         print(f"Sending: {command}")
#         if self.simulate:
#             self.log_debug(f"Simulated send: {command}")
#             return

#         with self.serial_lock:
#             try:
#                 self.ser.write(f"{command}\n".encode())
#             except Exception as e:
#                 error_msg = f"Error writing command: {e}"
#                 print(error_msg)
#                 self.log_debug(error_msg)
#                 self.handle_serial_error(e)
#                 return

#             try:
#                 while True:
#                     response = self.ser.readline().decode('utf-8', errors='replace').strip()
#                     if response:
#                         print(f"GRBL Response: {response}")
#                     if response == "ok":
#                         break
#             except Exception as e:
#                 error_msg = f"Error reading response: {e}"
#                 print(error_msg)
#                 self.log_debug(error_msg)
#                 self.handle_serial_error(e)
#                 return

#     def handle_serial_error(self, error):
#         """
#         Handle serial communication errors by logging the error,
#         closing the serial port if necessary, and scheduling a reconnect.
#         """
#         self.log_debug(f"Serial error occurred: {error}. Attempting to reconnect...")
#         try:
#             if hasattr(self, 'ser') and self.ser:
#                 self.ser.close()
#         except Exception as close_err:
#             self.log_debug(f"Error closing serial port: {close_err}")
#         # Schedule a reconnect attempt after a short delay.
#         Clock.schedule_once(lambda dt: self.connect_to_grbl(), 1)

#     def log_debug(self, message):
#         """
#         Append a message to the debug log widget on the main thread.
#         """
#         Clock.schedule_once(lambda dt: self._append_debug(message), 0)

#     def _append_debug(self, message):
#         self.debug_log.text += message + "\n"
#         self.debug_log.cursor = (0, len(self.debug_log.text))

#     def on_button_release(self, instance):
#         """
#         Handle a directional button tap by sending a single jog command.
#         """
#         dx = instance.dx
#         dy = instance.dy
#         self.send_jog_command(dx, dy)

#     def send_jog_command(self, dx, dy):
#         """
#         Construct and send the jog command based on dx, dy, and the current jog step size.
#         """
#         step = self.jog_step
#         cmd = "$J=G21G91"
#         if dx:
#             cmd += f"X{dx * step}"
#         if dy:
#             cmd += f"Y{dy * step}"
#         cmd += f"F{FEEDRATE}"
#         self.send_gcode(cmd)

#     def on_step_change(self, instance, value):
#         """
#         Update the jog step size when the user modifies the TextInput.
#         """
#         try:
#             self.jog_step = int(value)
#         except ValueError:
#             self.jog_step = 1

#     def on_reconnect(self, instance):
#         """
#         Manually trigger a reconnect to the GRBL device.
#         This can be useful if a flag is raised (e.g., a limit switch is triggered)
#         and you need to reinitialize the connection.
#         """
#         self.log_debug("Manual reconnect triggered.")
#         # Attempt to reconnect immediately.
#         self.connect_to_grbl()

# # ---------------------
# # Example Integration
# # ---------------------
# if __name__ == '__main__':
#     from kivy.app import App
#     from kivy.uix.boxlayout import BoxLayout

#     class TestApp(App):
#         def build(self):
#             root = BoxLayout(orientation='vertical')
#             gantry_widget = GantryControlWidget()
#             root.add_widget(gantry_widget)
#             return root

#     TestApp().run()


import glob
import serial
import time
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label

# Constant feedrate as in your original code
FEEDRATE = 10000  # mm/min
FONT_SIZE = 32


class GantryControlWidget(BoxLayout):
    def __init__(self, **kwargs):
        super(GantryControlWidget, self).__init__(**kwargs)
        self.orientation = 'horizontal'
        self.spacing = 10
        self.padding = 10

        # Internal state variables
        self.jog_step = 3
        self.simulate = False  # When True, widget is in simulation mode.

        # ---------------------
        # LEFT PANEL: Directional Buttons
        # ---------------------
        left_panel = GridLayout(cols=3, rows=3, spacing=5, size_hint=(0.7, 1))
        # Each button is defined with text indicating the x/y direction.
        buttons = [
            {"text": "X- Y+", "dx": -1, "dy":  -1},
            {"text": "Y+",   "dx":  0, "dy":  -1},
            {"text": "X+ Y+", "dx":  1, "dy":  -1},
            {"text": "X-",   "dx": -1, "dy":  0},
            {"text": "",     "dx":  0, "dy":  0},  # Center: left blank.
            {"text": "X+",   "dx":  1, "dy":  0},
            {"text": "X- Y-", "dx": -1, "dy": 1},
            {"text": "Y-",   "dx":  0, "dy": 1},
            {"text": "X+ Y-", "dx":  1, "dy": 1}
        ]
        for b in buttons:
            if b["text"] == "":
                left_panel.add_widget(Label())
            else:
                btn = Button(text=b["text"], font_size=FONT_SIZE)
                # Store directional values as custom properties.
                btn.dx = b["dx"]
                btn.dy = b["dy"]
                # Bind only on_release so that a tap counts as a single press.
                btn.bind(on_release=self.on_button_release)
                left_panel.add_widget(btn)

        # ---------------------
        # RIGHT PANEL: Controls & Debug Log
        # ---------------------
        right_panel = BoxLayout(orientation='vertical', spacing=10, size_hint=(0.3, 1))

        # Step size controls.
        step_label = Label(text="Step Size (mm):", size_hint_y=0.1, font_size=FONT_SIZE)
        self.step_input = TextInput(text=str(self.jog_step), multiline=False,
                                    input_filter='int', size_hint_y=0.1, font_size=FONT_SIZE)
        self.step_input.bind(text=self.on_step_change)

        # Placeholder for any extra action.
        extra_button = Button(text="Reconnect to GRBL Device", size_hint_y=0.2, font_size=FONT_SIZE)
        
        # Debug log area (for simulation mode).
        debug_label = Label(text="Debug Log:", size_hint_y=0.1, font_size=FONT_SIZE)
        self.debug_log = TextInput(text="", readonly=True, multiline=True, size_hint_y=0.6, font_size=FONT_SIZE)

        right_panel.add_widget(step_label)
        right_panel.add_widget(self.step_input)
        right_panel.add_widget(extra_button)
        right_panel.add_widget(debug_label)
        right_panel.add_widget(self.debug_log)

        self.add_widget(left_panel)
        self.add_widget(right_panel)

        # Schedule the GRBL connection attempt.
        Clock.schedule_once(lambda dt: self.connect_to_grbl(), 0)

    def connect_to_grbl(self):
        """
        Attempt to connect to a GRBL device via serial. If no device is found,
        switch to simulation mode.
        """
        grbl_port = self.find_grbl_port()
        if not grbl_port:
            print("No GRBL device found, switching to simulation mode.")
            self.simulate = True
            self.log_debug("Simulation mode enabled: No GRBL device found.")
            return

        try:
            self.ser = serial.Serial(grbl_port, 9600, timeout=1)
            time.sleep(2)  # Allow GRBL to initialize.
            self.send_gcode("$X")  # Clear alarms.
            print(f"Connected to GRBL on {grbl_port}")
        except Exception as e:
            print(f"Error connecting to GRBL: {e}")
            self.simulate = True
            self.log_debug(f"Simulation mode enabled due to error: {e}")

    def find_grbl_port(self):
        ports = glob.glob("/dev/ttyUSB*")
        return ports[0] if ports else None

    def send_gcode(self, command):
        """
        Send a G-code command to GRBL. In simulation mode, log the command instead.
        """
        print(f"Sending: {command}")
        if self.simulate:
            self.log_debug(f"Simulated send: {command}")
            return

        try:
            self.ser.write(f"{command}\n".encode())
            while True:
                response = self.ser.readline().decode().strip()
                if response:
                    print(f"GRBL Response: {response}")
                if response == "ok":
                    break
        except Exception as e:
            print(f"Error sending command: {e}")
            self.log_debug(f"Error sending command: {e}")

    def log_debug(self, message):
        """
        Append a message to the debug log widget on the main thread.
        """
        Clock.schedule_once(lambda dt: self._append_debug(message), 0)

    def _append_debug(self, message):
        self.debug_log.text += message + "\n"
        self.debug_log.cursor = (0, len(self.debug_log.text))

    def on_button_release(self, instance):
        """
        Handle a button tap (on_release) by sending a single jog command.
        """
        dx = instance.dx
        dy = instance.dy
        self.send_jog_command(dx, dy)

    def send_jog_command(self, dx, dy):
        """
        Construct and send the jog command based on dx, dy, and the current step size.
        """
        step = self.jog_step
        cmd = "$J=G21G91"
        if dx:
            cmd += f"X{dx * step}"
        if dy:
            cmd += f"Y{dy * step}"
        cmd += f"F{FEEDRATE}"
        self.send_gcode(cmd)

    def on_step_change(self, instance, value):
        """
        Update the jog step size when the user modifies the TextInput.
        """
        try:
            self.jog_step = int(value)
        except ValueError:
            self.jog_step = 1

# ---------------------
# Example Integration
# ---------------------
if __name__ == '__main__':
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout

    class TestApp(App):
        def build(self):
            root = BoxLayout(orientation='vertical')
            gantry_widget = GantryControlWidget()
            root.add_widget(gantry_widget)
            return root

    TestApp().run()
