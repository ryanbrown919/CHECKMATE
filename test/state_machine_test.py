from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from transitions import Machine

# -------------------------
# Game Mechanics State Machine
# -------------------------
class GameStateMachine(object):
    # Define game-related states
    states = ['idle', 'white_turn', 'black_turn', 'check', 'checkmate']

    def __init__(self):
        self.machine = Machine(model=self, states=GameStateMachine.states, initial='idle')
        # Transitions for starting the game and alternating turns.
        self.machine.add_transition(trigger='start_game', source='idle', dest='white_turn')
        self.machine.add_transition(trigger='move_made', source='white_turn', dest='black_turn')
        self.machine.add_transition(trigger='move_made', source='black_turn', dest='white_turn')
        # Transitions for special situations (check, checkmate) could be added here.
    
    def current_turn(self):
        return self.state

# -------------------------
# UI State Machine for Program Flow
# -------------------------
class UIStateMachine(object):
    states = ['loading', 'main_menu', 'game', 'manual_control']

    def __init__(self, app):
        self.app = app
        self.machine = Machine(model=self, states=UIStateMachine.states, initial='loading')
        # Transitions for moving between screens.
        self.machine.add_transition(trigger='loading_complete', source='loading', dest='main_menu', after='update_ui')
        self.machine.add_transition(trigger='start_game_ui', source='main_menu', dest='game', after='update_ui')
        self.machine.add_transition(trigger='manual_control_ui', source='main_menu', dest='manual_control', after='update_ui')
        self.machine.add_transition(trigger='back_to_menu', source=['game', 'manual_control'], dest='main_menu', after='update_ui')

    def update_ui(self):
        # Update the Kivy ScreenManager based on the current state
        print("UI transitioned to:", self.state)
        self.app.sm.current = self.state

# -------------------------
# Kivy Screens
# -------------------------
class LoadingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20)
        layout.add_widget(Image(source='assets/start_logo.png', size_hint=(1, 1), keep_ratio=True, allow_stretch=True))
        layout.add_widget(Label(text="loading game...", font_size=40))
        self.add_widget(layout)

class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20)
        layout.add_widget(Image(source='assets/start_logo.png', size_hint=(1, 1), keep_ratio=True, allow_stretch=True))
        layout.add_widget(Label(text="main game...", font_size=40))
        self.add_widget(layout)

class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20)
        layout.add_widget(Image(source='assets/start_logo.png', size_hint=(1, 1), keep_ratio=True, allow_stretch=True))
        layout.add_widget(Label(text="game game...", font_size=40))
        self.add_widget(layout)

class ManualControlScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20)
        layout.add_widget(Image(source='assets/start_logo.png', size_hint=(1, 1), keep_ratio=True, allow_stretch=True))
        layout.add_widget(Label(text="manual game...", font_size=40))
        self.add_widget(layout)

# -------------------------
# Main Application
# -------------------------
class ChessApp(App):
    def build(self):
        # Set up the screen manager without fancy transitions
        self.sm = ScreenManager(transition=NoTransition())
        self.sm.add_widget(LoadingScreen(name='loading'))
        self.sm.add_widget(MainMenuScreen(name='main_menu'))
        self.sm.add_widget(GameScreen(name='game'))
        self.sm.add_widget(ManualControlScreen(name='manual_control'))

        # Initialize the UI state machine with a reference to the app
        self.ui_state_machine = UIStateMachine(self)

        # Initialize the game state machine separately; it remains inactive until the game starts
        self.game_state_machine = GameStateMachine()

        # Simulate loading (e.g., initializing hardware modules) and then transition to main menu
        Clock.schedule_once(lambda dt: self.ui_state_machine.loading_complete(), 2)

        return self.sm

    def on_start_game(self):
        # Called when the user starts a game; first, update UI
        self.ui_state_machine.start_game_ui()
        # Then, initialize game logic (after collecting parameters, for example)
        self.game_state_machine.start_game()
        print("Game started. Current turn:", self.game_state_machine.current_turn())

if __name__ == '__main__':
    ChessApp().run()




# from kivy.app import App
# from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
# from kivy.uix.boxlayout import BoxLayout
# from kivy.uix.button import Button
# from kivy.uix.label import Label
# from kivy.uix.textinput import TextInput
# from kivy.clock import Clock
# from transitions import Machine

# import logging
# logging.getLogger('transitions').setLevel(logging.WARNING)

# # Define the control system with all required states.
# class ChessControlSystem:
#     states = [
#         'start_screen',         # UI: startup screen - fade after a few seconds (initialize gantry?)
#         'main_menu',            # UI: main menu - select game mode, difficulty etc
#         'gameplay',             # UI: game screen (and backend game state)
#         'manual_gantry_control',# UI: manual control
#         'settings',             # UI: settings
#         'initialize_gantry',    # Backend: initialize gantry via serial
#         'white_turn',           # Backend: white move processing
#         'black_turn',           # Backend: black move processing
#         'game_win',             # Backend: game finished (win)
#         'game_loss',            # Backend: game finished (loss)
#         'game_draw',            # Backend: game finished (draw)
#         'start_new_game',       # Backend: prepare for a new game
#         'reset_board'           # Backend: board reset logic
#     ]

#     def __init__(self):
#         # Start in the start screen state.
#         self.machine = Machine(model=self, states=ChessControlSystem.states, initial='start_screen')
#         self.parameters = {}  # Parameters set via the UI
#         self.game_progress = 0  # Just an example variable

#         # UI transitions:
#         self.machine.add_transition(trigger='go_to_main_menu', source='start_screen', dest='main_menu')
#         self.machine.add_transition(trigger='open_manual_control', source=['main_menu', 'gameplay'], dest='manual_gantry_control')
#         self.machine.add_transition(trigger='open_settings', source=['main_menu', 'manual_gantry_control', 'gameplay'], dest='settings')

#         # Start game transitions:
#         self.machine.add_transition(trigger='start_game', source='main_menu', dest='initialize_gantry', after='init_gantry')
#         # Once gantry is initialized, move to gameplay
#         self.machine.add_transition(trigger='gantry_ready', source='initialize_gantry', dest='gameplay', after='begin_game')

#         # Game backend transitions
#         self.machine.add_transition(trigger='white_move', source='gameplay', dest='black_turn', after='process_white_move')
#         self.machine.add_transition(trigger='black_move', source='gameplay', dest='white_turn', after='process_black_move')

#         # End-of-game transitions (win, loss, or draw)
#         self.machine.add_transition(trigger='win', source='gameplay', dest='game_win', after='handle_game_end')
#         self.machine.add_transition(trigger='loss', source='gameplay', dest='game_loss', after='handle_game_end')
#         self.machine.add_transition(trigger='draw', source='gameplay', dest='game_draw', after='handle_game_end')

#         # New game and reset board
#         self.machine.add_transition(trigger='new_game', source=['game_win', 'game_loss', 'game_draw'], dest='start_new_game', after='setup_new_game')
#         self.machine.add_transition(trigger='reset', source='*', dest='reset_board', after='reset_board_fn')

#     # Example backend methods:
#     def init_gantry(self):
#         # Asynchronously initialize GRBL serial communication.
#         print("Initializing gantry communication...")
#         # Simulate some processing delay before gantry is ready.
#         self.gantry_ready()
#         #Clock.schedule_once(lambda dt: self.gantry_ready(), 2)

#     def begin_game(self):
#         print("Game has started with parameters:", self.parameters)
#         self.game_progress = 0  # Reset progress

#     def process_white_move(self):
#         print("Processing white move...")
#         self.game_progress += 1
#         # After processing, return to gameplay
#         self.to_gameplay()

#     def process_black_move(self):
#         print("Processing black move...")
#         self.game_progress += 1
#         self.to_gameplay()

#     def handle_game_end(self):
#         print("Game ended.")
#         # Handle win/loss/draw specific logic here.

#     def setup_new_game(self):
#         print("Setting up new game...")
#         self.game_progress = 0  # Reset progress, etc.
#         # Transition back to gameplay after setup.
#         self.to_gameplay()

#     def reset_board_fn(self):
#         print("Resetting board...")
#         # Reset board logic here.
#         self.to_gameplay()


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


# class GameScreen(Screen):
#     def __init__(self, control_system, **kwargs):
#         super(GameScreen, self).__init__(**kwargs)
#         self.control_system = control_system

#         layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
#         self.status_label = Label(text="Game is active...")
#         # Buttons to simulate moves
#         white_move_btn = Button(text="Simulate White Move")
#         black_move_btn = Button(text="Simulate Black Move")
#         white_move_btn.bind(on_press=lambda instance: self.control_system.white_move())
#         black_move_btn.bind(on_press=lambda instance: self.control_system.black_move())

#         layout.add_widget(self.status_label)
#         layout.add_widget(white_move_btn)
#         layout.add_widget(black_move_btn)
#         self.add_widget(layout)

#         # Periodically update the screen based on backend progress
#         Clock.schedule_interval(self.update_status, 0.1)

#     def update_status(self, dt):
#         # For example, update progress or turn info
#         self.status_label.text = f"Game progress: {self.control_system.game_progress}"


# class ManualGantryControlScreen(Screen):
#     def __init__(self, control_system, **kwargs):
#         super(ManualGantryControlScreen, self).__init__(**kwargs)
#         layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
#         layout.add_widget(Label(text="Manual Gantry Control"))
#         back_btn = Button(text="Back to Main Menu")
#         back_btn.bind(on_press=lambda instance: self.switch_back())
#         layout.add_widget(back_btn)
#         self.add_widget(layout)

#     def switch_back(self):
#         self.manager.current = 'main_menu'


# class SettingsScreen(Screen):
#     def __init__(self, control_system, **kwargs):
#         super(SettingsScreen, self).__init__(**kwargs)
#         layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
#         layout.add_widget(Label(text="Settings"))
#         back_btn = Button(text="Back to Main Menu")
#         back_btn.bind(on_press=lambda instance: self.switch_back())
#         layout.add_widget(back_btn)
#         self.add_widget(layout)

#     def switch_back(self):
#         self.manager.current = 'main_menu'


# # The main Kivy App that manages the screens.
# class ChessApp(App):
#     def build(self):
#         self.control_system = ChessControlSystem()

#         sm = ScreenManager(transition=FadeTransition())
#         sm.add_widget(StartScreen(self.control_system, name='start_screen'))
#         sm.add_widget(MainMenuScreen(self.control_system, name='main_menu'))
#         sm.add_widget(GameScreen(self.control_system, name='gameplay'))
#         sm.add_widget(ManualGantryControlScreen(self.control_system, name='manual_gantry_control'))
#         sm.add_widget(SettingsScreen(self.control_system, name='settings'))

#         # Start with the start screen.
#         sm.current = 'start_screen'
#         return sm


# if __name__ == '__main__':
#     ChessApp().run()
