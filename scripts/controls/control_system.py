from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
# from kivy.uix.boxlayout import BoxLayout
# from kivy.uix.button import Button
# from kivy.uix.label import Label
# from kivy.uix.textinput import TextInput
from kivy.clock import Clock
# from transitions import Machine
from transitions.extensions import HierarchicalMachine as Machine

import chess
import chess.pgn
import chess.engine
import time
import threading
import sys
import random
import copy
import asyncio

import logging
logging.getLogger('transitions').setLevel(logging.WARNING)


# from gantry_control import GantryControl, ClockLogic
# #from game_control import ChessControlSystem
# from servo_control import Servo

try:
    from gantry_control import GantryControl, ClockLogic
    from rocker_control import Rocker
    from hall_control import Hall
    from reset_control import BoardReset
    from nfc_control import NFC

    from scripts.screens import GameScreen, MainScreen, InitScreen, GantryControlScreen

except:
    from scripts.controls.gantry_control import GantryControl, ClockLogic
    from scripts.controls.rocker_control import Rocker
    from scripts.controls.hall_control import Hall
    from scripts.controls.reset_control import BoardReset
    from scripts.controls.nfc_control import NFC


    from scripts.screens.gamescreen import GameScreen
    from scripts.screens.initscreen import InitScreen
    from scripts.screens.loadingscreen import LoadingScreen
    from scripts.screens.mainscreen import MainScreen
    from scripts.screens.gantryscreen import GantryControlScreen




'''
Check-M.A.T.E Automated chess board control logic
State machine architecture used for backend logic and frontend UI control for program maintainability and readability

General Flow:
Init program, init gantry, load to main menu
- Select game parameters, difficulty, opponent, 
    OR
- Go to settings, go to gantry control

If game, init engine with passed parameters
Start game for white
If player turn, poll hall effects until move detected, update screen, wait for rocker switch
- Check legal move mid state or on state switch
Push move 
If board turn, either check online for move or check engine for appropriate move

Send move to gantry control, knock rocker/change clock

Check for mate, check etc, update visuals 
if yes, end game
if no, Go to next turn

If end game, go to menu or reset board and start again


'''

running_on_pi = sys.platform.startswith("linux")
running_on_mac = sys.platform.startswith("darwin")
running_on_win = sys.platform.startswith("win")

class ChessControlSystem:
    # Top-level states: loading, main_menu, and gamescreen.
    # Within gamescreen, we nest the gameplay states.
    states = [
        'initscreen',
        'loadingscreen',
        'mainscreen',
        {'name': 'gamescreen', 'children': [
            
            'init_game',
            'player_turn',
            'hall_polling',
            'player_move_confirmed',
            'engine_turn', 
            'first_piece_detection',
            'second_piece_detection',
            'end_game',
            'predefined_game'
        ]
        },
        'gantryscreen',
        'settingsscreen',
        'endgamescreen',
        'boardresetscreen'
    ]

    systems_enabled = {
        "rocker": True,
        "gantry": True,
        "hall": False,
        "rfid": False
    }


    def __init__(self, ui_update_callback=None):
        # Start in the start screen state.

        self.piece_images = {
            'P': 'assets/white_pawn.png',
            'R': 'assets/white_rook.png',
            'N': 'assets/white_knight.png',
            'B': 'assets/white_bishop.png',
            'Q': 'assets/white_queen.png',
            'K': 'assets/white_king.png',
            'p': 'assets/black_pawn.png',
            'r': 'assets/black_rook.png',
            'n': 'assets/black_knight.png',
            'b': 'assets/black_bishop.png',
            'q': 'assets/black_queen.png',
            'k': 'assets/black_king.png',
            'K_mate': 'assets/black_king_mate.png',
            'K_check': 'assets/black_king_check.png',
            'k_mate': 'assets/white_king_mate.png',
            'k_check': 'assets/white_king_mate.png',

        }

        self.ui_update_callback = ui_update_callback
        self.capture_move = False
        self.endgame_message = "Jobs not finished"
        self.checkmate = False

        self.font_size = 40
        self.title_font = 120

        self.board = chess.Board()  # Integrated chess board.
        self.running = True
        if running_on_pi:
            self.engine_path = "./bin/stockfish"
            #self.engine_path = "./bin/stockfish-android-armv8"

        elif running_on_mac:
            self.engine_path = "./bin/stockfish-macos-m1-apple-silicon"
        else:
            print("Need to download windows stockfish")
            self.engine = None
        
        self.engine = None

        self.use_switch = True

        self.ingame_message = ""

        self.demo_game = ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6", "b5a4", "g8f6", "e1g1", "f8e7", "f1e1", "e8g8", "d2d4", "e5d4", "c2c4", "d4c3", "e4e5", "c3b2", "c1b2", "f6e8", "a4c2", "d7d6", "d1d3", "f7f5", "e5f6", "e7f6", "d3h7", "g8f7", "c2g6"]
        
        self.parameters = {'online': False, 'colour': "white", 'elo': 1500, 'timer': False, 'engine_time_limit': 0.1, 'bot_mode': True, 'engine_path': self.engine_path, 'local_mode': False}  # Default parameters to be set by the user 

        self.timer_enabled = False

        # Create a hierarchical state machine.
        self.machine = Machine(model=self, states=ChessControlSystem.states, initial='initscreen')

        # Top-level transitions. dj
        
        self.machine.add_transition(trigger='finish_loading', source='initscreen', dest='mainscreen', after=['update_ui', 'init_gantry'])
        # Two transitions for starting the game based on who goes first.
        self.machine.add_transition(trigger='start_game', source='mainscreen', dest='gamescreen_player_turn',
                                    conditions=lambda: self.parameters["colour"].lower() == "white",
                                    unless='is_auto_engine_mode',
                                    after=['init_game', 'update_ui', 'on_player_first_turn'])
        self.machine.add_transition(trigger='start_game', source='mainscreen', dest='gamescreen_engine_turn',
                                    conditions=lambda: self.parameters["colour"].lower() == "black",
                                    unless='is_auto_engine_mode',
                                    after=['init_game', 'update_ui', 'on_board_turn'])
        
        self.machine.add_transition(trigger='start_game', source='mainscreen', dest='gamescreen_engine_turn',
                                    conditions=lambda: self.parameters["bot_mode"] == True,
                                    after=['init_game', 'update_ui', 'on_board_turn'])
        
        self.machine.add_transition(trigger='start_demo_game', source='mainscreen', dest='gamescreen_predefined_game',
                                    after=['update_ui', 'on_predefined_first_turn'])

        


        # Nested transitions inside gamescreen.
        # Note: When referring to nested states, use the full path: e.g. gamescreen_player_turn.
        # self.machine.add_transition(trigger='begin_polling', source='gamescreen_player_turn', dest='gamescreen_hall_polling', after='on_hall_polling')
        # self.machine.add_transition(trigger='move_detected', source='gamescreen_hall_polling', dest='gamescreen_player_move_confirmed', after='on_player_move_confirmed')


        self.machine.add_transition(trigger='go_to_first_piece_detection', source='gamescreen_player_turn', dest='gamescreen_player_turn', after='first_piece_detection_poll')
        self.machine.add_transition(trigger='go_to_second_piece_detection', source='gamescreen_player_turn', dest='gamescreen_player_turn', after='second_piece_detection_poll')


        self.machine.add_transition(trigger='process_move', source=['gamescreen_player_turn', 'gamescreen_player_move_confirmed'], dest='gamescreen_engine_turn', after=['on_board_turn', 'toggle_clock', 'notify_observers'])
        #self.machine.add_transition(trigger='engine_move_complete', source='gamescreen_engine_turn', dest='gamescreen_player_turn', after='on_player_turn')

        self.machine.add_transition(trigger='engine_move_complete', source='gamescreen_engine_turn', dest='gamescreen_engine_turn',
                                    conditions='is_auto_engine_mode', after=['on_board_turn', 'notify_observers'])
        # Otherwise, transition to player_turn.
        self.machine.add_transition(trigger='engine_move_complete', source='gamescreen_engine_turn', dest='gamescreen_player_turn',
                                    unless='is_auto_engine_mode', after=['on_player_turn', 'notify_observers'])
        # deal with player move
        self.machine.add_transition(trigger='player_move_complete', source='gamescreen_player_turn', dest='gamescreen_player_turn',
                                    conditions='is_local_mode', after=['on_player_turn', 'notify_observers'])
        # Otherwise, transition to player_turn.
        self.machine.add_transition(trigger='player_move_complete', source='gamescreen_player_turn', dest='gamescreen_engine_turn',
                                    unless='is_local_mode', after=['on_player_turn', 'notify_observers'])
        
        self.machine.add_transition(trigger='process_predefined_board_move', source='gamescreen_predefined_game', dest='gamescreen_predefined_game',
                                    after=['notify_observers'])
        


        # self.machine.add_transition(trigger='end_game_processes', source=['gamescreen_engine_turn','gamescreen_player_turn', 'game_screen_player_move_confirmed'], dest='endgamescreen')
        self.machine.add_transition(trigger='go_to_endgamescreen', source=['gamescreen_engine_turn','gamescreen_player_turn', 'game_screen_player_move_confirmed', 'game_screen_player_engine_move_confirmed', 'gamescreen_predefined_game'], dest='endgamescreen', after=['update_ui'])
        self.machine.add_transition(trigger='resetboard', source=['endgamescreen', 'mainscreen'], dest='boardresetscreen', after='update_ui')
        self.machine.add_transition(trigger='go_to_mainscreen', source=['endgamescreen'], dest='mainscreen', after='update_ui')


        self.machine.add_transition(trigger='go_to_mainscreen', source=['gantryscreen'], dest='mainscreen', after='update_ui')
        self.machine.add_transition(trigger='go_to_mainscreen', source=['gamescreen_engine_turn','gamescreen_player_turn', 'game_screen_player_move_confirmed', 'game_screen_player_engine_move_confirmed', 'gamescreen_predefined_game'], dest='end_game_screen', after=['early_exit', 'update_ui'])


        self.machine.add_transition(trigger='go_to_gantry', source='mainscreen', dest='gantryscreen', after='update_ui')
        self.machine.add_transition(trigger='go_to_boardreset', source=['mainscreen', 'boardresetscreen'], dest='boardresetscreen', after='update_ui')
        

        # print("trying to init hall")
        # try:
        #     self.hall = Hall()
        # except Exception as e:
        #     print(f"Errorwith halls : {e}")
        # print("Hall Initialized")

        self.rocker = Rocker()
        self.rocker.begin()
        print("Rocker initialized")
        self.gantry = GantryControl()
        self.gantry.home()
        print("Gantry initialized: homing")
        self.move_history = []
        self.captured_pieces = []
        self.SQUARES = chess.SQUARES
        self.observers = []
        self.game_state = "UNFINISHED"
        print("trying to init hall")
        try:
            self.hall = Hall()
        except Exception as e:
            print(f"Errorwith halls : {e}")
        print("Hall Initialized")

        self.first_change = None
        self.second_change = None

        self.legal_moves = None
        self.game_winner = None
        self.selected_piece = None




        # self.rocker.toggle()
        # time.sleep(0.2)
        # self.rocker.toggle()
        # time.sleep(0.2)
        # self.rocker.toggle()

        

        


        # self.game_logic = ChessBackend(lichess_token=api_key, ui_move_callback=None, mode="offline",
        #                    engine_time_limit=0.1, difficulty_level=5, elo=self.elo, colour=self.colour, clock_logic = self.clock_logic, bot_mode=self.bot_mode, gantry_control=self.gantry_control)
        #self.clock_logic = None
        self.clock_logic = None

                # Run the state machine’s background loop in its own thread.
        self.sm_thread = threading.Thread(target=self.run, daemon=True)
        self.sm_thread.start()

    def run(self):
        # This loop keeps the state machine alive.
        while self.running:
            time.sleep(0.1)

    def update_ui(self):
        # Update the UI with the current state.
        state = self.state
        print(f"UI updated to state: {state}")
        if self.ui_update_callback:
            Clock.schedule_once(lambda dt: self.ui_update_callback(state), 0.1)

            # Condition method used for transitions.
    def is_auto_engine_mode(self):
        return self.parameters['bot_mode']
    
    def is_local_mode(self):
        return self.parameters['local_mode']
    
    def register_observer(self, callback):
        """Register a callback that will be called when the board changes."""
        self.observers.append(callback)
    
    def notify_observers(self):
        self.update_ui()
        """Call all registered observer callbacks with the updated board."""
        for callback in self.observers:
            Clock.schedule_once(lambda dt, cb=callback: cb(self.board), 0.05)
            #callback(self.board)

    # def start_game(self):
    #     self.to_gamescreen()
    #     pass

    def early_exit(self):

        self.endgame_message = "Game Abandoned"





##########################
# Process fucntions

    # def on_ui_move(self, move_uci):
    #     if self.process_move(move_uci):
    #         self.trigger_move_event()  # triggers state transition
    def handle_ui_move(self, move_uci):
        """
        This function is called by the UI when a move is input.
        It validates and applies the move and then triggers a state transition.
        """
        print(f"[UI] Received move: {move_uci}")
        # Validate the move.
        try:
            move = chess.Move.from_uci(move_uci)
        except Exception as e:
            print(f"[UI] Invalid move notation: {move_uci} ({e})")
            return False

        if move not in self.board.legal_moves:
            print(f"[UI] Illegal move attempted: {move_uci}")
            return False
        
        self.process_legal_player_move(move)
        
        #         # Check if the move is a capture before pushing it.
        # if self.board.is_capture(move):
        #     # For a normal capture, the captured piece is on the destination square.
        #     captured_piece = self.board.piece_at(move.to_square)
        #     if captured_piece:
        #         self.captured_pieces.append(captured_piece.symbol())
        #         # Note: You might need special handling for en passant captures.
        
        # self.move_history.append(move_uci)
        # # self.notify_observers()

        # # Apply the move.
        # self.board.push(move)
        # self.notify_observers()
        
        print(f"[Game] Move applied: {move_uci}")
        
        #self.process_move()
        # self.notify_observers()
        Clock.schedule_once(lambda dt: self.process_move(), 0.1)


        # Trigger a state transition.
        # Depending on your design you might trigger a transition here.
        # For example, if you want to signal that the player's move is complete:
        #self.process_move()  # This transition would typically lead to the engine_turn state.
        
        return True
    
    def process_legal_player_move(self, move_str):

        move = chess.Move.from_uci(move_str)

        if self.board.is_capture(move):
            # For a normal capture, the captured piece is on the destination square.
            captured_piece = self.board.piece_at(move.to_square)
            if captured_piece:
                self.captured_pieces.append(captured_piece.symbol())
                # Note: You might need special handling for en passant captures.
        
        self.move_history.append(move.uci())
    
        if self.is_move_checkmate(self.board, move):
            self.checkmate = True
            if self.board.turn == chess.WHITE:
                self.piece_images['k'] = 'assets/black_king_mate.png'
            else:
                self.piece_images['K'] = 'assets/white_king_mate.png'
            
        elif self.board.gives_check(move):
            if self.board.turn == chess.WHITE:
                self.piece_images['k'] = 'assets/black_king_check.png'
                self.game_winner = 'White'
            else:
                self.piece_images['K'] = 'assets/white_king_check.png'
                self.game_winner = 'Black'
            # Make some indication

            self.check = f"{self.board.turn}"
            self.checkmate = False

        else:
            if self.board.turn == chess.WHITE:
                self.piece_images['k'] = 'assets/black_king.png'
            else:
                self.piece_images['K'] = 'assets/white_king.png'
            
            self.check = ""

            self.checkmate = False

        self.legal_moves = None
        print("pushoing move:")

        self.board.push(move)
        self.notify_observers()

        self.rocker.toggle()

        self.notify_observers()
        self.on_player_move_confirmed()

        if self.checkmate:
            self.end_game()

    def process_illegal_player_move(self, move_str):

        # Send piece back to start and rock rocker, then scan for moves again

        """
        Calculate the distance between two chess squares given in text notation (e.g., 'e2e4').
        Returns the Manhattan distance between the squares.
        """

        self.ingame_message = "Illegal Move detected!"
        if len(move_str) != 4:
            raise ValueError("Move must be in the format 'e2e4'.")
        
        STEP_MM = 25

        # move = chess.Move.from_uci(move_str)


        start_square = move_str[:2]
        end_square = move_str[2:]

        # Calculate Manhattan distance

        init_coords = self.gantry.square_to_coord(start_square)
        end_coords = self.gantry.square_to_coord(end_square)

        init_coords = (init_coords[0]*STEP_MM, init_coords[1]*STEP_MM)
        end_coords = (end_coords[0]*STEP_MM, end_coords[1]*STEP_MM)

        path = []
        
        dx = init_coords[0] - end_coords[0]
        dy = init_coords[1] - end_coords[1]

        dx_sign = self.gantry.sign(dx)
        dy_sign = self.gantry.sign(dy)




        offset = STEP_MM

        # Add the final position to the path
        path = [end_coords, (dx - offset*dx_sign, dy-offset*dy_sign), (dx_sign * offset, dy_sign * offset)]


        cmds = self.gantry.movement_to_gcode(path)
        self.gantry.send_commands(cmds)

        # self.rocker.toggle()
        self.notify_observers()

        self.on_player_turn()


    def process_board_move(self, move, is_white):

        captured_symbol = None
        # move = chess.Move.from_uci(move_str)
        if self.board.is_capture(move):
            # For a normal capture, the captured piece is on the destination square.
            captured_piece = self.board.piece_at(move.to_square)
            if captured_piece:
                self.captured_pieces.append(captured_piece.symbol())
                captured_symbol = captured_piece.symbol()

                # Note: You might need special handling for en passant captures.

        self.gantry.interpret_chess_move(f"{move}", self.board.is_capture(move), self.board.is_castling(move), self.board.is_en_passant(move), is_white, captured_symbol)

        
        self.move_history.append(move.uci())
    
        if self.is_move_checkmate(self.board, move):
            self.checkmate = True
            if self.board.turn == chess.WHITE:
                self.piece_images['k'] = 'assets/black_king_mate.png'
                self.game_winner = 'White'
            else:
                self.piece_images['K'] = 'assets/white_king_mate.png'
                self.game_winner = 'Black'
            
        elif self.board.gives_check(move):
            if self.board.turn == chess.WHITE:
                self.piece_images['k'] = 'assets/black_king_check.png'
            else:
                self.piece_images['K'] = 'assets/white_king_check.png'
            # Make some indication

            self.check = f"{self.board.turn}"
            self.checkmate = False

        else:
            if self.board.turn == chess.WHITE:
                self.piece_images['k'] = 'assets/black_king.png'
            else:
                self.piece_images['K'] = 'assets/white_king.png'
            
            self.check = ""

            self.checkmate = False

        self.legal_moves = None
        print("pushing move:")

        self.board.push(move)
        self.notify_observers()

        self.rocker.toggle()

        self.notify_observers()

        if self.checkmate:
            self.end_game()
        else:
            self.engine_move_complete()

        # self.process_legal_player_move(f"{move}")


    # def on_player_first_turn(self):  
    #     print("[State] Entering Player Turn")
    #     self.ingame_message = "Waiting for Player..."

    #     Clock.schedule_once(lambda dt: self.go_to_first_piece_detection(), 5)


    # def on_player_turn(self):
    #     print("[State] Entering Player Turn")

    
    #     Clock.schedule_once(lambda dt: self.go_to_first_piece_detection(), 0.1)
    #     # When entering player's turn, immediately begin hall effect polling.
        
    #     # State transition will stay in this state until a change is detected, then it will go to second state
    # def first_piece_detection_poll(self):

    #     self.ingame_message = "Waiting for Player...."



    #     self.initial_board = copy.deepcopy(self.hall.sense_layer.get_squares_game())

    #     print(self.initial_board)

        
    #     self.selected_piece = None
    #     # while self.selected_piece is None:
             
    #         # #  print("Trying to find first piece")
             
    #         #  new_board = self.hall.sense_layer.get_squares_game()
    #         #  #print(new_board)
    #         #  self.selected_piece = self.hall.compare_boards(new_board, self.initial_board)
    #         #  time.sleep(0.1)
    #     # self.safe_poll_first()


    #     # Start the polling process:
    #     self.safe_poll_first(self.on_piece_found)

    #     while self.selected_piece is None:


    #     print(self.selected_piece)
        

    #     self.notify_observers()

    #     print("going to look for second piece")

    #     Clock.schedule_once(lambda dt: self.go_to_second_piece_detection, 0.1)

    # def safe_poll_first(self, callback):
    #     new_board = self.hall.sense_layer.get_squares_game()
    #     self.selected_piece = self.hall.compare_boards(new_board, self.initial_board)
    #     if self.selected_piece is not None:
    #         callback(self.selected_piece)
    #     else:
    #         Clock.schedule_once(lambda dt: self.safe_poll_first(callback), 0.1)


    # # def safe_poll_second(self):
    # #     # Schedule the next call after 0.1 seconds.

    # #         new_board = self.hall.sense_layer.get_squares_game()
    # #          #print(new_board)
    # #         self.selected_move = self.hall.compare_boards(new_board, self.initial_board)
    # #         if self.selected_move is not None:
    # #             return 
    # #         Clock.schedule_once(self.safe_poll_second, 0.1)


    # def on_piece_found(self,selected_piece):
    #         print("Detected piece:", selected_piece)
    #         # # Now that a piece has been selected, get its legal moves.
    #         # legal_moves = self.control_system.select_piece(selected_piece.chess_square)
    #         # self.highlight_legal_moves(legal_moves)
    #         self.notify_observers()

    # def safe_poll_second(self, callback):
    #     new_board = self.hall.sense_layer.get_squares_game()
    #     self.selected_move = self.hall.compare_boards(new_board, self.initial_board)
    #     if self.selected_move is not None:
    #         callback(self.selected_move)
    #     else:
    #         Clock.schedule_once(lambda dt: self.safe_poll_first(callback), 0.1)



    # def second_piece_detection_poll(self):

        
    #     print("looking for second move")
    #     self.initial_board = copy.deepcopy(self.hall.sense_layer.get_squares_game())
    #     self.selected_move = None
    #     # while self.selected_move is None:

    #     #     new_board = self.hall.sense_layer.get_squares_game()
    #     #     self.selected_move = self.hall.compare_boards(new_board, initial_board)
    #     #     time.sleep(0.1)

    #     # Start the polling process:
    #     self.safe_poll_second(self.on_piece_found)

    #     # print(self.selected_piece)

    #     # self.safe_poll_second()

    #     print(f"done, found move, {self.selected_piece}{self.selected_move}")

    #     if self.selected_piece == self.selected_move:
    #         print("Piece replaced, finding new move")
    #         # selected_piece = None
    #         self.go_to_first_piece_detection()

    #     move_str = f"{self.selected_piece}{self.selected_move}"

    #     self.selected_move = None

    #     print('switch')
    #     print(self.servo.get_switch_state())
    #     if self.use_switch:
    #         print("waiting for switch")
    #         while self.servo.get_switch_state():
    #             time.sleep(0.1)

    #         print('switch passed')

        
    #     move = chess.Move.from_uci(move_str)

    #     legal_moves = [move for move in self.board.legal_moves if move.from_square == chess.parse_square(self.selected_piece)]

    #     print(legal_moves)

    #     if move in legal_moves:
    #         print("Legal move, executing it")

    #         self.process_legal_player_move(move_str)

    #     else:
    #         print("Illegal move, executing YOU")

    #         self.process_illegal_player_move(move_str)

    # def on_player_move_confirmed(self):
    #     print("[State] Player Move Confirmed")
    #     self.update_ui()
    #     # Process the player move.
    #     # For simplicity, here we pick the first legal move.
    #     self.process_move()

    def on_player_first_turn(self):  
        print("[State] Entering Player Turn")
        self.ingame_message = "Waiting for Player..."
        # Start the first-piece detection after a delay (if needed).
        Clock.schedule_once(lambda dt: self.go_to_first_piece_detection(), 2)

    def on_player_turn(self):
        print("[State] Entering Player Turn")
        # Immediately begin first-piece detection.
        Clock.schedule_once(lambda dt: self.go_to_first_piece_detection(), 0.1)

    def first_piece_detection_poll(self):
        self.ingame_message = "Waiting for Player..."
        # Capture the initial board state.
        self.initial_board = copy.deepcopy(self.hall.sense_layer.get_squares_game())
        print("Initial board:", self.initial_board)
        # Reset the selected piece.
        self.selected_piece = None
        # Start polling for the first piece.
        self.safe_poll_first(self.on_first_piece_found)

    def safe_poll_first(self, callback):
        new_board = self.hall.sense_layer.get_squares_game()
        self.selected_piece = self.hall.compare_boards(new_board, self.initial_board)
        if self.selected_piece is not None:
            # Piece found; call the callback with the selected piece.
            callback(self.selected_piece)
        else:
            # Poll again after 0.1 seconds.
            Clock.schedule_once(lambda dt: self.safe_poll_first(callback), 0.1)

    def on_first_piece_found(self, selected_piece):
        print("Detected first piece:", selected_piece)
        self.notify_observers()
        # When the first piece is found, move on to second-piece detection.
        Clock.schedule_once(lambda dt: self.go_to_second_piece_detection(), 0.1)

    def go_to_second_piece_detection(self):
        # Call the second piece detection function.
        self.second_piece_detection_poll()

    def safe_poll_second(self, callback):
        new_board = self.hall.sense_layer.get_squares_game()
        self.selected_move = self.hall.compare_boards(new_board, self.initial_board)
        if self.selected_move is not None:
            callback(self.selected_move)
        else:
            Clock.schedule_once(lambda dt: self.safe_poll_second(callback), 0.1)

    def second_piece_detection_poll(self):
        print("Looking for second move")
        # Update initial board state for the second detection.
        self.initial_board = copy.deepcopy(self.hall.sense_layer.get_squares_game())
        self.selected_move = None
        # Start polling for the second move.
        self.safe_poll_second(self.on_second_piece_found)

    def on_second_piece_found(self, selected_move):
        print("Detected second move:", selected_move)
        # Now that we have both pieces, process the detection.
        print(f"Done, found move: {self.selected_piece}{self.selected_move}")
        # If the same square is selected (i.e. piece replaced), restart first detection.
        if self.selected_piece == self.selected_move:
            print("Piece replaced, finding new move")
            self.go_to_first_piece_detection()
            return

        move_str = f"{self.selected_piece}{self.selected_move}"
        self.selected_move = None  # Reset selected move for next turn

        # Optionally, if you're using a hardware switch and want to wait for it:
        if self.use_switch:
            # Instead of blocking with time.sleep, you can poll the switch status.
            def check_switch(dt):
                if not self.rocker.get_switch_state():
                    print("Switch passed")
                    # Continue processing move.
                    self.process_move_from_str(move_str)
                else:
                    Clock.schedule_once(check_switch, 0.1)
            print("Waiting for switch")
            Clock.schedule_once(check_switch, 0.1)
        else:
            self.process_move_from_str(move_str)

    def process_move_from_str(self, move_str):
        print('Switch passed (or not used), processing move')
        move = chess.Move.from_uci(move_str)
        legal_moves = [m for m in self.board.legal_moves 
                    if m.from_square == chess.parse_square(self.selected_piece)]
        print("Legal moves:", legal_moves)
        if move in legal_moves:
            print("Legal move, executing it")
            self.process_legal_player_move(move_str)
        else:
            print("Illegal move, executing fallback")
            self.process_illegal_player_move(move_str)

    def on_player_move_confirmed(self):
        print("[State] Player Move Confirmed")
        self.update_ui()
        # Process the player move.
        self.process_move()

    def on_board_turn(self):
        print("[State] Engine Turn")
        self.update_ui()
        # Process the engine move asynchronously.
        self.engine_thread = threading.Thread(target=self.compute_engine_move, daemon=True).start()
        #self.compute_engine_move()

    def compute_engine_move(self):
        self.ingame_message = "Engine Thinking.."
        time.sleep(0.2)  # Simulate engine thinking time.
        self.update_ui()

        if self.engine:
            try:
                result = self.engine.play(self.board, chess.engine.Limit(time=self.parameters['engine_time_limit']))
                move = result.move
                print(f"[Engine] Engine move: {move}")

                self.ingame_message = "Executing Board Move"


                if self.board.turn == chess.WHITE:
                    is_white = True
                else: 
                    is_white = False


                self.process_board_move(move, is_white)


                # self.notify_observers()
            except Exception as e:
                print("[Engine] Error computing engine move:", e)
            # finally:
            #     print("[Engine] Shutting down engine...")
            #     self.engine.quit()
            #     self.engine = None
        else:
            legal_moves = list(self.board.legal_moves)
            if legal_moves:
                move = legal_moves[0]
                print(f"[Engine] Fallback move: {move}")
                self.board.push(move)
        # Transition back to player's turn.

        # self.rocker.toggle()
        # self.notify_observers()
        # self.update_ui()
        # self.engine_move_complete()

    def end_game_processes(self):
        self.running = False
        self.victory_lap()
        # Ensure that if an engine is still running, we shut it down.
        if self.engine:
            print("[Engine] Shutting down engine on game over...")
            self.engine.quit()
            # self.engine_thread.join()
            self.engine = None

    # Example backend methods:
    def init_gantry(self):
        pass
        # Asynchronously initialize GRBL serial communication.
        # self.hall = Hall()
        # print("Hall Initialized")
        # Simulate some processing delay before gantry is ready.
        #self.gantry = GantryControl()
        # self.gantry.connect_to_grbl()
        #self.servo = Servo()
        #self.sense = Hall()
        # self.servo.begin()
        #self.gantry_ready()

        #Clock.schedule_once(lambda dt: self.gantry_ready(), 2)

    def init_game(self):
        print("Game has started with parameters:", self.parameters)

        self.game_winner = None
        self.board.reset()
        self.ingame_message = "Starting Game"

        self.first_change = None
        self.second_change = None

        self.legal_moves = None
        self.game_winner = None

        self.rocker.to_white()

        self.update_ui()


        if self.parameters['online']:
            pass
            # Retrieve API key from file
            with open('venv/key.txt', 'r') as f:
                api_key = f.read().strip()  # .strip() removes any extra whitespace or newline characters
        elif not self.parameters['online']:
            #Configure offline game 
            print("Configuring offline game")

            print(f"Engine: {self.engine_path}")

            if self.engine_path:
                try:
                    print(f"Trying to use engine: {self.engine}")
                    self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
                    self.engine.configure({"UCI_LimitStrength": True, "UCI_Elo": self.parameters['elo']})
                    print(f"[Engine] Initialized engine at Elo {self.parameters['elo']}")
                except Exception as e:
                    print("[Engine] Error initializing engine:", e)
                    self.engine = None
            else:
                self.engine = None

            



            pass
        self.clock_logic = ClockLogic(timer_enabled=False)


        # Initialize engine or API for given game parameters 
        self.game_progress = 0  # Reset progress

        # if self.parameters['colour'].lower() == 'white' and not self.parameters['bot_mode']:
        
        # else :   

    def is_move_checkmate(self, board, move):
        """
        Returns True if making the given move on a copy of the board results in checkmate.
        
        Args:
            board (chess.Board): The current board position.
            move (chess.Move): The move to test.
        
        Returns:
            bool: True if the move results in a checkmate, False otherwise.
        """
        board_copy = board.copy()   # Make a copy so we don't modify the original board
        board_copy.push(move)         # Apply the move on the copy
        return board_copy.is_checkmate()  # Check if t

    # Define the default handler for the on_move_processed event.
    def on_move_processed(self, move):
        # This can be empty—its primary purpose is to allow binding from UI.
        pass

    def handle_game_end(self):
        print("Game ended.")
        # Handle win/loss/draw specific logic here.

    def setup_new_game(self):
        print("Setting up new game...")
        self.game_progress = 0  # Reset progress, etc.
        # Transition back to gameplay after setup.
        self.to_gameplay()

    def reset_board_fn(self):
        print("Resetting board...")
        # Reset board logic here.
        self.to_gameplay()
    
    def end_game(self):

        self.game_state = "FINISHED"
        

        # if turn == chess.WHITE:
        #     self.game_winner = "White"
        #     # self.victory_lap('white')
        #     #find white king, victory lap
        # else:
        #     self.game_winner = "Black"
            # self.victory_lap('black')
            #find black king, victory lap  
            # 
        self.end_game_processes()
        Clock.schedule_once(lambda dt: self.go_to_endgamescreen(), 5)

        self.notify_observers()

    def process_predefined_board_move(self, move, is_white):

        captured_symbol = None
        # move = chess.Move.from_uci(move_str)
        if self.board.is_capture(move):
            # For a normal capture, the captured piece is on the destination square.
            captured_piece = self.board.piece_at(move.to_square)
            if captured_piece:
                self.captured_pieces.append(captured_piece.symbol())
                captured_symbol = captured_piece.symbol()

                # Note: You might need special handling for en passant captures.

        self.gantry.interpret_chess_move(f"{move}", self.board.is_capture(move), self.board.is_castling(move), self.board.is_en_passant(move), is_white, captured_symbol)

        
        self.move_history.append(move.uci())
    
        if self.is_move_checkmate(self.board, move):
            self.checkmate = True
            if self.board.turn == chess.WHITE:
                self.piece_images['k'] = 'assets/black_king_mate.png'
                self.game_winner = 'White'
            else:
                self.piece_images['K'] = 'assets/white_king_mate.png'
                self.game_winner = 'Black'
            
        elif self.board.gives_check(move):
            if self.board.turn == chess.WHITE:
                self.piece_images['k'] = 'assets/black_king_check.png'
            else:
                self.piece_images['K'] = 'assets/white_king_check.png'
            # Make some indication

            self.check = f"{self.board.turn}"
            self.checkmate = False

        else:
            if self.board.turn == chess.WHITE:
                self.piece_images['k'] = 'assets/black_king.png'
            else:
                self.piece_images['K'] = 'assets/white_king.png'
            
            self.check = ""

            self.checkmate = False

        self.legal_moves = None
        print("pushing move:")

        self.board.push(move)
        self.notify_observers()

        self.rocker.toggle()

        # self.notify_observers()

        if self.checkmate:
            self.end_game()


    def on_predefined_first_turn(self):

        self.demo_progress = 0
        self.game_winner = None
        self.board.reset()

        self.rocker.to_white()

        self.update_ui()
        
        Clock.schedule_once(lambda dt: self.on_predefined_turn(), 3)

    def on_predefined_turn(self):

        
        self.process_predefined_board_move(chess.Move.from_uci(self.demo_game[self.demo_progress]),  self.demo_progress % 2 == 0)
        #self.notify_observers()
        #self.update_ui()
        self.demo_progress += 1

        Clock.schedule_once(lambda dt: self.on_predefined_turn(), 1)



    def toggle_clock(self):
        self.clock_logic.toggle_active_player()

        self.notify_observers()


    #################################################################################################################
    # Non-state related functions
    #################################################################################################################

    def victory_lap(self):

        white_win = (self.game_winner.lower() == 'white')

        white_king_square = chess.square_name(self.board.king(chess.WHITE))
        black_king_square = chess.square_name(self.board.king(chess.BLACK))

        print("winner white?")
        print(white_win)

        print("white king square")
        print(white_king_square)


        if white_win:
            start_square = f"{white_king_square}"
            end_square = f"{black_king_square}"
        else:
            start_square = f"{black_king_square}"
            end_square = f"{white_king_square}"

        init_coords = self.gantry.square_to_coord(start_square)

        #Only used in king lap mode
        end_coords = self.gantry.square_to_coord(end_square)


        init_coords = (init_coords[0]*25, init_coords[1]*25)
        end_coords = (end_coords[0]*25, end_coords[1]*25)

        # print("testing")

        # print(init_coords)
        # print(init_coords[0])
        # print(init_coords[0] > 180)

        # find closest border corner
        if init_coords[0] > 180:
            close_x = 325
            dx = 1 if init_coords[0] != 350 else -1
        else:
            close_x = 25
            dx = -1 if init_coords[0] != 0 else 1

        if init_coords[1] > 180:
            close_y = 325
            dy = 1 if init_coords[1] != 350 else -1
        else:
            close_y = 25
            dy = -1 if init_coords[1] != 0 else 1

        # print("pasdsed")

        
        


        init_path = [init_coords, (dx*25, dy*25), (0, close_y-(init_coords[1]+dy*25)), (close_x-(init_coords[0]+dx*25), 0)]
        if close_x == 325:
            if close_y == 325:
                loop_path = ([(-6*50, 0), (0, -6*50), (6*50, 0), (0, 6*50)])
            else:
                loop_path = ([(-6*50, 0), (0, 6*50), (6*50, 0), (0, -6*50)])
        else:
            if close_y == 325:
                loop_path = ([(6*50, 0), (0, -6*50), (-6*50, 0), (0, 6*50)])
            else:
                loop_path = ([(6*50, 0), (0, 6*50), (-6*50, 0), (0, -6*50)])

        

        end_path = ([((init_coords[0]+dx*25)-close_x, 0), (0, (init_coords[1]+dy*25)-close_y), (-dx*25, -dy*25)])

        path = init_path + loop_path + end_path


        ## Need to put a lil more thought into this

        # print(path)
        cmds = self.gantry.movement_to_gcode(path)
        self.gantry.send_commands(cmds)

        # self.rocker.toggle()
        self.notify_observers




        pass

    def select_piece(self, square):
        # Find legal moves for the selected piece, update any boards with hgihlighted squares

        legal_moves = [move for move in self.board.legal_moves if move.from_square == square]
        # self.update_board()
        self.update_ui()

        return legal_moves
    

    def on_boardresetscreen(self):
        while True:
            self.notify_observers()
            self.sleep(0.5)
        



# # Kivy UI screens corresponding to UI states
# class StartScreen(Screen):
#     def __init__(self, control_system, **kwargs):
#         super(StartScreen, self).__init__(**kwargs)
#         self.control_system = control_system
#         layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
#         label = Label(text="Welcome to the Automated Chessboard")
#         button = Button(text="Enter Main Menu")
#         button.bind(on_press=self.go_to_menu)
#         layout.add_widget(label)
#         layout.add_widget(button)
#         self.add_widget(layout)

#     def go_to_menu(self, instance):
#         self.control_system.go_to_main_menu()
#         self.manager.current = 'main_menu'


# class MainMenuScreen(Screen):
#     def __init__(self, control_system, **kwargs):
#         super(MainMenuScreen, self).__init__(**kwargs)
#         self.control_system = control_system

#         layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
#         self.param_input = TextInput(multiline=False, hint_text="Game Parameter (e.g., difficulty)")
#         start_game_btn = Button(text="Start Game")
#         manual_btn = Button(text="Manual Gantry Control")
#         settings_btn = Button(text="Settings")
#         start_game_btn.bind(on_press=self.start_game)
#         manual_btn.bind(on_press=self.go_manual)
#         settings_btn.bind(on_press=self.go_settings)

#         layout.add_widget(Label(text="Main Menu"))
#         layout.add_widget(self.param_input)
#         layout.add_widget(start_game_btn)
#         layout.add_widget(manual_btn)
#         layout.add_widget(settings_btn)
#         self.add_widget(layout)

#     def start_game(self, instance):
#         self.control_system.parameters['game_param'] = self.param_input.text
#         self.control_system.start_game()  # Triggers initialize_gantry
#         # Transition will occur when gantry is ready.
#         self.manager.current = 'gameplay'

#     def go_manual(self, instance):
#         self.control_system.open_manual_control()
#         self.manager.current = 'manual_gantry_control'

#     def go_settings(self, instance):
#         self.control_system.open_settings()
#         self.manager.current = 'settings'

# # A simple ScreenManager that holds our GameScreen.
class MainScreenManager(ScreenManager):
    pass

# --------------------------
# Kivy App Integration
# --------------------------
class TestApp(App):
    def build(self):
        # Create an instance of our state machine.
        self.control_system = ChessControlSystem(ui_update_callback=self.on_state_change)
        # Set engine parameters at runtime.
        self.control_system.parameters["engine_path"] = "./bin/stockfish-macos-m1-apple-silicon"  # Adjust this path.
        self.control_system.parameters["engine_time_limit"] = 0.1
        self.control_system.parameters["elo"] = 1400
        self.control_system.parameters["auto_engine"] = False  # Set to True for engine vs. engine.

        self.sm = MainScreenManager(transition=FadeTransition())
        gamescreen = GameScreen(control_system=self.control_system, name="gamescreen")
        initscreen = InitScreen(control_system=self.control_system, name='initscreen')
        loadingscreen = LoadingScreen(control_system=self.control_system, name='loadingscreen')
        mainscreen = MainScreen(control_system=self.control_system, name='mainscreen')
        gantryscreen = GantryControlScreen(control_system=self.control_system, name="gantryscreen")

        self.sm.add_widget(gamescreen)
        self.sm.add_widget(initscreen)
        self.sm.add_widget(loadingscreen)
        self.sm.add_widget(mainscreen)
        self.sm.add_widget(gantryscreen)

        # Start in main menu.
        self.sm.current = 'initscreen'

        # Simulate UI flow.
        Clock.schedule_once(lambda dt: self.control_system.finish_loading(), 3)
        #Clock.schedule_once(lambda dt: self.control_system.finish_init(), 2)
        #Clock.schedule_once(lambda dt: self.control_system.start_game(), 10)

        return self.sm
    
    def on_state_change(self, state):
        print(f"[App] State changed: {state}")
        # Schedule the screen update on the main thread.
        Clock.schedule_once(lambda dt: self.update_screen(state))
    
    def update_screen(self, state):
        """
        This callback is called whenever the state machine updates.
        We map state machine states to screen names:
          - If state is 'mainscreen', show the main menu.
          - If state starts with 'gamescreen', show the game screen.
        """
        if state == 'mainscreen':
            self.sm.current = 'mainscreen'
        elif state.startswith('gamescreen'):
            self.sm.current = 'gamescreen'
        elif state == 'gantryscreen':
            self.sm.current = 'gantryscreen'

        else:
            print("[App] Unhandled state:", state)


if __name__ == '__main__':
    TestApp().run()


