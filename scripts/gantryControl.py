'''
Contains wwidget to conenct and control gantry, as well as interface for manual gantry control and debug log

'''


import glob
import serial
import time
import threading
import sys

from kivy.uix.screenmanager import Screen

from kivy.uix.label import Label
from kivy.core.text import Label as CoreLabel

from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Ellipse, Line
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput   
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.app import App
from kivy.core.window import Window
Window.fullscreen = True



'''
Gantry parameters from testing mar 25

Max Y value: 430, 435 barely touching end ??
440 (445 reachable)
Home then move -y 11mm



'''


SQUARE_SIZE_MM = 50    # each square is 50mm
STEP_MM = 25  # each step is 25mm
try:
    from scripts.customWidgets import HorizontalLine, VerticalLine, IconButton, RoundedButton, headerLayout
    from scripts.hall import SenseLayer
    from scripts.servo import Servo
except:
    from customWidgets import HorizontalLine, VerticalLine, IconButton, RoundedButton, headerLayout
    from hall import SenseLayer

# Constant feedrate as in your original code
FEEDRATE = 15000  # mm/min

class gantryControl:
        def __init__(self, **kwargs):
            self.feed_rate = FEEDRATE
            #self.hall = SenseLayer()

            for key, value in kwargs.items():
                self.capture_move = value
                print(key, value)
                setattr(self, key, value)

            # Internal state variables
            self.deadzone_origin = (0, 425)

            self.jog_step = 4
            self.overshoot = 4
            self.magnet_state =  "MOVE MODE"
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
            


        def home(self):
            self.send_gcode("$H")

        def correct_position(self):
            self.home()
            self.send_gcode("$120=500") # X accl = 100
            self.send_gcode("$121=500") # Y accl = 100
            self.send_gcode("G21G91G1Y-11F15000")
            self.send_gcode("G92X0Y0Z0")
            self.servo = Servo()
            self.servo.begin()

        def list_serial_ports(self):
            if sys.platform.startswith('darwin'):
                # macOS: use a wildcard pattern
                ports = glob.glob('/dev/tty.usbmodem*')
            elif sys.platform.startswith('win'):
                # Windows: Try a range of COM ports
                ports = ['COM%s' % (i + 1) for i in range(256)]
            elif sys.platform.startswith('linux'):
                # Linux: use a wildcard pattern
                ports = glob.glob('/dev/ttyACM*')
            else:
                raise EnvironmentError('Unsupported platform')
            return ports

        def find_grbl_port(self, baudrate=115200, timeout=2):
            ports = self.list_serial_ports()
            print("Scanning ports:", ports)
            for port in ports:
                try:
                    print(f"Trying to open port: {port}")
                    ser = serial.Serial(port, baudrate, timeout=timeout)
                    # Allow time for GRBL to reset and output its welcome message.
                    time.sleep(2)
                    # Do not flush immediately to avoid discarding data.
                    welcome = ""
                    # Try reading lines for up to 3 seconds.
                    start_time = time.time()
                    while time.time() - start_time < 3:
                        line = ser.readline().decode('utf-8', errors='ignore').strip()
                        if line:
                            welcome += line + "\n"
                    print("Welcome message received:")
                    print(welcome)
                    if "Grbl" in welcome:
                        print(f"Found GRBL on port: {port}")
                        return ser  # Return the already-opened serial instance.
                    else:
                        ser.close()
                except Exception as e:
                    print(f"Could not open port {port}: {e}")
            return None

        def connect_to_grbl(self):
            """
            Attempt to connect to a GRBL device via serial.
            If no device is found or an error occurs, simulation mode is enabled.
            """
            grbl_serial = self.find_grbl_port()
            print(f"grbl_serial: {grbl_serial}")
            if not grbl_serial:
                print("No GRBL device found, switching to simulation mode.")
                self.simulate = True
                return

            try:
                self.simulate = False
                # Use the serial instance returned by find_grbl_port directly.
                self.ser = grbl_serial
                time.sleep(2)  # Allow GRBL to initialize.
                self.send_gcode("$X")  # Clear alarms.
                print(f"Connected to GRBL on port: {self.ser.port}")
                self.correct_position()
            except Exception as e:
                print(f"Error connecting to GRBL: {e}")
                self.simulate = True



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
                    #self.handle_serial_error(e)
                    return

                try:
                    while True:
                        response = self.ser.readline().decode('utf-8', errors='replace').strip()
                        if response:
                            print(f"GRBL Response: {response}")
                        if response == "ok":
                            break
                        elif response == "ALARM:1":
                            #self.log_debug("ALARM:1 - Resetting GRBL")
                            self.send_gcode("$X")
                            break   
                        
                except Exception as e:
                    error_msg = f"Error reading response: {e}"
                    print(error_msg)
                    #self.handle_serial_error(e)
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

        def send_coordinates_command(self, location):
            """
            Construct and send the jog command based on dx, dy, and the current jog step size.
            Figure out the gcode move command
            """
            x_offset = 0
            y_offset = 0
            x = location[0] + x_offset
            y = location[1] + y_offset

            cmd = "G21G90G1"
            if x:
                cmd += f"X{x}"
            if y:
                cmd += f"Y{y}"
            cmd += f"F{FEEDRATE}\n"
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

        def square_to_coord(self, square):
            """
            Converts a chess square string (e.g. "e2") to coordinates (x, y)
            in half‐step units using the following system:
            - h1 is (0,0)
            - x increases as rank increases (rank 1 → 0, rank 8 → 14)
            - y increases as file goes from h to a (h → 0, a → 14)
            This yields a difference of 2 between adjacent squares so that there are
            intermediate half‐steps between them.
            """
            file = square[0].lower()
            try:
                rank = int(square[1])
            except ValueError:
                raise ValueError("Invalid square: rank must be a number")
            x = (rank - 1) * 2   # Multiply by 2 to represent half-steps
            y = (ord('h') - ord(file)) * 2
            return (x, y)
        
        def interpret_chess_move(self, move_str, is_capture):
            """
            Given a move string (e.g. "e2e4") and a step_value (in mm),
            returns the relative displacement as a tuple (dx_mm, dy_mm).
            """
            if len(move_str) < 4:
                raise ValueError("Move string must be at least 4 characters (e.g. 'e2e4').")
            
            print(f"Interpreting move: {move_str}")

            print(f"Capture state: {is_capture}")

            
            start_square = move_str[:2]
            end_square = move_str[2:4]

            print(f"Move again: {start_square}, {end_square}")
            
            start_coord = self.square_to_coord(start_square)
            end_coord = self.square_to_coord(end_square)

            start_coord = (start_coord[0]*STEP_MM, start_coord[1]*STEP_MM)
            end_coord = (end_coord[0]*STEP_MM, end_coord[1]*STEP_MM)

            # Compute the difference in "steps"
            dx = end_coord[0] - start_coord[0]
            dy = end_coord[1] - start_coord[1]

            print(dx)
            print(dy)

            not_castle = True

            offset = STEP_MM

            print(f"Start square: {start_coord}, end square: {end_coord}")

            if start_square == 'e1' or start_square == 'e8':
                print("in castle")
                if end_square == 'c1':
                    # Rook path
                    path = [(0, 14*offset), (0, -6*offset)]
                    movements = self.parse_path_to_movement(path)
                    commands = self.movement_to_gcode(movements)
                    print(f"Rook comamnds: {commands}")
                    self.send_commands(commands)

                    # King_path
                    path = [(start_coord), (offset, offset), (0, 2*offset), (-offset, offset)]


                    movements = self.parse_path_to_movement(path)
                    commands = self.movement_to_gcode(movements)
                    print(f"Rook comamnds: {commands}")
                    self.send_commands(commands)
                    not_castle = False

                    
                elif end_square == 'g1':

                    # Rook path
                    path = [(0, 0), (0, 4*offset)]
                    movements = self.parse_path_to_movement(path)
                    commands = self.movement_to_gcode(movements)
                    print(f"rook comamnds: {commands}")
                    self.send_commands(commands)

                    # King_path
                    path = [(start_coord), (offset, -offset), (0, -2*offset), (-offset, -offset)]

                    movements = self.parse_path_to_movement(path)
                    commands = self.movement_to_gcode(movements)
                    print(f"king comamnds: {commands}")
                    self.send_commands(commands)
                    not_castle = False
                    

                if end_square == 'c8':
                    # Rook path
                    path = [(14*offset, 14*offset), (0, 6*offset)]
                    movements = self.parse_path_to_movement(path)
                    commands = self.movement_to_gcode(movements)
                    print(f"Rook comamnds: {commands}")
                    self.send_commands(commands)

                    # King_path
                    path = [(start_coord), (-offset, offset), (0, 2*offset), (offset, offset)]

                    movements = self.parse_path_to_movement(path)
                    commands = self.movement_to_gcode(movements)
                    print(f"king comamnds: {commands}")
                    self.send_commands(commands)
                    not_castle = False

                    
                elif end_square == 'g8':

                    # Rook path
                    path = [(14*offset, 0), (0, -4*offset)]
                    movements = self.parse_path_to_movement(path)
                    commands = self.movement_to_gcode(movements)
                    print(f"Rook comamnds: {commands}")
                    self.send_commands(commands)

                    # King_path
                    path = [(start_coord), (-offset, -offset), (0, -2*offset), (offset, -offset)]
                    not_castle = False

                else:
                    not_castle = True
                # For castling, need to move rook to new position, then slide king around it vertically. 
                # Need to know colour, , which rook is being moved
                
    
                
            
            if not_castle: 
                print('Not a castle')

                # Computational method for determineing if it is a knight.
                if min(abs(dx), abs(dy)) == 0 or abs(dx) == abs(dy):
                    print("Not a knight")

                    path = [(start_coord[0], start_coord[1]), (dx, dy)]   
                else:
                    print("Probably a horse")
                    angled_movement = (self.sign(dx) * offset, self.sign(dy)*offset)
                    print(angled_movement)

                    # inital offset is (sign(dx) * dx, sing(dy)*dy)
                    if abs(dx) > abs(dy):
                        path = [start_coord, angled_movement, (2*self.sign(dx)*offset, 0), angled_movement]
                    else:
                        path = [start_coord, angled_movement, (0, 2*self.sign(dy)*offset), angled_movement]
                 

            
            if is_capture:
                print('Is capture')
                # Take away 25mm from last movement, so piece is on the edge
                end_x, end_y = path[-1]
                new_end_x =  end_x - self.sign(end_x)*offset if not end_x == 0 else 0
                new_end_y = end_y - self.sign(end_y)*offset if not end_y == 0 else 0
                path[-1] = (new_end_x, new_end_y)
                print(f"Path for moving to piece to capture: {path}")
                movements = self.parse_path_to_movement(path)
                commands = self.movement_to_gcode(movements)
                print(f"Moving to capture piece: {commands}")
                self.send_commands(commands)


                #move piece off center in opposite direction
                captured_new_x = self.sign(end_x)*offset if not end_x == 0 else 0
                captured_new_y = self.sign(end_y)*offset if not end_y == 0 else 0
                path = [end_coord, (captured_new_x, captured_new_y)]

                print(f"Path for moving captured piece off square: {path}")


                #movements = self.parse_path_to_movement(path)
                commands = self.movement_to_gcode(path)
                print(f"Moving piece off center: : {commands}")
                self.send_commands(commands)      
                print(f"moving piece off center: {path}")
                  


                #Move capturing piece back to center

                path = [(end_coord[0] -self.sign(end_x)*offset, end_coord[1] -self.sign(end_y)*offset), (self.sign(end_x)*offset, self.sign(end_y)*offset)]

                print(f"Path for moving piece back to center: {path}")

                movements = self.parse_path_to_movement(path)
                commands = self.movement_to_gcode(movements)
                print(f"Moving piece to center comamnds: {commands}")
                self.send_commands(commands)


                dead_coordinates = (end_coord[0] + captured_new_x, end_coord[1] + captured_new_y)

                dead_x = self.deadzone_origin[0] - dead_coordinates[0]
                dead_y = self.deadzone_origin[1] - dead_coordinates[1]

                dz_x, dz_y = self.deadzone_origin

                path = [dead_coordinates, (0, offset*16 - dead_coordinates[1]), (dead_x, 0), (0, dz_y-offset*16)]

                print(f"moving to deadzone: {path}")


                # movements = self.parse_path_to_movement(path)
                # commands = self.movement_to_gcode(movements)
                # print(f" moving to deadzone: {commands}")
                # self.send_commands(commands)



                

                if dz_x == 400:
                    dz_x = -50
                    dz_y = 400

                self.deadzone_origin = (dz_x + 2*offset, dz_y)


            print(f"Interpreted move: {move_str} as dx={dx}, dy={dy} as {path}")

            
            return (path)


        def interpret_move(self, move_str):
            """
            Given a move string (e.g. "e2e4") and a step_value (in mm),
            returns the relative displacement as a tuple (dx_mm, dy_mm).
            """
            if len(move_str) < 4:
                raise ValueError("Move string must be at least 4 characters (e.g. 'e2e4').")
            
            print(f"Interpreting move: {move_str}")
            
            start_square = move_str[:2]
            end_square = move_str[2:4]
            
            start_coord = self.square_to_coord(start_square)
            end_coord = self.square_to_coord(end_square)

            print(f"Start square: {start_coord}, end square: {end_coord}")


            # Compute the difference in "steps"
            dx_steps = end_coord[0] - start_coord[0]
            dy_steps = end_coord[1] - start_coord[1]
            
            # Convert steps to mm
            dx_mm = dx_steps + start_coord[0]
            dy_mm = dy_steps + start_coord[1]

            #dx_mm = dx_steps * step_value
            #dy_mm = dy_steps * step_value

            path = [(start_coord[0], start_coord[1]), (dx_mm, dy_mm)]     


            print(f"Interpreted move: {move_str} as dx={dx_mm}, dy={dy_mm} as {path}")

            
            return (path)

        def send_command(self, coordinates):
            print(f"Sending command: {coordinates}")
            pass

        def sign(self, num):
            """Helper function: returns the sign of num."""
            if num > 0:
                return 1
            elif num < 0:
                return -1
            else:
                return 0
            
        def parse_path_to_movement(self, points):
            """
            Given a list of absolute points [(x, y), ...], this function returns a new list where:
            - The first element is the original starting point.
            - Each subsequent element is the relative displacement from that starting point,
                with colinear segments merged into a single vector.
            
            For example:
            Absolute points: [(0,300), (25,275), (50,300), (75,275)]
            After normalization (subtracting starting point (0,300)):
                [(0,0), (25,-25), (50,0), (75,-25)]
            Differences between normalized points:
                (25,-25), (25,25), (25,-25)
            Merging colinear segments (if applicable) and then
            computing cumulative relative positions gives:
                [(0,0), (25,-25), (50,0), (25,-25)]
            Finally, the function outputs:
                [(0,300), (25,-25), (50,0), (25,-25)]

            """
            if not points or len(points) < 2:
                return points
            
            if points[1][0] % 25 == 0 or points[1][1] % 25 ==0:
                return points
            else:
                points = [(x * STEP_MM, y * STEP_MM) for (x, y) in points]

            # Save the absolute starting point.
            base = points[0]

            # Convert all points into relative coordinates, so that the start is (0,0).
            rel_points = [(p[0] - base[0], p[1] - base[1]) for p in points]

            # Compute differences between consecutive relative points.
            diffs = []
            for i in range(1, len(rel_points)):
                dx = rel_points[i][0] - rel_points[i - 1][0]
                dy = rel_points[i][1] - rel_points[i - 1][1]
                diffs.append((dx, dy))

            # Helper to check if two vectors are colinear and in the same direction.
            def same_direction(v1, v2):
                # Cross product: if nonzero, vectors are not colinear.
                cross = v1[0] * v2[1] - v1[1] * v2[0]
                if cross != 0:
                    return False
                # Dot product > 0 ensures they're pointing in the same direction.
                return (v1[0] * v2[0] + v1[1] * v2[1]) > 0

            # Merge consecutive differences if they are colinear.
            merged = []
            current = diffs[0]
            for d in diffs[1:]:
                if same_direction(current, d):
                    # Sum the two differences.
                    current = (current[0] + d[0], current[1] + d[1])
                else:
                    merged.append(current)
                    current = d
            merged.append(current)

            # Rebuild the cumulative relative positions from the merged differences.
            cumulative = [(0, 0)]
            current_pos = (0, 0)
            for d in merged:
                current_pos = (current_pos[0] + d[0], current_pos[1] + d[1])
                cumulative.append(current_pos)

            # The final output:
            # The first element is the original absolute starting point.
            # Every subsequent element is the relative movement from the starting point.
            final_points = [base] + cumulative[1:]
            return final_points


        # def parse_path_to_movement(self, points):

        #     print(f"Points:{points}")
        #     """
        #     Given a list of points (x, y) representing the trajectory in half‑step units,
        #     returns a list of (dx, dy) moves where consecutive moves in the same direction
        #     are combined.
            
        #     NOTE: This function currently only returns differences between consecutive points.
        #     If you want to include the absolute starting coordinate as the first "move",
        #     you must add that explicitly.
            
        #     For example:
        #     Input: [(0,0), (1,0), (2,0), (2,1), (2,2), (3,2), (4,2)]
        #     Differences: (1,0), (1,0), (0,1), (0,1), (1,0), (1,0)
        #     Output: [(2,0), (0,2), (2,0)]
        #     """
        #     step_size = 1
        #     if not points or len(points) < 2:
        #         return []
            
        #     start = points[0]

        #     points[0] = (0,0)
            
        #     # Calculate differences between consecutive points.
        #     diffs = []
        #     for i in range(1, len(points)):
        #         print(points[i])
        #         print(points[i-1])
        #         dx = points[i][0] - points[i-1][0]
        #         dy = points[i][1] - points[i-1][1]
        #         diffs.append((dx, dy))
        #     print("diffs")
        #     print(diffs)
            
        #     movements = []
        #     # Initialize the current accumulated movement.
        #     current_dx, current_dy = diffs[0]
            
        #     # Loop over the remaining differences.
        #     for dx, dy in diffs[1:]:
        #         if self.sign(dx) == self.sign(current_dx) and self.sign(dy) == self.sign(current_dy):
        #             current_dx += dx
        #             current_dy += dy
        #             print(f'test: {current_dx, current_dy}')
        #         else:
        #             movements.append((current_dx * step_size, current_dy * step_size))
        #             current_dx, current_dy = dx, dy
        #             print(f'test2: {current_dx, current_dy}')
        #     movements.append((current_dx * step_size, current_dy * step_size))
            
        #     # If you want the starting coordinate (the absolute position of the first point)
        #     # to be included as the very first move, you could prepend it:
        #     print(f"movements almost done: {movements}")
        #     movements.insert(0, (start[0] * step_size, start[1] * step_size))

            
        #     return movements


        def send_commands(self, cmd_list):

            if self.simulate:
                time.sleep(2)
                print(f"Sent commands")
            else:
                
                for cmd in cmd_list:
                    self.finished = False
                    full_cmd = cmd + "\n"
                    self.send_gcode(full_cmd)
                    # Wait for GRBL response ("ok")
                    response = self.ser.readline().decode().strip()
                    while response != "ok":
                        # You might log the response or wait until "ok" arrives.
                        response = self.ser.readline().decode().strip()
                    print(f"Sent: {cmd}, Response: {response}")

                    while not self.finished:
                        self.ser.write(b'?')
                        status = self.ser.readline().decode().strip()
                        print(f"Status: {status}")
                        if '<Idle' in status:
                            self.finished = True
                        time.sleep(0.5)
                    print("Finished Sending commands")

            

        def path_to_gcode(self, move_list):
            """
            Given a list of moves (e.g., ["e2e4", "g8h6"]), converts them to relative
            displacement commands in G-code format.
            """

            print(f"move list: {move_list}")
            if self.magnet_state == "MAG OFF":
                self.send_gcode("M9") # off
            elif self.magnet_state == "MAG ON":
                self.send_gcode("M8") # on

            gcode_commands = []
            for i, move in enumerate(move_list):
                if i == 0:
                    gcode_commands.append(f"G21G90G1X{move[0]}Y{move[1]}F{FEEDRATE}")
                    if self.magnet_state == "MOVE MODE":
                        gcode_commands.append(f"M8") #Activate after initial movement
                elif i == len(move_list) - 1:
                    dx = self.sign(move_list[-1][0]) * self.overshoot
                    dy = self.sign(move_list[-1][1]) * self.overshoot

                    print(f"Overshoots: {dx, dy}")
                    gcode_commands.append(f"G21G91G1X{move[0]+dx}Y{move[1]+dy}F{FEEDRATE}")

                    gcode_commands.append(f"G21G91G1X{-dx}Y{-dy}F{FEEDRATE}")
                    # gcode_commands.append(f"M8") # deactivate after final movement
                    # gcode_commands.append(f"M9") # deactivate after final movement

                

                    if self.magnet_state == "MOVE MODE":
                        gcode_commands.append(f"M9") # deactivate after final movement
                else:
                    gcode_commands.append(f"G21G91G1X{move[0]}Y{move[1]}F{FEEDRATE}")


            
            return gcode_commands




        def movement_to_gcode(self, move_list):
            """
            Given a list of moves (e.g., ["e2e4", "g8h6"]), converts them to relative
            displacement commands in G-code format.
            """

            print(f"move list: {move_list}")
            if self.magnet_state == "MAG OFF":
                self.send_gcode("M9") # off
            elif self.magnet_state == "MAG ON":
                self.send_gcode("M8") # on

            gcode_commands = []
            for i, move in enumerate(move_list):
                if i == 0:
                    gcode_commands.append(f"G21G90G1X{move[0]}Y{move[1]}F{FEEDRATE}")
                    if self.magnet_state == "MOVE MODE":
                        gcode_commands.append(f"M8") #Activate after initial movement
                elif i == len(move_list) - 1:
                    dx = self.sign(move_list[-1][0]) * self.overshoot
                    dy = self.sign(move_list[-1][1]) * self.overshoot
                    gcode_commands.append(f"G21G91G1X{move[0]+dx}Y{move[1]+dy}F{FEEDRATE}")

                    gcode_commands.append(f"G21G91G1X{-dx}Y{-dy}F{FEEDRATE}")
                    # gcode_commands.append(f"M8") # deactivate after final movement
                    # gcode_commands.append(f"M9") # deactivate after final movement

                

                    if self.magnet_state == "MOVE MODE":
                        gcode_commands.append(f"M9") # deactivate after final movement
                else:
                    gcode_commands.append(f"G21G91G1X{move[0]}Y{move[1]}F{FEEDRATE}")


            
            return gcode_commands
        
        def magnet_control(self):
            if self.magnet_state == "MAG ON":
                self.send_gcode("M8")
            elif self.magnet_state == "MAG OFF":
                self.send_gcode("M9")

        



class GantryTargetWidget(Widget):

    
    """
    Draws an 8x10 grid:
      - The inner 8x8 area (rows 2 to 9, columns 0 to 7) is the chessboard.
      - The extra rows/columns serve as margins.
    A red dot is drawn on top whose position is maintained in half‑steps.
    The grid scales relative to the parent widget and is offset from the bottom‑left.
    When trail mode is active, each new dot center is appended to a continuous red line.
    
    The coordinate system is rotated 90° clockwise relative to standard chess so that:
      - Traditional h1 appears at the top right,
      - h8 appears at the top left,
      - a8 appears at the bottom left,
      - a1 appears at the bottom right.
    Border labels are drawn in the outermost margin cells.
    """
    def __init__(self, gantry_control, capture_move, **kwargs):
        super(GantryTargetWidget, self).__init__(**kwargs)
        self.capture_move = capture_move
        self.gantry_control = gantry_control
        self.cols = 8
        self.rows = 10
        self.square_size = None  # computed in update_canvas
        self.step_size = None    # half of square_size
        # Dot's position in half‑steps (range: 0 to 16 horizontally, 0 to 20 vertically)
        self.dot_step_x = 8
        self.dot_step_y = 11  
        # Offset (in pixels) from the widget's bottom‑left where the grid starts.
        self.offset_value = 50  
        # Trail points: list of (x,y) pixel positions.
        self.trail_points = []
        self.trail_enabled = False

        self.path = []
        # Lists for border labels.
        self.top_labels = []
        self.bottom_labels = []
        self.left_labels = []
        self.right_labels = []
        self.bind(pos=self.update_canvas, size=self.update_canvas)
        Clock.schedule_once(lambda dt: self.update_canvas(), 0)
        Clock.schedule_once(lambda dt: self.add_labels(), 0)
    
    def update_canvas(self, *args):
        self.canvas.clear()
        # Compute square size relative to parent's available size minus the offset.
        self.square_size = min((self.width - self.offset_value) / self.cols,
                               (self.height - self.offset_value) / self.rows)
        self.step_size = self.square_size / 2.0
        # The full grid origin (bottom‑left of drawn grid)
        grid_origin = (self.x + self.offset_value, self.y + self.offset_value)
        with self.canvas:
            # --- Draw extra two rows (rows 0 and 1) at the bottom ---
            for row in range(2):
                for col in range(self.cols):
                    x = grid_origin[0] + col * self.square_size
                    y = grid_origin[1] + row * self.square_size
                    Color(247/255.0, 182/255.0, 114/255.0, 1)
                    Rectangle(pos=(x, y), size=(self.square_size, self.square_size))
            # --- Draw chessboard (rows 2 to 9) ---
            for row in range(2, self.rows):
                for col in range(self.cols):
                    x = grid_origin[0] + col * self.square_size
                    y = grid_origin[1] + row * self.square_size
                    if (col + row) % 2 == 0:
                        #Color(189/255.0, 100/255.0, 6/255.0, 1)
                        Color(247/255.0, 182/255.0, 114/255.0, 1)
                    else:
                        #Color(247/255.0, 182/255.0, 114/255.0, 1)
                        Color(189/255.0, 100/255.0, 6/255.0, 1)
                    Rectangle(pos=(x, y), size=(self.square_size, self.square_size))

                    #square_label = f"{chr(ord('a') + (7 - col))}{row - 1}"
                    square_label = f"{chr(ord('h') - (7 - (row-2)))}{8-col}"
                    # Create a CoreLabel to render the text.
                    core_lbl = CoreLabel(text=square_label, font_size=self.square_size * 0.2, color=(0, 0, 0, 0.8))
                    core_lbl.refresh()
                    texture = core_lbl.texture
                    # Position the label in the bottom right of the square.
                    label_x = x + self.square_size * 0.7
                    label_y = y + self.square_size * 0.05
                    # Draw the label texture.
                    Rectangle(texture=texture, pos=(label_x, label_y), size=texture.size)
            # --- Draw grid lines ---
            Color(0, 0, 0, 1)
            for col in range(self.cols + 1):
                x = grid_origin[0] + col * self.square_size
                Line(points=[x, grid_origin[1], x, grid_origin[1] + self.rows * self.square_size], width=1)
            for row in range(self.rows + 1):
                y = grid_origin[1] + row * self.square_size
                Line(points=[grid_origin[0], y, grid_origin[0] + self.cols * self.square_size, y], width=1)
            # --- Draw the trail (continuous red line) ---
            if len(self.trail_points) >= 2:
                Color(1, 0, 0, 1)
                flat_points = [coord for pt in self.trail_points for coord in pt]
                Line(points=flat_points, width=2)
            # --- Draw the red dot ---
            dot_center_x = grid_origin[0] + self.dot_step_x * self.step_size
            dot_center_y = grid_origin[1] + self.dot_step_y * self.step_size
            dot_radius = self.step_size * 0.4
            Color(1, 0, 0, 1)
            Ellipse(pos=(dot_center_x - dot_radius, dot_center_y - dot_radius),
                    size=(dot_radius * 2, dot_radius * 2))
        self.update_labels()
    
    def add_labels(self):
        # Create 8 labels for each border if not already created.
        if len(self.top_labels) < 8:
            for i in range(8):
                lbl = Label(text="", halign="center", valign="middle", color=(0,0,0,1))
                self.top_labels.append(lbl)
                self.add_widget(lbl)
            for i in range(8):
                lbl = Label(text="", halign="center", valign="middle", color=(0,0,0,1))
                self.bottom_labels.append(lbl)
                self.add_widget(lbl)
            for j in range(8):
                lbl = Label(text="", halign="center", valign="middle", color=(0,0,0,1))
                self.left_labels.append(lbl)
                self.add_widget(lbl)
            for j in range(8):
                lbl = Label(text="", halign="center", valign="middle", color=(0,0,0,1))
                self.right_labels.append(lbl)
                self.add_widget(lbl)

            Clock.schedule_once(lambda dt: self.update_labels(), 0)

    
    def update_labels(self):
        # Ensure labels are present.
        if len(self.top_labels) < 8:
            self.add_labels()
        # Define the inner chessboard as the 8x8 area (rows 2 to 9, cols 0 to 7).
        grid_origin = (self.x + self.offset_value, self.y + self.offset_value)
        chess_origin = (grid_origin[0], grid_origin[1] + 2 * self.square_size)
        board_width = 8 * self.square_size
        board_height = 8 * self.square_size
        # Top labels (above the chessboard): Files in rotated coordinates.
        # In our rotated system, top-left is h8 and top-right is a8.
        top_files = ["h","g","f","e","d","c","b","a"]
        for i in range(8):
            lbl = self.top_labels[i]
            lbl.text = f"{top_files[i]}8"
            lbl.font_size = self.square_size * 0.4
            lbl.size = (self.square_size, self.square_size)
            lbl.pos = (chess_origin[0] + i * self.square_size, chess_origin[1] + board_height)
        # Bottom labels (below the chessboard): Files (h1 to a1)
        bottom_files = ["h","g","f","e","d","c","b","a"]
        for i in range(8):
            lbl = self.bottom_labels[i]
            lbl.text = f"{bottom_files[i]}1"
            lbl.font_size = self.square_size * 0.4
            lbl.size = (self.square_size, self.square_size)
            lbl.pos = (chess_origin[0] + i * self.square_size, chess_origin[1] - self.square_size)
        # Left labels (to the left of the chessboard): Ranks 8 to 1.
        for j in range(8):
            lbl = self.left_labels[j]
            lbl.text = f"{8 - j}"
            lbl.font_size = self.square_size * 0.4
            lbl.size = (self.square_size, self.square_size)
            lbl.pos = (chess_origin[0] - self.square_size, chess_origin[1] + (7 - j) * self.square_size)
        # Right labels (to the right of the chessboard): Ranks 8 to 1.
        for j in range(8):
            lbl = self.right_labels[j]
            lbl.text = f"{8 - j}"
            lbl.font_size = self.square_size * 0.4
            lbl.size = (self.square_size, self.square_size)
            lbl.pos = (chess_origin[0] + board_width, chess_origin[1] + (7 - j) * self.square_size)
    
    def move_dot(self, dx, dy):
        new_x = self.dot_step_x + dx
        new_y = self.dot_step_y + dy
        new_x = max(0, min(self.cols * 2, new_x))
        new_y = max(0, min(self.rows * 2, new_y))
        self.dot_step_x = new_x
        self.dot_step_y = new_y
        grid_origin = (self.x + self.offset_value, self.y + self.offset_value)
        new_center = (grid_origin[0] + self.dot_step_x * self.step_size,
                      grid_origin[1] + self.dot_step_y * self.step_size)
        if self.trail_enabled:
            self.trail_points.append(new_center)
            self.path.append(self.adjust_coords(new_x, new_y))
        self.update_canvas()
    
    def adjust_coords(self, x, y):
        return (15-x, 19-y)
    
    def clear_trail(self):
        self.trail_points = []
        self.path = []
        self.update_canvas()
    
    def move_dot_to_chess_square(self, square_str):
        """
        Given a traditional chess square (e.g., "e2"), moves the red dot to that square's center,
        using a rotated coordinate system (90° clockwise rotation):
          Standard chess: col = ord(file)-ord('a'), row = rank-1.
          Then: new_col = 7 - row, new_row = col.
          For the inner chessboard (rows 2 to 9), set:
            dot_step_x = 2 * new_col + 1,
            dot_step_y = 2 * (new_row + 2) + 1.
        For example, "h8": col=7, row=7 => new_col=0, new_row=7,
            dot_step_x = 2*0+1 = 1, dot_step_y = 2*(7+2)+1 = 19.
        """
        if len(square_str) != 2:
            return
        file = square_str[0].lower()
        try:
            rank = int(square_str[1])
        except ValueError:
            return
        col_index = ord(file) - ord('a')   # 0 to 7
        row_index = rank - 1               # 0 to 7
        new_col_index = 7 - row_index
        new_row_index = col_index
        self.dot_step_x = 2 * new_col_index + 1
        self.dot_step_y = 2 * (new_row_index + 2) + 1
        grid_origin = (self.x + self.offset_value, self.y + self.offset_value)
        new_center = (grid_origin[0] + self.dot_step_x * self.step_size,
                      grid_origin[1] + self.dot_step_y * self.step_size)
        if self.trail_enabled:
            self.trail_points.append(new_center)
        self.update_canvas()
    
    def process_chess_move(self, move_str, is_capture):
        """
        Processes a chess move string (e.g., "e2e4").
        Moves the red dot first to the "from" square then (after 0.5 sec) to the "to" square.
        """

        if len(move_str) < 4:
            return
        from_sq = move_str[:2]
        to_sq = move_str[2:4]
        
        self.path = (self.gantry_control.interpret_chess_move(move_str, is_capture))
        self.move_dot_to_chess_square(from_sq)
        Clock.schedule_once(lambda dt: self.move_dot_to_chess_square(to_sq), 0.5)

    
    
    # def square_to_coord(self, square):
    #         """
    #         Converts a chess square string (e.g. "e2") to coordinates (x, y)
    #         in half‐step units using the following system:
    #         - h1 is (0,0)
    #         - x increases as rank increases (rank 1 → 0, rank 8 → 14)
    #         - y increases as file goes from h to a (h → 0, a → 14)
    #         This yields a difference of 2 between adjacent squares so that there are
    #         intermediate half‐steps between them.
    #         """
    #         file = square[0].lower()
    #         try:
    #             rank = int(square[1])
    #         except ValueError:
    #             raise ValueError("Invalid square: rank must be a number")
    #         x = (rank - 1) * 2   # Multiply by 2 to represent half-steps
    #         y = (ord('h') - ord(file)) * 2
    #         return (x, y)
    
    def get_current_mm(self):
        # Get internal half-step coordinates:
        ix = self.dot_step_x
        iy = self.dot_step_y
        # Transform so that h1 (internal (15,19)) becomes (0,0) in half-steps.
        # In our mapping:
        #   h1: (15, 19)  => (15 - 15, 19 - 19) = (0, 0)
        #   a1: should be (0, 14) half-steps, etc.
        desired_x_steps = (15 - ix)
        desired_y_steps = (19 - iy)
        return (desired_x_steps * STEP_MM, desired_y_steps * STEP_MM)


class GantryControlWidget(Screen):
    """
    A composite widget that displays the gantry target board (grid) and arrow buttons.
    The arrow buttons move the red dot by 25mm per press.
    """
    def __init__(self, gantry_control=None, **kwargs):
        super(GantryControlWidget, self).__init__(**kwargs)
        self.orientation = 'vertical'
        # The target board occupies most of the space.

        self.capture_move = False

        self.root_layout = BoxLayout(orientation='vertical')

        self.header_layout = headerLayout(menu=False)
        self.body_layout = BoxLayout(orientation='horizontal')
        self.board_display = BoxLayout(orientation='vertical', padding=10)
        self.gantry_controls = BoxLayout(orientation='vertical')

        if gantry_control is None:
            self.gantry_control = gantryControl(capture_move = self.capture_move)
            self.gantry_control.connect_to_grbl()
        else: 
            self.gantry_control=gantry_control


        self.target_board = GantryTargetWidget(gantry_control=self.gantry_control, capture_move=self.capture_move)
        self.board_display.add_widget(self.target_board)

        # # Top row: file labels for the top border (rotated: top row shows h8, g8, ... a8)
        # self.top_row = BoxLayout(orientation="horizontal", size_hint=(1, 0.2))
        # self.bottom_row = BoxLayout(orientation="horizontal", size_hint=(1, 0.8))
        # self.top_label = BoxLayout(orientation="horizontal", size_hint=(0.8, 0.1))
        # self.side_label = BoxLayout(orientation="vertical", size_hint= (0.1, 0.9))


        # for rank in range(8, 0, -1):
        #     self.top_label.add_widget(Label(text=str(rank), halign="center", valign="middle"))

        # files = ["h", "g", "f", "e", "d", "c", "b", "a"]
        # for file in files:
        #     self.side_label.add_widget(Label(text=f"{file}", halign="left", valign="middle"))

        # self.side_label.add_widget(Widget(size_hint=(1, 0.4)))

        # self.top_row.add_widget(self.top_label)
        # self.top_row.add_widget(Widget(size_hint=(0.2, 0.2)))

        # self.bottom_row.add_widget(self.target_board)
        # self.bottom_row.add_widget(self.side_label)

        # self.board_display.add_widget(self.top_row)
        # self.board_display.add_widget(self.bottom_row)
    









        


        #self.target_board = GantryTargetWidget(size_hint=(1, 0.8))
        self.root_layout.add_widget(self.header_layout)
        self.root_layout.add_widget(HorizontalLine())
        self.root_layout.add_widget(self.body_layout)
        self.body_layout.add_widget(self.board_display)
        self.body_layout.add_widget(self.gantry_controls)
        
        # Create arrow buttons.
        btn_layout = GridLayout(size_hint=(1, 1), cols=3, rows=3)
        # We arrange buttons in a simple vertical layout with a nested grid.
        arrow_layout = BoxLayout(orientation='vertical')


        
        nw = IconButton(source="assets/nw.png", size_hint=(0.1, 0.1))
        n  = IconButton(source="assets/n.png",  size_hint=(0.1, 0.1))
        ne = IconButton(source="assets/ne.png", size_hint=(0.1, 0.1))
        w  = IconButton(source="assets/w.png",  size_hint=(0.1, 0.1))
        c = GoButton(gantry_control=self.gantry_control, target_board=self.target_board, size_hint=(0.1, 0.1))
        e  = IconButton(source="assets/e.png",  size_hint=(0.1, 0.1))
        sw = IconButton(source="assets/sw.png", size_hint=(0.1, 0.1))
        s  = IconButton(source="assets/s.png",  size_hint=(0.1, 0.1))
        se = IconButton(source="assets/se.png", size_hint=(0.1, 0.1))

        self.pathButton = PathPlanToggleButton(target_widget = self.target_board)
        self.chess_move_input = ChessMoveInput(target_widget=self.target_board,
                                               path_button=self.pathButton,
                                               on_move_callback=self.on_move_entered,
                                               size_hint=(1, 1))  
        c_clear  = ClearTrailButton(target_widget=self.target_board, path_toggle_button=self.pathButton, move_input=self.chess_move_input)
        controls = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        self.move_input_block = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))


        controls.add_widget(self.pathButton)
        controls.add_widget(c_clear)
        controls.add_widget(Button(text="Home", on_press=lambda instance: self.gantry_control.home()))


        btn_layout.add_widget(nw)
        btn_layout.add_widget(n)
        btn_layout.add_widget(ne)
        btn_layout.add_widget(w)
        btn_layout.add_widget(c)
        btn_layout.add_widget(e)
        btn_layout.add_widget(sw)
        btn_layout.add_widget(s)
        btn_layout.add_widget(se)

        self.gantry_controls.add_widget(btn_layout)
# Instantiate the modular chess move input.
              
        # self.move_input.bind(on_text_validate=self.target_board.process_chess_move)
        self.gantry_controls.add_widget(controls)

        self.move_input_block.add_widget(self.chess_move_input)

        capture_toggle = CaptureToggleButton(
            text="Capture Move",
            size_hint=(0.3, 1))
        capture_toggle.bind(state=self.on_toggle_state)

        self.move_input_block.add_widget(capture_toggle)
        self.gantry_controls.add_widget(self.move_input_block)
        #self.gantry_controls.add_widget(Label(text="Magnet Controls", size_hint=(1, 0.1)))
        self.magnet_control = MagnetControl(gantry_control=self.gantry_control, size_hint=(1, 0.1))
        #self.magnet_state = self.magnet_control.get_state()
        self.gantry_controls.add_widget(self.magnet_control)
        commandButton = SendCommandButton(gantry_control=self.gantry_control, target_widget=self.target_board, path_toggle_button=self.pathButton, move_input=self.chess_move_input, size_hint=(1, 0.1))

        self.gantry_controls.add_widget(commandButton)

                #         ↖ ↑ ↗
                # ← · →
                # ↙ ↓ ↘
        
        # middle_row = BoxLayout()
        # btn_left = Button(text="Left")
        # btn_right = Button(text="Right")
        # middle_row.add_widget(btn_left)
        # middle_row.add_widget(Label())
        # middle_row.add_widget(btn_right)
        
        # bottom_row = BoxLayout()
        # btn_down = Button(text="Down")
        # bottom_row.add_widget(Label())
        # bottom_row.add_widget(btn_down)
        # bottom_row.add_widget(Label())
        
        # arrow_layout.add_widget(top_row)
        # arrow_layout.add_widget(middle_row)
        # arrow_layout.add_widget(bottom_row)
        # btn_layout.add_widget(arrow_layout)
        # self.add_widget(btn_layout)
        
        # Bind the arrow buttons to move the dot.
        nw.bind(on_release=lambda inst: self.target_board.move_dot(-1, 1))
        n.bind(on_release=lambda inst: self.target_board.move_dot(0, 1))
        ne.bind(on_release=lambda inst: self.target_board.move_dot(1, 1))
        w.bind(on_release=lambda inst: self.target_board.move_dot(-1, 0))
        c.bind(on_release=lambda inst: self.target_board.move_dot(0, 0))
        e.bind(on_release=lambda inst: self.target_board.move_dot(1, 0))
        sw.bind(on_release=lambda inst: self.target_board.move_dot(-1, -1))
        s.bind(on_release=lambda inst: self.target_board.move_dot(0, -1))
        se.bind(on_release=lambda inst: self.target_board.move_dot(1, -1))
        self.add_widget(self.root_layout)
        # Optionally, you can add a label to display the current coordinate in mm.
        self.coord_label = Label(text="Target: -- mm", size_hint=(1, 0.1))
        # self.gantry_controls.add_widget(self.coord_label)
        # Update the label periodically.
        Clock.schedule_interval(self.update_label, 0.2)
    
    def update_label(self, dt):
        mm_coord = self.target_board.get_current_mm()
        self.coord_label.text = f"Target: {mm_coord[0]} mm, {mm_coord[1]} mm"

    def on_move_entered(self, move):
        # When a move is entered via the text input, force trail mode so the moves leave a trail.
        self.target_board.trail_enabled = True
        self.target_board.process_chess_move(move, self.capture_move)
        # Disable the text input and update its display with the trail coordinates.
        self.chess_move_input.disabled = True
        if self.target_board.trail_points:
            coords = [f"({int(x)},{int(y)})" for x, y in self.target_board.trail_points]
            self.chess_move_input.text = (move)


    def send_command(self):


        pass

    def on_toggle_state(self, instance, value):
        # Update the app-level variable based on the button's state
        self.capture_move = (value == "down")
        print(f"App Variable: capture_move = {self.capture_move}")



class PathPlanToggleButton(Button):
    """
    A toggle button that enables/disables trail updates.
    On first press, it changes to "Finish Path Plan" (green), enables trail mode,
    and disables the text input. On next press, it ends the path, disables trail mode,
    and then disables itself until the trail is cleared.
    """
    def __init__(self, target_widget, **kwargs):
        super(PathPlanToggleButton, self).__init__(**kwargs)
        self.target_widget = target_widget
        self.text = "Start Path Plan"
        self.background_color = [0.8, 0.8, 0.8, 1]
        self.bind(on_release=self.toggle_path)

    def adjust_coords(self, x, y):
        return (15-x, 19-y)
    
    def toggle_path(self, instance):
        if not self.target_widget.trail_enabled:
            # Enable trail mode.
            self.target_widget.trail_enabled = True
            self.text = "Finish Path Plan"
            self.background_color = [0, 1, 0, 1]
            board_origin = (self.target_widget.x + self.target_widget.offset_value,
                            self.target_widget.y + self.target_widget.offset_value)
            current_center = (board_origin[0] + self.target_widget.dot_step_x * self.target_widget.step_size,
                              board_origin[1] + self.target_widget.dot_step_y * self.target_widget.step_size)
            self.target_widget.trail_points.append(current_center)
            print((self.target_widget.dot_step_x, self.target_widget.dot_step_y))
            adjusted_path = self.adjust_coords(self.target_widget.dot_step_x, self.target_widget.dot_step_y)
            self.target_widget.path.append(adjusted_path)
            self.target_widget.update_canvas()
            # Disable the text input.
            if self.parent and hasattr(self.parent, 'chess_move_input'):
                self.parent.chess_move_input.disabled = True
        else:
            # Finish the path: disable trail mode and disable this button.
            self.target_widget.trail_enabled = False
            print("Path Plan finished. Trail path:", self.target_widget.path)

            self.text = "Path Plan Finished"
            self.background_color = [0.5, 0.5, 0.5, 1]
            self.disabled = True

class ClearTrailButton(Button):
    """
    A button that clears the current trail, resets the path planning controls,
    and clears & re-enables the text input.
    """
    def __init__(self, target_widget, path_toggle_button, move_input, **kwargs):
        super(ClearTrailButton, self).__init__(**kwargs)
        self.target_widget = target_widget
        self.path_toggle_button = path_toggle_button
        self.move_input = move_input
        self.text = "Clear Trail"
        self.background_color = [1, 0, 0, 1]
        self.bind(on_release=self.clear_trail)
    
    def clear_trail(self, instance):
        self.target_widget.clear_trail()
        self.target_widget.trail_enabled = False
        self.path_toggle_button.text = "Start Path Plan"
        self.path_toggle_button.background_color = [0.8, 0.8, 0.8, 1]
        self.path_toggle_button.disabled = False
        self.move_input.text = ""
        self.move_input.disabled = False

class GoButton(Button):
    """
    A button that clears the current trail, resets the path planning controls,
    and clears & re-enables the text input.
    """
    def __init__(self, gantry_control, target_board, **kwargs):
        super(GoButton, self).__init__(**kwargs)
        self.gantry_control = gantry_control
        self.target_board = target_board
        self.text = "Go"
        self.font_size = 40
        self.background_color = [0, 0, 0, 1]
        self.bind(on_release=self.send_commands)


    def send_commands(self, instance):
        dot_location = self.target_board.get_current_mm()
        print(f"Sending command: {dot_location}")
        if not self.gantry_control.simulate:
            self.gantry_control.send_coordinates_command(dot_location)
    
    




class SendCommandButton(Button):
    """
    A button that clears the current trail and resets the path plan toggle.
    """
    def __init__(self, gantry_control, target_widget, path_toggle_button, move_input, **kwargs):
        super(SendCommandButton, self).__init__(**kwargs)
        self.target_widget = target_widget
        self.path_toggle_button = path_toggle_button
        self.move_input = move_input
        self.gantry_control = gantry_control

        self.text = "Send Command"
        self.background_color = [1, 0, 0, 1]
        self.bind(on_release=self.send_command)
    
    def send_command(self, instance):
        #self.gantry_control.interpret_move(self.move_input.text, STEP_MM)
        print("Path Plan finished HAHA. Trail path:", self.target_widget.path)
        movements = self.gantry_control.parse_path_to_movement(self.target_widget.path)
        commands = self.gantry_control.movement_to_gcode(movements)
        print(f"Sending movements: {movements}")
        print(f"Sending commands: {commands}")

        if not self.gantry_control.simulate:
            self.gantry_control.send_commands(commands)

        self.target_widget.clear_trail()
        self.target_widget.trail_enabled = False
        self.path_toggle_button.text = "Start Path Plan"
        self.path_toggle_button.background_color = [0.8, 0.8, 0.8, 1]
        self.path_toggle_button.disabled = False
        self.move_input.text = ""
        self.move_input.disabled = False
        self.path = []
        
class MagnetControl(BoxLayout):
    def __init__(self, gantry_control, **kwargs):
        super(MagnetControl, self).__init__(**kwargs)
        self.orientation = 'horizontal'
        self.spacing = 0  # No gap between buttons so they look continuous.
        self.gantry_control = gantry_control
        
        # Define the three options.
        options = ["MAG OFF", "MOVE MODE", "MAG ON"]
        
        # Create three ToggleButtons that belong to the same group.
        self.buttons = []
        for option in options:
            btn = ToggleButton(text=option,
                               group="segmented",
                               background_normal='',
                               background_down='',
                               # Normal (unselected) background color.
                               background_color=[0.8, 0.8, 0.8, 1],
                               color=[0, 0, 0, 1],
                               size_hint=(1, 1))
            btn.bind(state=self.on_button_state)
            self.buttons.append(btn)
            self.add_widget(btn)
        
        # Set a default selection.
        self.buttons[1].state = 'down'

    def on_button_state(self, instance, value):
        # When the button is selected, use a highlight color; otherwise, the normal color.
        if value == 'down':
            instance.background_color = [0.2, 0.6, 1, 1]  # highlight (blue)
        else:
            instance.background_color = [0.8, 0.8, 0.8, 1]
        self.gantry_control.magnet_state = self.get_state()
        self.gantry_control.magnet_control()

    def get_state(self):
        # Return the text of the currently selected button.
        for btn in self.buttons:
            if btn.state == 'down':
                return btn.text
        return None     
    
class CaptureToggleButton(ToggleButton):
    def on_state(self, instance, value):
        # Update a property on the widget itself (or notify the app)
        self.is_capture = (value == "down")
        print(f"Toggle Button: capture_move = {self.is_capture}")



class ChessMoveInput(TextInput):
    """
    A modular text input widget that either accepts traditional chess moves (e.g. "e2e4")
    or displays the current trail's coordinates if a path exists.
    It also disables the path toggle button when there is any text.
    """
    def __init__(self, target_widget, path_button, on_move_callback=None, **kwargs):
        super(ChessMoveInput, self).__init__(**kwargs)
        self.multiline = False
        self.hint_text = "Enter chess move (e.g. e2e4)"
        self.target_widget = target_widget
        self.path_button = path_button
        self.on_move_callback = on_move_callback
        self.bind(on_text_validate=self.handle_move)
        self.bind(text=self.on_text_change)
    
    def on_text_change(self, instance, value):
        # Disable the path button if there is any text.
        
        self.path_button.disabled = bool(value.strip())

    
    def handle_move(self, instance):
        move = self.text.strip().lower()
        # If a path already exists, display its coordinates.
        if self.target_widget.trail_points:
            # coords = [f"({int(x)},{int(y)})" for x, y in self.target_widget.trail_points]
            # self.text = "Path: " + " -> ".join(coords)
            self.text = "hello"
            self.disabled = True
        else:
            if self.on_move_callback and move:
                # Force trail mode on so that the movement leaves a trail.
                self.target_widget.trail_enabled = True
                self.on_move_callback(move)
            #self.text = ""
    



class TrailWidget(Widget):
    def update_trail_with_points(self, points):
        self.canvas.clear()
        if len(points) >= 2:
            flat_points = [coord for p in points for coord in p]
            with self.canvas:
                Color(1, 0, 0, 1)
                Line(points=flat_points, width=2)
    def clear_trail(self):
        self.canvas.clear()


# --- For testing the widget in an app ---
class TestApp(App):
    def build(self):
        return GantryControlWidget()

if __name__ == '__main__':
    TestApp().run()














