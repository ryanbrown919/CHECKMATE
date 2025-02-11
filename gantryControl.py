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
        self.active_movements = {}
        self.jog_step = 1
        self.simulate = False  # When True, widget is in simulation mode.

        # ---------------------
        # LEFT PANEL: Directional Buttons
        # ---------------------
        left_panel = GridLayout(cols=3, rows=3, spacing=5, size_hint=(0.7, 1))
        # Define each button with text indicating the movement direction.
        buttons = [
            {"text": "X- Y+", "dx": -1, "dy":  1, "id": "upleft"},
            {"text": "Y+",   "dx":  0, "dy":  1, "id": "up"},
            {"text": "X+ Y+", "dx":  1, "dy":  1, "id": "upright"},
            {"text": "X-",   "dx": -1, "dy":  0, "id": "left"},
            {"text": "",     "dx":  0, "dy":  0, "id": "center"},
            {"text": "X+",   "dx":  1, "dy":  0, "id": "right"},
            {"text": "X- Y-", "dx": -1, "dy": -1, "id": "downleft"},
            {"text": "Y-",   "dx":  0, "dy": -1, "id": "down"},
            {"text": "X+ Y-", "dx":  1, "dy": -1, "id": "downright"}
        ]
        for b in buttons:
            if b["id"] == "center":
                left_panel.add_widget(Label())
            else:
                btn = Button(text=b["text"], font_size=24)
                btn.dx = b["dx"]
                btn.dy = b["dy"]
                btn.direction_id = b["id"]
                btn.bind(on_press=self.on_move_press)
                btn.bind(on_release=self.on_move_release)
                left_panel.add_widget(btn)

        # ---------------------
        # RIGHT PANEL: Controls & Debug Log
        # ---------------------
        right_panel = BoxLayout(orientation='vertical', spacing=10, size_hint=(0.3, 1))

        # Step size controls
        step_label = Label(text="Step Size (mm):", size_hint_y=0.1)
        self.step_input = TextInput(text=str(self.jog_step), multiline=False,
                                    input_filter='int', size_hint_y=0.1)
        self.step_input.bind(text=self.on_step_change)

        # Placeholder for any extra action
        extra_button = Button(text="Reconnect to GRBL", size_hint_y=0.2)
        
        # Debug log area (visible in simulation mode)
        debug_label = Label(text="Debug Log:", size_hint_y=0.1)
        self.debug_log = TextInput(text="", readonly=True, multiline=True, size_hint_y=0.6)

        right_panel.add_widget(step_label)
        right_panel.add_widget(self.step_input)
        right_panel.add_widget(extra_button)
        right_panel.add_widget(debug_label)
        right_panel.add_widget(self.debug_log)

        # Add both panels to the widget.
        self.add_widget(left_panel)
        self.add_widget(right_panel)

        # Schedule the connection attempt after initialization.
        Clock.schedule_once(lambda dt: self.connect_to_grbl(), 0)

    def connect_to_grbl(self):
        """
        Attempt to connect to a GRBL device via serial. If no device is found
        or an error occurs, the widget switches to simulation mode.
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
        Send a G-code command to GRBL. In simulation mode, append the command
        to the debug log instead.
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

    def send_jog_command(self, dx, dy):
        """
        Construct and send the jogging command based on dx, dy, and the current
        jog step size.
        """
        step = self.jog_step
        cmd = "$J=G21G91"
        if dx:
            cmd += f"X{dx * step}"
        if dy:
            cmd += f"Y{dy * step}"
        cmd += f"F{FEEDRATE}"
        self.send_gcode(cmd)

    def movement_thread(self, dx, dy, direction_id):
        """
        This thread repeatedly sends jog commands until the movement is stopped.
        """
        self.active_movements[direction_id] = True
        while self.active_movements.get(direction_id, False):
            self.send_jog_command(dx, dy)
            time.sleep(0.1)
        print(f"Stopped movement: {direction_id}")

    def on_extra_press(self, instance):
        
        self.connect_to_grbl()


    def on_move_press(self, instance):
        """
        Start a movement thread when a directional button is pressed.
        """
        dx = instance.dx
        dy = instance.dy
        direction_id = instance.direction_id
        t = threading.Thread(target=self.movement_thread, args=(dx, dy, direction_id))
        t.daemon = True
        t.start()

    def on_move_release(self, instance):
        """
        Stop the movement when the directional button is released.
        """
        direction_id = instance.direction_id
        self.active_movements[direction_id] = False

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
            # Instantiate the GantryControlWidget and add it to the app.
            gantry_widget = GantryControlWidget()
            root.add_widget(gantry_widget)
            return root

    TestApp().run()
