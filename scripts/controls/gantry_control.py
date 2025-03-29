
import glob
import serial
import time
import threading
import sys

from transitions import Machine
from kivy.clock import Clock

FEEDRATE=15000
STEP_MM = 25


class GantryControl:
        def __init__(self, **kwargs):
            #self.feed_rate = FEEDRATE
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
            self.send_gcode("$120=600") # X accl = 100
            self.send_gcode("$121=600") # Y accl = 100
            self.send_gcode("G21G91G1Y-11F15000")
            self.send_gcode("G92X0Y0Z0")
            # self.servo = Servo()
            # self.servo.begin()

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



                

                if dz_x == 350:
                    dz_x = -50
                    dz_y = 400

                self.deadzone_origin = (dz_x + 2*offset, dz_y)


            print(f"Interpreted move: {move_str} as dx={dx}, dy={dy} as {path}")

            movements = self.parse_path_to_movement(path)
            commands = self.movement_to_gcode(movements)
            print(f"Last move: {commands}")
            self.send_commands(commands)

            
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


class ClockLogic:
    def __init__(self, total_time=300, enable_increment=True, increment_time=5, increment_threshold=10, timer_enabled=True):
        self.total_time = total_time
        self.enable_increment = enable_increment
        self.increment_time = increment_time
        self.increment_threshold = increment_threshold
        self.timer_enabled = timer_enabled
        # self.gantry = gantry

        self.white_time = total_time
        self.black_time = total_time
        self.active_player = 1  # 1 for player1, 2 for player2
        self.paused = True     # False = running, True = paused

    def update(self, dt):
        """Call this method regularly to update the active player's clock."""
        if self.paused:
            return
        if self.active_player == 1 and self.white_time > 0:
            self.white_time = max(0, self.white_time - dt)
        elif self.active_player == 2 and self.black_time > 0:
            self.black_time = max(0, self.black_time - dt)

    def toggle_active_player(self):
        """
        Switch the active player. If increment is enabled and the current player's remaining
        time is below the threshold, add extra seconds.
        """
        if self.enable_increment:
            if self.active_player == 1 and self.white_time < self.increment_threshold:
                self.white_time += self.increment_time
                print("Incremented player 1 time by", self.increment_time)
            elif self.active_player == 2 and self.black_time < self.increment_threshold:
                self.black_time += self.increment_time
                print("Incremented player 2 time by", self.increment_time)
        self.active_player = 2 if self.active_player == 1 else 1
        print("Switched active player to", self.active_player)
        # self.gantry.servo.toggle()

    def toggle_pause(self):
        """Toggle between pause and play modes."""
        self.paused = not self.paused
        if self.paused:
            print("Paused")
        else:
            print("Resumed")

    def reset(self):
        """Reset both clocks to the initial total time and set active player to 1."""
        self.white_time = self.total_time
        self.black_time = self.total_time
        self.active_player = 1
        self.paused = False
        print("Clocks have been reset.")

    def format_time(self, seconds):
        """Return a string in mm:ss format."""
        minutes = int(seconds) // 60
        secs = int(seconds) % 60
        return f"{minutes:02d}:{secs:02d}"

    def update_display(self, dt):
        """Update the ChessClock and refresh the display labels."""
        self.clock_instance.update(dt)
        self.player1_label.text = self.format_time(self.clock_instance.white_time)
        self.player2_label.text = self.format_time(self.clock_instance.black_time)

    def on_pause(self, instance):
        """Toggle pause and update the button text."""
        self.clock_instance.toggle_pause()
        self.pause_button.text = "Play" if self.clock_instance.paused else "Pause"

    def on_reset(self, instance):
        """Reset the clock and update the display immediately."""
        self.clock_instance.reset()
        self.player1_label.text = self.format_time(self.clock_instance.white_time)
        self.player2_label.text = self.format_time(self.clock_instance.black_time)
        self.pause_button.text = "Pause"
