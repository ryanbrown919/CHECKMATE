
import glob
import serial
import time
import threading
import sys

# from transitions import Machine
from kivy.clock import Clock

STEP_MM = 25

class GantryControl:
        def __init__(self, **kwargs):
            #self.hall = SenseLayer()

            for key, value in kwargs.items():
                self.capture_move = value
                print(key, value)
                setattr(self, key, value)

            # Internal state variables
            self.nextdead_white = (0, 435)
            self.nextdead_black = (350, 435)

            self.white_captured = []
            self.black_captured = []

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
            
            self.ser = serial.Serial("/dev/ttyACM0", 115200)
            self.send("\r\n\r")
            time.sleep(2)
            self.ser.flushInput()  
            self.position = None


        def home(self):
            self.send("$H")
            self.send("G91 X0 Y-11")  # Center under H1
            self.send("G92 X0 Y0 Z0") # Reposition coordinate system
            self.set_velocity(15000)
            self.set_acceleration(700)

        def send(self, command):
            with self.serial_lock:
                self.ser.write(str.encode(command + "\n"))
        
        def set_velocity(self, velocity):
            self.send(f"$110={velocity}")
            self.send(f"$111={velocity}")
        
        def set_acceleration(self, acceleration):
            self.send(f"$120={acceleration}")
            self.send(f"$121={acceleration}")
        
        def get_position(self, max_attempts=10, delay=0.1):
            for _ in range(max_attempts):
                self.send("?")
                response = self.serial.readline().decode().strip()
                
                if 'MPos:' in response:
                    pos_part = response.split('MPos:')[1].split('|')[0]
                    coords = pos_part.split(',')
                elif 'WPos:' in response:
                    pos_part = response.split('WPos:')[1].split('|')[0]
                    coords = pos_part.split(',')
                else:
                    continue 
                    
                x = int(float(coords[0]) + 475)
                y = int(float(coords[1]) + 486)
                
                return x, y   
            return None, None  

        def is_idle(self):
            self.send("?")
            response = self.ser.readline().decode().strip()

            if "Idle" in response:
                return True
            else:
                return False

        def move(self, x, y):
            ''' Absolute positioning'''
            self.send(f"G90 X{x} Y{y}")
            time.sleep(0.05) 

            self.ser.flushInput()
            while True:
                if self.is_idle():
                    self.ser.flushInput()
                    break
    
        def send_jog_command(self, dx, dy):
            """
            Construct and send the jog command based on dx, dy, and the current jog step size.
            """
            step = self.jog_step
            cmd = "$J=G91"
            if dx:
                cmd += f"X{dx * step}"
            if dy:
                cmd += f"Y{dy * step}"
            self.send(cmd)

        def send_coordinates_command(self, location):
            """
            Construct and send the jog command based on dx, dy, and the current jog step size.
            Figure out the gcode move command
            """
            x_offset = 0
            y_offset = 0
            x = location[0] + x_offset
            y = location[1] + y_offset

            cmd = "G90"
            if x:
                cmd += f"X{x}"
            if y:
                cmd += f"Y{y}"
            self.send(f"G90X{x}Y{y}")

            while True:
                self.ser.write(b'?')
                status = self.ser.readline().decode().strip()
                #print(f"Status: {status}")
                if '<Idle' in status:
                    break
                time.sleep(0.5)

        def toggle_magnet(self):
            self.send("M8")
            time.sleep(0.3)
            self.send("M9")
            time.sleep(0.1)

        def magnet_carlsen(self):
            self.set_acceleration(1000)

            for i in range(8):
                if i == 0:
                    self.toggle_magnet()
                    continue
                self.move(0, i*50)
                self.toggle_magnet()
    
            for i in range(7, -1, -1):
                self.move(50, i*50)
                self.toggle_magnet()

            for i in range(8):
                self.move(300, i*50)
                self.toggle_magnet()
    
            for i in range(7, -1, -1):
                self.move(350, i*50)
                self.toggle_magnet()

            self.set_acceleration(400)


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
        
        def interpret_chess_move(self, move_str, is_capture, is_castling, is_en_passant, is_white, symbol):
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

            #print(f"Move again: {start_square}, {end_square}")
            
            start_coord = self.square_to_coord(start_square)
            end_coord = self.square_to_coord(end_square)

            start_coord = (start_coord[0]*STEP_MM, start_coord[1]*STEP_MM)
            end_coord = (end_coord[0]*STEP_MM, end_coord[1]*STEP_MM)

            # Compute the difference in "steps"
            dx = end_coord[0] - start_coord[0]
            dy = end_coord[1] - start_coord[1]

            #print(dx)
            #print(dy)

            offset = STEP_MM

            print(f"Start square: {start_coord}, end square: {end_coord}")
            ###### Need to check if king ##### otherwise this will always trigger 
            if is_castling:
                print("in castle")

                #All notes in perspective of white

                # White king to the left
                if end_square == 'c1':
                    # Rook path
                    path = [(0, 14*offset), (0, -6*offset)]
                    movements = self.parse_path_to_movement(path)
                    commands = self.movement_to_gcode(movements)
                    #print(f"Rook comamnds: {commands}")
                    self.send_commands(commands)

                    # King_path
                    path = [(start_coord), (offset, offset), (0, 2*offset), (-offset, offset)]


                    movements = self.parse_path_to_movement(path)
                    commands = self.movement_to_gcode(movements)
                    #print(f"Rook comamnds: {commands}")
                    self.send_commands(commands)
                    return path
                    

                
                # White king to the right
                elif end_square == 'g1':

                    # Rook path
                    path = [(0, 0), (0, 4*offset)]
                    movements = self.parse_path_to_movement(path)
                    commands = self.movement_to_gcode(movements)
                    #print(f"rook comamnds: {commands}")
                    self.send_commands(commands)

                    # King_path
                    path = [(start_coord), (offset, -offset), (0, -2*offset), (-offset, -offset)]

                    movements = self.parse_path_to_movement(path)
                    commands = self.movement_to_gcode(movements)
                    #print(f"king comamnds: {commands}")
                    self.send_commands(commands)
                    return path
                    
                 # black king to the left
                if end_square == 'c8':
                    # Rook path
                    path = [(14*offset, 14*offset), (0, -6*offset)]
                    movements = self.parse_path_to_movement(path)
                    commands = self.movement_to_gcode(movements)
                    #print(f"Rook comamnds: {commands}")
                    self.send_commands(commands)

                    # King_path
                    path = [(start_coord), (-offset, offset), (0, 2*offset), (offset, offset)]

                    movements = self.parse_path_to_movement(path)
                    commands = self.movement_to_gcode(movements)
                    #print(f"king comamnds: {commands}")
                    self.send_commands(commands)
                    return path

                # White king to the right
                elif end_square == 'g8':

                    # Rook path
                    path = [(14*offset, 0), (0, 4*offset)]
                    movements = self.parse_path_to_movement(path)
                    commands = self.movement_to_gcode(movements)
                    print(f"Rook comamnds: {commands}")
                    self.send_commands(commands)

                    # King_path
                    path = [(start_coord), (-offset, -offset), (0, -2*offset), (offset, -offset)]
                    movements = self.parse_path_to_movement(path)
                    commands = self.movement_to_gcode(movements)
                    print(f"king comamnds: {commands}")
                    self.send_commands(commands)
                    return path


                # For castling, need to move rook to new position, then slide king around it vertically. 
                # Need to know colour, , which rook is being moved
                
    
                
            
            else: 
                print('Not a castle')

                # Computational method for determineing if it is a knight.
                if min(abs(dx), abs(dy)) == 0 or abs(dx) == abs(dy):
                    print("Not a knight")

                    path = [(start_coord[0], start_coord[1]), (dx, dy)]   
                else:
                    print("Probably a horse")
                    angled_movement = (self.sign(dx) * offset, self.sign(dy)*offset)
                    #print(angled_movement)

                    # inital offset is (sign(dx) * dx, sing(dy)*dy)
                    if abs(dx) > abs(dy):
                        path = [start_coord, angled_movement, (2*self.sign(dx)*offset, 0), angled_movement]
                    else:
                        path = [start_coord, angled_movement, (0, 2*self.sign(dy)*offset), angled_movement]
                 

            
            if is_capture:
                print('Is capture')

                dx_sign = self.sign(dx)
                dy_sign = self.sign(dy)


                if is_en_passant:
                    print("Is en passant")

                    commands = self.movement_to_gcode(path)
                    self.send_commands(commands)


                    # moved captured piece off square
                    path = [(end_coord[0]- 2*offset*dx_sign, end_coord[1]), (offset*dx_sign, offset)]

                    commands = self.movement_to_gcode(path)
                    self.send_commands(commands)

                    dead_coordinates = (end_coord[0]-offset*dx_sign, end_coord[1]+offset)
                    self.to_deadzone(dead_coordinates, is_white, symbol)
                    return (path)


                # Need to make literal edge case

                elif end_square[1] == '8' or end_square[1] == '1' or end_square[0] == 'h':
                    print("Is edge case")
                    #edged
                    
                    
                    if end_square == 'h1':

                        if dx_sign == 0 and dy_sign == -1:
                            #straight right

                            # Take away 25mm from last movement, so piece is on the edge
                            end_x, end_y = path[-1]
                            new_end_x =  end_x - self.sign(end_x)*offset
                            new_end_y = end_y - self.sign(end_y)*offset
                            path[-1] = (new_end_x, new_end_y)

                            commands = self.movement_to_gcode(path)
                            self.send_commands(commands)

                            #move piece off center in +x direction 
                            path = [end_coord, (offset, 0)]
                            commands = self.movement_to_gcode(path)
                            self.send_commands(commands)

                            # put capturing piece in square
                            path = [(end_coord[0], end_coord[1]+offset), (0, -offset)]
                            commands = self.movement_to_gcode(path)
                            self.send_commands(commands)


                            # take capturing piece to deadzone
                            dead_coordinates = (end_coord[0] + offset, end_coord[1])
                            self.to_deadzone(dead_coordinates, is_white, symbol)
                            return (path)

                        elif dx_sign == -1 and dy_sign == 0:
                            #straight in
                            # Take away 50mm, then angle and dive in
                            end_x, end_y = path[-1]
                            new_end_x =  end_x - self.sign(end_x)*2*offset
                            new_end_y = end_y - self.sign(end_y)*2*offset
                            path[-1] = (new_end_x, new_end_y)
                            path.append((-offset, offset))
                            path.append((-offset, 0))

                            commands = self.movement_to_gcode(path)
                            self.send_commands(commands)

                            #move piece off center in +x direction 
                            path = [end_coord, (offset, 0)]
                            commands = self.movement_to_gcode(path)
                            self.send_commands(commands)

                            # put capturing piece in square
                            path = [(end_coord[0], end_coord[1]+offset), (0, -offset)]
                            commands = self.movement_to_gcode(path)
                            self.send_commands(commands)

                            # take capturing piece to deadzone
                            dead_coordinates = (end_coord[0] + offset, end_coord[1])
                            self.to_deadzone(dead_coordinates, is_white, symbol)
                            return (path)


                        elif dx_sign == -1 and dy_sign == -1:
                            #angled close right 
                            end_x, end_y = path[-1]
                            new_end_x =  end_x - self.sign(end_x)*offset
                            new_end_y = end_y - self.sign(end_y)*offset
                            path[-1] = (new_end_x, new_end_y)
                            path.append((-offset, 0))

                            commands = self.movement_to_gcode(path)
                            self.send_commands(commands)

                            #move piece off center in +x direction 
                            path = [end_coord, (offset, 0)]
                            commands = self.movement_to_gcode(path)
                            self.send_commands(commands)

                            # put capturing piece in square
                            path = [(end_coord[0], end_coord[1]+offset), (0, -offset)]
                            commands = self.movement_to_gcode(path)
                            self.send_commands(commands)

                            # take capturing piece to deadzone
                            dead_coordinates = (end_coord[0] + offset, end_coord[1])
                            self.to_deadzone(dead_coordinates, is_white, symbol)
                            return (path)


                    elif end_square == 'h8':

                        if dx_sign == 1 and dy_sign == -1:
                            #angled far right
                            end_x, end_y = path[-1]
                            new_end_x =  end_x - self.sign(end_x)*offset
                            new_end_y = end_y - self.sign(end_y)*offset
                            path[-1] = (new_end_x, new_end_y)
                            path.append((offset, 0))

                            commands = self.movement_to_gcode(path)
                            self.send_commands(commands)

                            #move piece off center in -x direction 
                            path = [end_coord, (-offset, 0)]
                            commands = self.movement_to_gcode(path)
                            self.send_commands(commands)

                            # put capturing piece in square
                            path = [(end_coord[0], end_coord[1]+offset), (0, -offset)]
                            commands = self.movement_to_gcode(path)
                            self.send_commands(commands)

                            # take capturing piece to deadzone
                            dead_coordinates = (end_coord[0] - offset, end_coord[1])
                            self.to_deadzone(dead_coordinates, is_white, symbol)
                            return (path)

                        elif dx_sign == 0 and dy_sign == -1:
                            # Take away 25mm from last movement, so piece is on the edge
                            end_x, end_y = path[-1]
                            new_end_x =  end_x - self.sign(end_x)*offset
                            new_end_y = end_y - self.sign(end_y)*offset
                            path[-1] = (new_end_x, new_end_y)

                            commands = self.movement_to_gcode(path)
                            self.send_commands(commands)

                            #move piece off center in -x direction 
                            path = [end_coord, (-offset, 0)]

                            commands = self.movement_to_gcode(path)
                            self.send_commands(commands)

                            # put capturing piece in square
                            path = [(end_coord[0], end_coord[1]+offset), (0, -offset)]
                            commands = self.movement_to_gcode(path)
                            self.send_commands(commands)

                            # take capturing piece to deadzone
                            dead_coordinates = (end_coord[0] - offset, end_coord[1])
                            self.to_deadzone(dead_coordinates, is_white, symbol)
                            return (path)
                        
                        elif dx_sign == 1 and dy_sign == 0:
                             # Take away 50mm, then angle and dive in
                            end_x, end_y = path[-1]
                            new_end_x =  end_x - self.sign(end_x)*2*offset
                            new_end_y = end_y - self.sign(end_y)*2*offset
                            path[-1] = (new_end_x, new_end_y)
                            path.append((offset, offset))
                            path.append((offset, 0))

                            commands = self.movement_to_gcode(path)
                            self.send_commands(commands)

                            #move piece off center in -x direction 
                            path = [end_coord, (-offset, 0)]
                            commands = self.movement_to_gcode(path)
                            self.send_commands(commands)

                            # put capturing piece in square
                            path = [(end_coord[0], end_coord[1]+offset), (0, -offset)]
                            commands = self.movement_to_gcode(path)
                            self.send_commands(commands)

                            # take capturing piece to deadzone
                            dead_coordinates = (end_coord[0] - offset, end_coord[1])
                            self.to_deadzone(dead_coordinates, is_white, symbol)
                            return (path)

                    

                    else:
                        if end_square[1] == '1':
                            print("rank1")
                            if dx_sign == 0 and dy_sign == 1:
                                #Straight left

                                end_x, end_y = path[-1]
                                new_end_x =  end_x - self.sign(end_x)*offset
                                new_end_y = end_y - self.sign(end_y)*offset
                                path[-1] = (new_end_x, new_end_y)

                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)
                                
                                #move piece off center in
                                path = [end_coord, (offset, 0)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # put capturing piece in square
                                path = [(end_coord[0], end_coord[1]-offset), (0, offset)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # take capturing piece to deadzone
                                dead_coordinates = (end_coord[0] + offset, end_coord[1])
                                self.to_deadzone(dead_coordinates, is_white, symbol)
                                return (path)

                            elif dx_sign == -1 and dy_sign == 1:
                            #     # angled close left
                                
                                end_x, end_y = path[-1]
                                new_end_x =  end_x - self.sign(end_x)*offset
                                new_end_y = end_y - self.sign(end_y)*offset
                                path[-1] = (new_end_x, new_end_y)

                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)
                                
                                #move piece off center in
                                path = [end_coord, (offset, offset)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # put capturing piece in square
                                path = [(end_coord[0]+offset, end_coord[1]-offset), (-offset, offset)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # take capturing piece to deadzone
                                dead_coordinates = (end_coord[0] + offset, end_coord[1] + offset)
                                self.to_deadzone(dead_coordinates, is_white, symbol)
                                return (path)

                            elif dx_sign == -1 and dy_sign == 0:
                                #straight in
                                end_x, end_y = path[-1]
                                new_end_x =  end_x - self.sign(end_x)*2*offset
                                new_end_y = end_y - self.sign(end_y)*2*offset
                                path[-1] = (new_end_x, new_end_y)
                                path.append((-offset, -offset))

                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)
                                
                                #move piece off center in
                                path = [end_coord, (offset, offset)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # put capturing piece in square
                                path = [(end_coord[0]+offset, end_coord[1]-offset), (-offset, offset)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # take capturing piece to deadzone
                                dead_coordinates = (end_coord[0] + offset, end_coord[1]+offset)
                                self.to_deadzone(dead_coordinates, is_white, symbol)
                                return (path)

                            elif dx_sign == -1 and dy_sign == -1:
                                #angled close right
                                end_x, end_y = path[-1]
                                new_end_x =  end_x - self.sign(end_x)*offset
                                new_end_y = end_y - self.sign(end_y)*offset
                                path[-1] = (new_end_x, new_end_y)

                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                #move piece off center in
                                path = [end_coord, (offset, -offset)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # put capturing piece in square
                                path = [(end_coord[0]+offset, end_coord[1]+offset), (-offset, -offset)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # take capturing piece to deadzone
                                dead_coordinates = (end_coord[0] + offset, end_coord[1] - offset)
                                self.to_deadzone(dead_coordinates, is_white, symbol)
                                return (path)

                            elif dx_sign == 0 and dy_sign == -1:
                                # straight right
                                end_x, end_y = path[-1]
                                new_end_x =  end_x - self.sign(end_x)*offset
                                new_end_y = end_y - self.sign(end_y)*offset
                                path[-1] = (new_end_x, new_end_y)

                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)
                                
                                #move piece off center in
                                path = [end_coord, (offset, 0)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # put capturing piece in square
                                path = [(end_coord[0], end_coord[1]+offset), (0, -offset)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # take capturing piece to deadzone
                                dead_coordinates = (end_coord[0] + offset, end_coord[1])
                                self.to_deadzone(dead_coordinates, is_white, symbol)
                                return (path)


                        
                        elif end_square[1] == '8':
                            if dx_sign == 0 and dy_sign == 1:
                                #Straight left

                                end_x, end_y = path[-1]
                                new_end_x =  end_x - self.sign(end_x)*offset
                                new_end_y = end_y - self.sign(end_y)*offset
                                path[-1] = (new_end_x, new_end_y)

                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)
                                
                                #move piece off center in
                                path = [end_coord, (-offset, 0)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # put capturing piece in square
                                path = [(end_coord[0], end_coord[1]-offset), (0, offset)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # take capturing piece to deadzone
                                dead_coordinates = (end_coord[0] - offset, end_coord[1])
                                self.to_deadzone(dead_coordinates, is_white, symbol)
                                return (path)

                            elif dx_sign == 1 and dy_sign == 1:
                            #     # angled far left
                                
                                end_x, end_y = path[-1]
                                new_end_x =  end_x - self.sign(end_x)*offset
                                new_end_y = end_y - self.sign(end_y)*offset
                                path[-1] = (new_end_x, new_end_y)

                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)
                                
                                #move piece off center in
                                path = [end_coord, (-offset, offset)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # put capturing piece in square
                                path = [(end_coord[0]-offset, end_coord[1]-offset), (offset, offset)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # take capturing piece to deadzone
                                dead_coordinates = (end_coord[0] - offset, end_coord[1] + offset)
                                self.to_deadzone(dead_coordinates, is_white, symbol)
                                return (path)

                            elif dx_sign == 1 and dy_sign == 0:
                                #straight in
                                end_x, end_y = path[-1]
                                new_end_x =  end_x - self.sign(end_x)*2*offset
                                new_end_y = end_y - self.sign(end_y)*2*offset
                                path[-1] = (new_end_x, new_end_y)
                                path.append((offset, -offset))

                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)
                                
                                #move piece off center in
                                path = [end_coord, (-offset, offset)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # put capturing piece in square
                                path = [(end_coord[0]-offset, end_coord[1]-offset), (offset, offset)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # take capturing piece to deadzone
                                dead_coordinates = (end_coord[0] - offset, end_coord[1]+offset)
                                self.to_deadzone(dead_coordinates, is_white, symbol)
                                return (path)

                            elif dx_sign == 1 and dy_sign == -1:
                                #angled far right
                                end_x, end_y = path[-1]
                                new_end_x =  end_x - self.sign(end_x)*offset
                                new_end_y = end_y - self.sign(end_y)*offset
                                path[-1] = (new_end_x, new_end_y)

                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                #move piece off center in
                                path = [end_coord, (-offset, -offset)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # put capturing piece in square
                                path = [(end_coord[0]-offset, end_coord[1]+offset), (offset, -offset)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # take capturing piece to deadzone
                                dead_coordinates = (end_coord[0] - offset, end_coord[1] - offset)
                                self.to_deadzone(dead_coordinates, is_white, symbol)
                                return (path)

                            elif dx_sign == 0 and dy_sign == -1:
                                # straight right
                                end_x, end_y = path[-1]
                                new_end_x =  end_x - self.sign(end_x)*offset
                                new_end_y = end_y - self.sign(end_y)*offset
                                path[-1] = (new_end_x, new_end_y)

                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)
                                
                                #move piece off center in
                                path = [end_coord, (-offset, 0)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # put capturing piece in square
                                path = [(end_coord[0], end_coord[1]+offset), (0, -offset)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # take capturing piece to deadzone
                                dead_coordinates = (end_coord[0] - offset, end_coord[1])
                                self.to_deadzone(dead_coordinates, is_white, symbol)
                                return (path)

                            
                        
                        elif end_square[0] == 'h':

                            if dx_sign == 0 and dy_sign == -1:
                                #Straight right

                                end_x, end_y = path[-1]
                                new_end_x =  end_x - self.sign(end_x)*2*offset
                                new_end_y = end_y - self.sign(end_y)*2*offset
                                path[-1] = (new_end_x, new_end_y)
                                if end_coord[0] > 180: # send to outside if on black side
                                    path.append((offset, -offset))
                                else: # send to white side
                                    path.append((-offset, -offset))

                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)
                                
                                if end_coord[0] > 180:
                                    path = [end_coord, (-offset, offset)]
                                else:
                                #move piece off center in
                                    path = [end_coord, (offset, offset)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)


                                # capturing piece in square
                                if end_coord[0] > 180:
                                    path = [(end_coord[0]+offset, end_coord[1]+offset), (-offset, -offset)]
                                else:
                                    path = [(end_coord[0]-offset, end_coord[1]+offset), (offset, -offset)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # take capturing piece to deadzone
                                if end_coord[0] > 180:
                                    dead_coordinates = (end_coord[0] - offset, end_coord[1]+offset)
                                else:
                                    dead_coordinates = (end_coord[0] + offset, end_coord[1]+offset)
                                self.to_deadzone(dead_coordinates, is_white, symbol)
                                return (path)

                            elif dx_sign == -1 and dy_sign == -1:
                            #     # angled close right
                                
                                end_x, end_y = path[-1]
                                new_end_x =  end_x - self.sign(end_x)*offset
                                new_end_y = end_y - self.sign(end_y)*offset
                                path[-1] = (new_end_x, new_end_y)

                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)
                                
                                #move piece off center in
                                path = [end_coord, (-offset, offset)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # put capturing piece in square
                                path = [(end_coord[0]+offset, end_coord[1]+offset), (-offset, -offset)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # take capturing piece to deadzone
                                dead_coordinates = (end_coord[0] - offset, end_coord[1] + offset)
                                self.to_deadzone(dead_coordinates, is_white, symbol)
                                return (path)

                            elif dx_sign == -1 and dy_sign == 0:
                                #straight in
                                end_x, end_y = path[-1]
                                new_end_x =  end_x - self.sign(end_x)*offset
                                new_end_y = end_y - self.sign(end_y)*offset
                                path[-1] = (new_end_x, new_end_y)
                                # path.append((offset, -offset))

                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)
                                
                                #move piece off center in
                                path = [end_coord, (-offset, 0)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # put capturing piece in square
                                path = [(end_coord[0]+offset, end_coord[1]), (-offset, 0)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # take capturing piece to deadzone
                                dead_coordinates = (end_coord[0], end_coord[1]+offset)
                                self.to_deadzone(dead_coordinates, is_white, symbol)

                                return (path)

                            elif dx_sign == 1 and dy_sign == -1:
                                #angled far right
                                end_x, end_y = path[-1]
                                new_end_x =  end_x - self.sign(end_x)*offset
                                new_end_y = end_y - self.sign(end_y)*offset
                                path[-1] = (new_end_x, new_end_y)

                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                #move piece off center in
                                path = [end_coord, (offset, offset)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # put capturing piece in square
                                path = [(end_coord[0]-offset, end_coord[1]+offset), (offset, -offset)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # take capturing piece to deadzone
                                dead_coordinates = (end_coord[0] + offset, end_coord[1] + offset)
                                self.to_deadzone(dead_coordinates, is_white, symbol)
                                return (path)

                            elif dx_sign == 1 and dy_sign == 0:
                                # straight out
                                end_x, end_y = path[-1]
                                new_end_x =  end_x - self.sign(end_x)*offset
                                new_end_y = end_y - self.sign(end_y)*offset
                                path[-1] = (new_end_x, new_end_y)

                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)
                                
                                #move piece off center in
                                path = [end_coord, (offset, 0)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # put capturing piece in square
                                path = [(end_coord[0]-offset, end_coord[1]), (offset, 0)]
                                commands = self.movement_to_gcode(path)
                                self.send_commands(commands)

                                # take capturing piece to deadzone
                                dead_coordinates = (end_coord[0]+offset, end_coord[1])
                                self.to_deadzone(dead_coordinates, is_white, symbol)
                                return (path)


                else:
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

                    
                    if self.sign(dx) == 0:
                        # case where straight off would impede other piece

                        if end_coord[0] > 180: # send towards white
                            captured_new_x = -offset
                            captured_new_y = 0

                        else: # send towards black
                            captured_new_x = offset
                            captured_new_y = 0

                    else:

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

                    self.to_deadzone(dead_coordinates, is_white, symbol)

                    return (path)
                # dead_x = self.deadzone_origin[0] - dead_coordinates[0]
                # dead_y = self.deadzone_origin[1] - dead_coordinates[1]

                # dz_x, dz_y = self.deadzone_origin

                # path = [dead_coordinates, (0, offset*16 - dead_coordinates[1]), (dead_x, 0), (0, dz_y-offset*16)]

                # print(f"moving to deadzone: {path}")


                    # movements = self.parse_path_to_movement(path)
                    # commands = self.movement_to_gcode(movements)
                    # print(f" moving to deadzone: {commands}")
                    # self.send_commands(commands)



                

                # if dz_x == 350:
                #     dz_x = -50
                #     dz_y = 400

                # self.deadzone_origin = (dz_x + 2*offset, dz_y)



            print(f"Interpreted move: {move_str} as dx={dx}, dy={dy} as {path}")

            movements = self.parse_path_to_movement(path)
            commands = self.movement_to_gcode(movements)
            print(f"Last move: {commands}")
            self.send_commands(commands)

            
            return (path)
        


        def to_deadzone(self, dead_coordinates, is_white, symbol):

            ## FELIPE DIAZ DO SOME MAGIC HERE
            offset = 25

            if is_white:
                dead_x = self.nextdead_white[0] - dead_coordinates[0]
                dead_y = self.nextdead_white[1] - dead_coordinates[1]
                #dz_x, dz_y = self.nextdead_white
                
                path = [dead_coordinates, (0, offset*15 - dead_coordinates[1]), (dead_x, 0), (0,  self.nextdead_white[1] - offset*15)]
            
                self.white_captured.append((symbol, (self.nextdead_white)))

                if self.nextdead_white[1] == 435:
                    self.nextdead_white = (self.nextdead_white[0], 410)
                else:
                    self.nextdead_white = (self.nextdead_white[0] + offset, 435)
                

            else: 
                dead_x = self.nextdead_black[0] - dead_coordinates[0]
                dead_y = self.nextdead_black[1] - dead_coordinates[1]
                
                path = [dead_coordinates, (0, offset*15 - dead_coordinates[1]), (dead_x, 0), (0, self.nextdead_black[1] - offset*15)]
                
                self.black_captured.append((symbol, (self.nextdead_black)))

                if self.nextdead_black[1] == 435:
                    self.nextdead_black = (self.nextdead_black[0], 410)
                else:
                    self.nextdead_black = (self.nextdead_black[0] - offset, 435)
    
            print(f"moving to deadzone: {path}")

            movements = self.parse_path_to_movement(path)
            commands = self.movement_to_gcode(movements)
            print(f"Last move: {commands}")
            self.send_commands(commands)

            pass
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

        def send_commands(self, cmd_list):
            if self.simulate:
                time.sleep(2)
                print(f"Sent commands")
            else:
                print("[S] sending commands")
                for cmd in cmd_list:
                    self.finished = False
                    full_cmd = cmd + "\n"
                    self.send(full_cmd)
                    # Wait for GRBL response ("ok")
                    response = self.ser.readline().decode().strip()
                    while response != "ok":
                        response = self.ser.readline().decode().strip()
                time.sleep(0.1)

                while not self.finished:
                    self.ser.write(b'?')
                    status = self.ser.readline().decode().strip()

                    if '<Idle' in status:
                        self.finished = True
                        self.ser.flushInput()
                print("[S] sent commands")

        

        def path_to_gcode(self, move_list):
            """
            Given a list of moves (e.g., ["e2e4", "g8h6"]), converts them to relative
            displacement commands in G-code format.
            """

            print(f"move list: {move_list}")
            if self.magnet_state == "MAG OFF":
                self.send("M9") # off
            elif self.magnet_state == "MAG ON":
                self.set_acceleration(400)
                self.send("M8") # on

            gcode_commands = []
            for i, move in enumerate(move_list):
                if i == 0:
                    gcode_commands.append(f"G90X{move[0]}Y{move[1]}")
                    if self.magnet_state == "MOVE MODE":
                        gcode_commands.append(f"M8") #Activate after initial movement
                elif i == len(move_list) - 1:
                    dx = self.sign(move_list[-1][0]) * self.overshoot
                    dy = self.sign(move_list[-1][1]) * self.overshoot

                    print(f"Overshoots: {dx, dy}")
                    gcode_commands.append(f"G91X{move[0]+dx}Y{move[1]+dy}")

                    gcode_commands.append(f"G91X{-dx}Y{-dy}")
                    # gcode_commands.append(f"M8") # deactivate after final movement
                    # gcode_commands.append(f"M9") # deactivate after final movement

                

                    if self.magnet_state == "MOVE MODE":
                        gcode_commands.append(f"M9") # deactivate after final movement
                else:
                    gcode_commands.append(f"G91X{move[0]}Y{move[1]}")


            
            return gcode_commands




        def movement_to_gcode(self, move_list):
            """
            Given a list of moves (e.g., ["e2e4", "g8h6"]), converts them to relative
            displacement commands in G-code format.
            """

            print(f"move list: {move_list}")
            if self.magnet_state == "MAG OFF":
                self.send("M9") # off
            elif self.magnet_state == "MAG ON":
                self.send("M8") # on

            gcode_commands = []
            for i, move in enumerate(move_list):
                if i == 0:
                    gcode_commands.append(f"G90X{move[0]}Y{move[1]}")
                    if self.magnet_state == "MOVE MODE":
                        gcode_commands.append(f"M8") #Activate after initial movement
                elif i == len(move_list) - 1:
                    dx = self.sign(move_list[-1][0]) * self.overshoot
                    dy = self.sign(move_list[-1][1]) * self.overshoot
                    gcode_commands.append(f"G91X{move[0]+dx}Y{move[1]+dy}")

                    gcode_commands.append(f"G91X{-dx}Y{-dy}")
                    # gcode_commands.append(f"M8") # deactivate after final movement
                    # gcode_commands.append(f"M9") # deactivate after final movement

                

                    if self.magnet_state == "MOVE MODE":
                        gcode_commands.append(f"M9") # deactivate after final movement
                else:
                    gcode_commands.append(f"G91X{move[0]}Y{move[1]}")


            
            return gcode_commands
        
        def magnet_control(self):
            if self.magnet_state == "MAG ON":
                self.send("M8")
            elif self.magnet_state == "MAG OFF":
                self.send("M9")


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
