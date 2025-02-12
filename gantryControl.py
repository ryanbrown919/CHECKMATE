import glob
import serial
import time
import threading

from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label

# Constant feedrate as in your original code
FEEDRATE = 10000  # mm/min

class GantryControlWidget(BoxLayout):
    def __init__(self, **kwargs):
        super(GantryControlWidget, self).__init__(**kwargs)
        self.orientation = 'horizontal'
        self.spacing = 10
        self.padding = 10

        # Internal state variables
        self.jog_step = 1
        self.simulate = False  # When True, widget is in simulation mode.
        self.serial_lock = threading.Lock()
        self.handling_limit_switch = False  # Prevent re-entrant handling

        # ---------------------
        # LEFT PANEL: Directional Buttons
        # ---------------------
        left_panel = GridLayout(cols=3, rows=3, spacing=5, size_hint=(0.7, 1))
        # Define directional buttons with text indicating x/y movements.
        buttons = [
            {"text": "X- Y+", "dx": -1, "dy":  1},
            {"text": "Y+",   "dx":  0, "dy":  1},
            {"text": "X+ Y+", "dx":  1, "dy":  1},
            {"text": "X-",   "dx": -1, "dy":  0},
            {"text": "",     "dx":  0, "dy":  0},  # Center is left blank.
            {"text": "X+",   "dx":  1, "dy":  0},
            {"text": "X- Y-", "dx": -1, "dy": -1},
            {"text": "Y-",   "dx":  0, "dy": -1},
            {"text": "X+ Y-", "dx":  1, "dy": -1}
        ]
        for b in buttons:
            if b["text"] == "":
                left_panel.add_widget(Label())
            else:
                btn = Button(text=b["text"], font_size=24)
                btn.dx = b["dx"]
                btn.dy = b["dy"]
                # Bind only on_release so that each tap sends one command.
                btn.bind(on_release=self.on_button_release)
                left_panel.add_widget(btn)

        # ---------------------
        # RIGHT PANEL: Controls & Debug Log
        # ---------------------
        right_panel = BoxLayout(orientation='vertical', spacing=10, size_hint=(0.3, 1))

        # Step size controls.
        step_label = Label(text="Step Size (mm):", size_hint_y=0.1)
        self.step_input = TextInput(text=str(self.jog_step), multiline=False,
                                    input_filter='int', size_hint_y=0.1)
        self.step_input.bind(text=self.on_step_change)

        # Reconnect button now repurposed as manual reconnect.
        reconnect_button = Button(text="Reconnect", size_hint_y=0.2)
        reconnect_button.bind(on_release=self.on_reconnect)

        # Debug log area (visible in simulation mode or upon errors).
        debug_label = Label(text="Debug Log:", size_hint_y=0.1)
        self.debug_log = TextInput(text="", readonly=True, multiline=True, size_hint_y=0.6)

        right_panel.add_widget(step_label)
        right_panel.add_widget(self.step_input)
        right_panel.add_widget(reconnect_button)
        right_panel.add_widget(debug_label)
        right_panel.add_widget(self.debug_log)

        self.add_widget(left_panel)
        self.add_widget(right_panel)

        # Schedule the GRBL connection attempt after initialization.
        Clock.schedule_once(lambda dt: self.connect_to_grbl(), 0)

    def connect_to_grbl(self):
        """
        Attempt to connect to a GRBL device via serial.
        If no device is found or an error occurs, simulation mode is enabled.
        """
        grbl_port = self.find_grbl_port()
        if not grbl_port:
            print("No GRBL device found, switching to simulation mode.")
            self.simulate = True
            self.log_debug("Simulation mode enabled: No GRBL device found.")
            return

        try:
            self.ser = serial.Serial(grbl_port, 115200, timeout=1)
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
        Send a G-code command to GRBL.
        In simulation mode, the command is logged to the debug log.
        Errors during write/read are caught and handled.
        If an ALARM response (limit switch) is detected, safe recovery is scheduled.
        """
        print(f"Sending: {command}")
        if self.simulate:
            self.log_debug(f"Simulated send: {command}")
            return

        with self.serial_lock:
            try:
                self.ser.write(f"{command}\n".encode())
            except Exception as e:
                error_msg = f"Error writing command: {e}"
                print(error_msg)
                self.log_debug(error_msg)
                self.handle_serial_error(e)
                return

            # Wait for a response with a timeout so we don't block forever.
            start_time = time.time()
            timeout = 5  # seconds
            while True:
                if time.time() - start_time > timeout:
                    self.log_debug("Timeout waiting for GRBL response.")
                    break
                response = self.ser.readline().decode('utf-8', errors='replace').strip()
                if response:
                    print(f"GRBL Response: {response}")
                    if response.startswith("ALARM:"):
                        self.log_debug(f"Limit switch triggered: {response}")
                        # Schedule safe recovery asynchronously.
                        Clock.schedule_once(lambda dt: self.handle_limit_switch(response), 0)
                        break
                    if response == "ok":
                        break

    def handle_limit_switch(self, alarm_msg):
        """
        Automatically handle a triggered limit switch by resetting the alarm
        and sending a safe jog command to move the carriage away from the end stop.
        This function is scheduled asynchronously so it runs outside the serial lock.
        """
        if self.handling_limit_switch:
            return  # Already handling one.
        self.handling_limit_switch = True
        self.log_debug(f"Handling limit switch alarm: {alarm_msg}")

        # Define a helper function to perform safe recovery.
        def safe_recovery(dt):
            # First, clear the alarm state.
            self.send_gcode("$X")
            # Define a safe move away from the limit switch.
            safe_distance = 5  # mm (adjust as needed)
            safe_command = f"$J=G21G91X{safe_distance}Y{safe_distance}F{FEEDRATE}"
            self.log_debug(f"Sending safe jog command: {safe_command}")
            self.send_gcode(safe_command)
            self.handling_limit_switch = False

        # Schedule safe recovery immediately (or after a brief pause if desired).
        Clock.schedule_once(safe_recovery, 0)

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
            self.log_debug(f"Error closing serial port: {close_err}")
        # Schedule a reconnect attempt after a short delay.
        Clock.schedule_once(lambda dt: self.connect_to_grbl(), 1)

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
        Handle a directional button tap by sending a single jog command.
        """
        dx = instance.dx
        dy = instance.dy
        self.send_jog_command(dx, dy)

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
        """
        self.log_debug("Manual reconnect triggered.")
        self.connect_to_grbl()

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
#         self.jog_step = 1
#         self.simulate = False  # When True, widget is in simulation mode.
#         self.serial_lock = threading.Lock()

#         # ---------------------
#         # LEFT PANEL: Directional Buttons
#         # ---------------------
#         left_panel = GridLayout(cols=3, rows=3, spacing=5, size_hint=(0.7, 1))
#         # Define directional buttons with text indicating x/y movements.
#         buttons = [
#             {"text": "X- Y+", "dx": -1, "dy":  1},
#             {"text": "Y+",   "dx":  0, "dy":  1},
#             {"text": "X+ Y+", "dx":  1, "dy":  1},
#             {"text": "X-",   "dx": -1, "dy":  0},
#             {"text": "",     "dx":  0, "dy":  0},  # Center is left blank.
#             {"text": "X+",   "dx":  1, "dy":  0},
#             {"text": "X- Y-", "dx": -1, "dy": -1},
#             {"text": "Y-",   "dx":  0, "dy": -1},
#             {"text": "X+ Y-", "dx":  1, "dy": -1}
#         ]
#         for b in buttons:
#             if b["text"] == "":
#                 left_panel.add_widget(Label())
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
#         step_label = Label(text="Step Size (mm):", size_hint_y=0.1)
#         self.step_input = TextInput(text=str(self.jog_step), multiline=False,
#                                     input_filter='int', size_hint_y=0.1)
#         self.step_input.bind(text=self.on_step_change)

#         # Reconnect button (extra action) to manually reconnect to the device.
#         reconnect_button = Button(text="Reconnect", size_hint_y=0.2)
#         reconnect_button.bind(on_release=self.on_reconnect)

#         # Debug log area (visible in simulation mode or upon errors).
#         debug_label = Label(text="Debug Log:", size_hint_y=0.1)
#         self.debug_log = TextInput(text="", readonly=True, multiline=True, size_hint_y=0.6)

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
