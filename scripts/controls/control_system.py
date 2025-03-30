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

import logging
logging.getLogger('transitions').setLevel(logging.WARNING)


# from gantry_control import GantryControl, ClockLogic
# #from game_control import ChessControlSystem
# from servo_control import Servo

try:
    from controls.gantry_control import GantryControl, ClockLogic
    from controls.servo_control import Servo
    from controls.hall_control import Hall

    from screens.gamescreen import GameScreen
    from screens.initscreen import InitScreen
    from screens.loadingscreen import LoadingScreen
    from screens.mainscreen import MainScreen
    from screens.gantryscreen import GantryControlScreen

except:
    from scripts.controls.gantry_control import GantryControl, ClockLogic
    from scripts.controls.servo_control import Servo
    from scripts.controls.hall_control import Hall


    from scripts.screens.gamescreen import GameScreen
    from scripts.screens.initscreen import InitScreen
    from scripts.screens.loadingscreen import LoadingScreen
    from scripts.screens.mainscreen import MainScreen
    from scripts.screens.gantryscreen import GantryControlScreen

# except:
#     from gantry_control import GantryControl, ClockLogic
#     #from backend_scripts.game_control import ChessControlSystem
#     from servo_control import Servo



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
            'end_game'
        ]
        },
        'gantryscreen',
        'settingsscreen'
    ]


    def __init__(self, ui_update_callback=None):
        # Start in the start screen state.
        self.ui_update_callback = ui_update_callback
        self.capture_move = False

        self.board = chess.Board()  # Integrated chess board.
        self.running = True
        if running_on_pi:
            self.engine_path = "./bin/stockfish-android-armv8"
        elif running_on_mac:
            self.engine_path = "./bin/stockfish-macos-m1-apple-silicon"
        else:
            print("Need to download windows stockfish")
            self.engine_path = None
        
        self.parameters = {'online': False, 'colour': "black", 'elo': 1500, 'timer': False, 'engine_time_limit': 0.1, 'bot_mode': True}  # Default parameters to be set by the user 


        
        # Create a hierarchical state machine.
        self.machine = Machine(model=self, states=ChessControlSystem.states, initial='initscreen')

        # Top-level transitions. dj
        #self.machine.add_transition(trigger='finish_loading', source='initscreen', dest='mainscreen', after='update_ui')
        #self.machine.add_transition(trigger='launch_game', source='mainscreen', dest='gamescreen_player_turn', after='on_player_turn')
        # self.machine.add_transition(trigger='finish_loading', source='initscreen', dest='gamescreen_engine_turn', after=['init_game', 'on_board_turn'], conditions=['board_turn'])

        self.machine.add_transition(trigger='finish_loading', source='initscreen', dest='mainscreen', before='init_gantry', after=['update_ui'])
        # Two transitions for starting the game based on who goes first.
        self.machine.add_transition(trigger='start_game', source='mainscreen', dest='gamescreen_player_turn',
                                    conditions=lambda: self.parameters["colour"] == "white",
                                    unless='is_auto_engine_mode',
                                    after=['init_game', 'update_ui', 'on_player_turn'])
        self.machine.add_transition(trigger='start_game', source='mainscreen', dest='gamescreen_engine_turn',
                                    conditions=lambda: self.parameters["colour"] == "black",
                                    unless='is_auto_engine_mode',
                                    after=['init_game', 'update_ui', 'on_board_turn'])
        
        self.machine.add_transition(trigger='start_game', source='mainscreen', dest='gamescreen_engine_turn',
                                    conditions=lambda: self.parameters["bot_mode"] == True,
                                    after=['init_game', 'update_ui', 'on_board_turn'])

        


        # Nested transitions inside gamescreen.
        # Note: When referring to nested states, use the full path: e.g. gamescreen_player_turn.
        self.machine.add_transition(trigger='begin_polling', source='gamescreen_player_turn', dest='gamescreen_hall_polling', after='on_hall_polling')
        self.machine.add_transition(trigger='move_detected', source='gamescreen_hall_polling', dest='gamescreen_player_move_confirmed', after='on_player_move_confirmed')
        self.machine.add_transition(trigger='process_move', source=['gamescreen_player_turn', 'gamescreen_player_move_confirmed'], dest='gamescreen_engine_turn', after=['on_board_turn', 'toggle_clock', 'notify_observers'])
        #self.machine.add_transition(trigger='engine_move_complete', source='gamescreen_engine_turn', dest='gamescreen_player_turn', after='on_player_turn')

        self.machine.add_transition(trigger='engine_move_complete', source='gamescreen_engine_turn', dest='gamescreen_engine_turn',
                                    conditions='is_auto_engine_mode', after=['on_board_turn', 'notify_observers'])
        # Otherwise, transition to player_turn.
        self.machine.add_transition(trigger='engine_move_complete', source='gamescreen_engine_turn', dest='gamescreen_player_turn',
                                    unless='is_auto_engine_mode', after=['on_player_turn', 'notify_observers'])


        self.machine.add_transition(trigger='end_game', source='gamescreen', dest='gamescreen_end_game', after='on_end_game')

        self.machine.add_transition(trigger='go_to_gantry', source='mainscreen', dest='gantryscreen', after='update_ui')

        #self.machine = Machine(model=self, states=ChessControlSystem.states, initial='initscreen')
        self.game_progress = 0  # Just an example variable

        self.engine = None

        self.servo = None
        self.gantry = GantryControl()
        self.move_history = []
        self.captured_pieces = []
        self.SQUARES = chess.SQUARES
        self.observers = []
        self.game_state = "UNFINISHED"
        

        


        # self.game_logic = ChessBackend(lichess_token=api_key, ui_move_callback=None, mode="offline",
        #                    engine_time_limit=0.1, difficulty_level=5, elo=self.elo, colour=self.colour, clock_logic = self.clock_logic, bot_mode=self.bot_mode, gantry_control=self.gantry_control)
        #self.clock_logic = None
        self.clock_logic = ClockLogic(timer_enabled=False)

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
            self.ui_update_callback(state)

            # Condition method used for transitions.
    def is_auto_engine_mode(self):
        return self.parameters['bot_mode']
    
    def register_observer(self, callback):
        """Register a callback that will be called when the board changes."""
        self.observers.append(callback)
    
    def notify_observers(self):
        """Call all registered observer callbacks with the updated board."""
        for callback in self.observers:
            callback(self.board)

    # def start_game(self):
    #     self.to_gamescreen()
    #     pass




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
        
                # Check if the move is a capture before pushing it.
        if self.board.is_capture(move):
            # For a normal capture, the captured piece is on the destination square.
            captured_piece = self.board.piece_at(move.to_square)
            if captured_piece:
                self.captured_pieces.append(captured_piece.symbol())
                # Note: You might need special handling for en passant captures.
        
        self.move_history.append(move_uci)
        # self.notify_observers()

        # Apply the move.
        self.board.push(move)
        self.notify_observers()
        
        print(f"[Game] Move applied: {move_uci}")
        
        #self.process_move()
        # self.notify_observers()
        Clock.schedule_once(lambda dt: self.process_move(), 0.1)


        # Trigger a state transition.
        # Depending on your design you might trigger a transition here.
        # For example, if you want to signal that the player's move is complete:
        #self.process_move()  # This transition would typically lead to the engine_turn state.
        
        return True

    def on_player_turn(self):
        print("[State] Entering Player Turn")
        self.update_ui()
        # When entering player's turn, immediately begin hall effect polling.
        #wait until UI move 
        self.hall_thread_running = True  # Add a flag to control the thread
        # self.hall_thread = threading.Thread(target=self.sense.poll_board_for_change, daemon=True)
        # self.hall_thread.start()

        # while self.sense.move is None:
        #     time.sleep(0.5)

        # self.stop_hall_thread()
        # self.go_to_player_move_confirmed
        

    def stop_hall_thread(self):
        self.hall_thread_running = False
        if self.hall_thread and self.hall_thread.is_alive():
            self.hall_thread.join()  # Wait for the thread to finish

        pass

    def on_player_move_confirmed(self):
        print("[State] Player Move Confirmed")
        self.update_ui()
        # Process the player move.
        # For simplicity, here we pick the first legal move.
        legal_moves = list(self.board.legal_moves)
        # if self.sense.move in legal_moves:
        
        #     print(f"[Game Engine] Processing player move: {self.sense.move}")
        #     self.board.push(self.sense.move)
        # # Transition to engine turn.
        #     self.process_move()

        #     self.update_ui()


    # def on_hall_polling(self):
    #     print("[State] Hall Polling Active")
    #     self.update_ui()
    #     # Start sensor polling asynchronously.
    #     threading.Thread(target=self.simulate_hall_polling, daemon=True).start()

    # def simulate_hall_polling(self):
    #     # Simulate asynchronous hall effect sensor polling.
    #     time.sleep(1)  # Delay simulating waiting for a player's move.
    #     # In a real system, when the sensor detects a move, trigger:
    #     self.move_detected()


    def on_player_move_confirmed(self):
        print("[State] Player Move Confirmed")
        self.update_ui()
        # Process the player move.
        # For simplicity, here we pick the first legal move.
        legal_moves = list(self.board.legal_moves)
        if legal_moves:
            move = legal_moves[0]
            print(f"[Game Engine] Processing player move: {move}")
            self.board.push(move)
        # Transition to engine turn.
        self.process_move()

    def on_board_turn(self):
        print("[State] Engine Turn")
        self.update_ui()
        # Process the engine move asynchronously.
        threading.Thread(target=self.compute_engine_move, daemon=True).start()
        #self.compute_engine_move()

    def compute_engine_move(self):
        time.sleep(0.2)  # Simulate engine thinking time.
        self.update_ui()

        if self.engine:
            try:
                result = self.engine.play(self.board, chess.engine.Limit(time=self.parameters['engine_time_limit']))
                move = result.move
                print(f"[Engine] Engine move: {move}")

                self.gantry.interpret_chess_move(f"{move}", self.board.is_capture(move))
                
                        # Check if the move is a capture before pushing it.
                if self.board.is_capture(move):
                    # For a normal capture, the captured piece is on the destination square.
                    captured_piece = self.board.piece_at(move.to_square)
                    if captured_piece:
                        self.captured_pieces.append(captured_piece.symbol())
                        # Note: You might need special handling for en passant captures.
                
                self.move_history.append(move.uci())

                


                self.board.push(move)

                self.notify_observers()
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

        time.sleep(0.5)

        # self.notify_observers()
        self.update_ui()
        self.engine_move_complete()

    def on_game_over(self):
        print("[State] Game Over")
        self.update_ui()
        self.running = False
        # Ensure that if an engine is still running, we shut it down.
        if self.engine:
            print("[Engine] Shutting down engine on game over...")
            self.engine.quit()
            self.engine = None

    # Example backend methods:
    def init_gantry(self):
        # Asynchronously initialize GRBL serial communication.
        print("Initializing gantry communication...")
        # Simulate some processing delay before gantry is ready.
        self.gantry = GantryControl()
        self.gantry.connect_to_grbl()
        self.servo = Servo()
        #self.sense = Hall()
        # self.servo.begin()
        #self.gantry_ready()

        #Clock.schedule_once(lambda dt: self.gantry_ready(), 2)

    def init_game(self):
        print("Game has started with parameters:", self.parameters)

        self.update_ui()


        if self.parameters['online']:
            pass
            # Retrieve API key from file
            with open('venv/key.txt', 'r') as f:
                api_key = f.read().strip()  # .strip() removes any extra whitespace or newline characters
        elif not self.parameters['online']:
            #Configure offline game 

            # if self.parameters['colour'] == 'Random':
            #     self.colour = random.choice(['White', 'Black'])
            #     self.auto_engine = False
            # elif self.parameters['colour'] == "BotVBot":
            #     time.sleep(2)
            #     self.auto_engine = True
            #     self.engine_colour = chess.WHITE

            # if self.parameters['colour'] == "Black":
            #     time.sleep(2)
            #     self.engine_colour = chess.WHITE
            #     self.auto_engine = False
            # else:
            #     self.engine_colour = chess.BLACK
            #     self.auto_engine = False

            # if self.parameters['bot_mode']:
            #     time.sleep(2)

            if self.engine_path:
                try:
                    self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
                    self.engine.configure({"UCI_LimitStrength": True, "UCI_Elo": self.parameters['elo']})
                    print(f"[Engine] Initialized engine at Elo {self.parameters['elo']}")
                except Exception as e:
                    print("[Engine] Error initializing engine:", e)
                    self.engine = None
            else:
                self.engine = None

            



            pass

        # look to adjust this as needed
        self.game_logic=None
        self.clock_logic = None
        #self.game_logic = ChessBackend(self.parameters)

        # Initialize engine or API for given game parameters 
        self.game_progress = 0  # Reset progress



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

    def toggle_clock(self):
        if self.board.turn:
            print("It's White's turn.")
            self.clock_logic.active_player=1
            #self.servo.white()
        else:
            self.clock_logic.active_player=2
            #self.servo.black()
            print("It's Black's turn.")

        self.notify_observers()


    #################################################################################################################
    # Non-state related functions
    #################################################################################################################

    def select_piece(self, square):
        # Find legal moves for the selected piece, update any boards with hgihlighted squares

        legal_moves = [move for move in self.board.legal_moves if move.from_square == square]
        # self.update_board()
        self.update_ui()

        return legal_moves



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
# class MainScreenManager(ScreenManager):
#     pass

# # --------------------------
# # Kivy App Integration
# # --------------------------
# class TestApp(App):
#     def build(self):
#         # Create an instance of our state machine.
#         self.control_system = ChessControlSystem(ui_update_callback=self.on_state_change)
#         # Set engine parameters at runtime.
#         self.control_system.parameters["engine_path"] = "./bin/stockfish-macos-m1-apple-silicon"  # Adjust this path.
#         self.control_system.parameters["engine_time_limit"] = 0.1
#         self.control_system.parameters["elo"] = 1400
#         self.control_system.parameters["auto_engine"] = False  # Set to True for engine vs. engine.

#         self.sm = MainScreenManager(transition=FadeTransition())
#         gamescreen = GameScreen(control_system=self.control_system, name="gamescreen")
#         initscreen = InitScreen(control_system=self.control_system, name='initscreen')
#         loadingscreen = LoadingScreen(control_system=self.control_system, name='loadingscreen')
#         mainscreen = MainScreen(control_system=self.control_system, name='mainscreen')
#         gantryscreen = GantryControlScreen(control_system=self.control_system, name="gantryscreen")

#         self.sm.add_widget(gamescreen)
#         self.sm.add_widget(initscreen)
#         self.sm.add_widget(loadingscreen)
#         self.sm.add_widget(mainscreen)
#         self.sm.add_widget(gantryscreen)

#         # Start in main menu.
#         self.sm.current = 'initscreen'

#         # Simulate UI flow.
#         Clock.schedule_once(lambda dt: self.control_system.finish_loading(), 3)
#         #Clock.schedule_once(lambda dt: self.control_system.finish_init(), 2)
#         #Clock.schedule_once(lambda dt: self.control_system.start_game(), 10)

#         return self.sm
    
#     def on_state_change(self, state):
#         print(f"[App] State changed: {state}")
#         # Schedule the screen update on the main thread.
#         Clock.schedule_once(lambda dt: self.update_screen(state))
    
#     def update_screen(self, state):
#         """
#         This callback is called whenever the state machine updates.
#         We map state machine states to screen names:
#           - If state is 'mainscreen', show the main menu.
#           - If state starts with 'gamescreen', show the game screen.
#         """
#         if state == 'mainscreen':
#             self.sm.current = 'mainscreen'
#         elif state.startswith('gamescreen'):
#             self.sm.current = 'gamescreen'
#         elif state == 'gantryscreen':
#             self.sm.current = 'gantryscreen'

#         else:
#             print("[App] Unhandled state:", state)


# if __name__ == '__main__':
#     TestApp().run()


