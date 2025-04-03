"""
Comprehensive Gameplay Loop for Chess with Dynamic Screen Layout

This file demonstrates how to build a Kivy-based chess game screen that updates
its layout dynamically depending on parameter values. Each time the screen is entered,
the layout is re-built to reflect any changes in parameters (e.g., demo mode, local play,
or board colour settings). A dummy control system is provided for demonstration purposes.
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
import chess
from kivy.core.window import Window
from kivy.uix.popup import Popup

# Set the application to fullscreen.
Window.fullscreen = True

# Import custom widgets; if the module is not available, try an alternate location.
try:
    from scripts.screens.custom_widgets import HorizontalLine, VerticalLine, IconButton, headerLayout, ChessBoard, MaterialBar, MovesHistory, CapturedPieces, PlayerClock
except ImportError:
    from custom_widgets import HorizontalLine, VerticalLine, IconButton, headerLayout, ChessBoard, MaterialBar, MovesHistory, CapturedPieces, PlayerClock


class GameScreen(Screen):
    """
    GameScreen is the main screen for gameplay.
    The layout is built dynamically based on the control_system parameters,
    ensuring that changes (like switching game mode) are reflected every time the screen is entered.
    """
    def __init__(self, control_system, **kwargs):
        super(GameScreen, self).__init__(**kwargs)
        self.control_system = control_system
        self.font_size = self.control_system.font_size
        self.ingame_message = self.control_system.ingame_message
        self.clock_logic = self.control_system.clock_logic

        # Root layout for the screen.
        self.root_layout = BoxLayout(orientation='vertical', padding=10, spacing=0)

        # Header layout.
        self.header_layout = headerLayout(control_system=self.control_system, menu=False)
        
        # Play area layout which holds the black board/area, a middle panel, and the white board/area.
        self.playarea_layout = BoxLayout(orientation='horizontal', spacing=20, size_hint=(1, 0.9))
        
        # Sub-layouts for each section of the play area.
        self.black_layout = BoxLayout(orientation='vertical', spacing=20, size_hint=(0.4, 1))
        self.middle_layout = BoxLayout(orientation='vertical', spacing=20, size_hint=(0.2, 1))
        self.white_layout = BoxLayout(orientation='vertical', spacing=20, size_hint=(0.4, 1))

        # Assemble the root layout.
        self.root_layout.add_widget(self.header_layout)
        self.root_layout.add_widget(HorizontalLine())
        self.root_layout.add_widget(self.playarea_layout)
        
        # Add the sub-layouts into the play area.
        self.playarea_layout.add_widget(self.black_layout)
        self.playarea_layout.add_widget(VerticalLine())
        self.playarea_layout.add_widget(self.middle_layout)
        self.playarea_layout.add_widget(VerticalLine())
        self.playarea_layout.add_widget(self.white_layout)

        # Additional widgets for the middle panel.
        self.material_possesion = MaterialBar(size_hint=(1, 0.2), control_system=self.control_system)
        self.move_list = MovesHistory(size_hint=(1, 0.5), control_system=self.control_system)
        self.piece_jail = CapturedPieces(size_hint=(1, 0.3), control_system=self.control_system)

        # Initially build the screen layout based on the current parameters.
        self.build_screen_layout()

        # Add the root layout to the screen.
        self.add_widget(self.root_layout)

        # Register the refresh_board callback for when a UI move is executed.
        self.control_system.ui_move_callback = self.refresh_board

    def build_screen_layout(self):
        """
        Constructs the dynamic layout of the game screen based on current parameters.
        This method clears any existing widgets in the layout containers and re-adds them.
        """
        # Clear any previous widgets if the layout is being rebuilt.
        self.black_layout.clear_widgets()
        self.middle_layout.clear_widgets()
        self.white_layout.clear_widgets()

        params = self.control_system.parameters

        # The layout configuration changes based on game parameters.
        if params.get('bot_mode') or params.get('demo_mode'):
            print("Initializing bot_mode or demo_mode layout")
            # Both boards are non-interactive.
            black_board = ChessBoard(touch_enabled_black=False, touch_enabled_white=False,
                                     bottom_colour_white=False, control_system=self.control_system, size_hint=(1, 1))
            white_board = ChessBoard(touch_enabled_black=False, touch_enabled_white=False,
                                     bottom_colour_white=True, control_system=self.control_system, size_hint=(1, 1))
        elif params.get('local_mode'):
            print("Initializing local_mode layout")
            # Both boards are interactive in a local game.
            black_board = ChessBoard(touch_enabled_black=True, touch_enabled_white=False,
                                     bottom_colour_white=False, control_system=self.control_system, size_hint=(1, 1))
            white_board = ChessBoard(touch_enabled_black=False, touch_enabled_white=True,
                                     bottom_colour_white=True, control_system=self.control_system, size_hint=(1, 1))
        elif params.get('colour') == 'white':
            print("Initializing white game layout")
            # Playing as white: show a chessboard on the white side and a message on the black side.
            white_board = ChessBoard(touch_enabled_black=False, touch_enabled_white=False,
                                     bottom_colour_white=True, control_system=self.control_system, size_hint=(1, 1))
            black_board = Label(text=self.ingame_message, font_size=50)
        else:
            print("Initializing default game layout (playing as black)")
            # Default mode: playing as black; interactive black board and a message on the white side.
            black_board = ChessBoard(touch_enabled_black=True, touch_enabled_white=False,
                                     bottom_colour_white=False, control_system=self.control_system, size_hint=(1, 1))
            white_board = Label(text=self.ingame_message, font_size=50)

        # Build the black layout with board and clock.
        self.black_layout.add_widget(black_board)
        self.black_layout.add_widget(HorizontalLine())
        black_clock = PlayerClock(side='black', control_system=self.control_system, size_hint=(1, 0.3))
        self.black_layout.add_widget(black_clock)

        # Build the middle layout with additional game information.
        self.middle_layout.add_widget(Label(text="Material Possession", size_hint=(1, 0.1), font_size=self.font_size))
        self.middle_layout.add_widget(self.material_possesion)
        self.middle_layout.add_widget(Label(text="Move History", size_hint=(1, 0.1), font_size=self.font_size))
        self.middle_layout.add_widget(self.move_list)
        self.middle_layout.add_widget(Label(text="Piece Jail", size_hint=(1, 0.1), font_size=self.font_size))
        self.middle_layout.add_widget(self.piece_jail)

        # Build the white layout with board and clock.
        self.white_layout.add_widget(white_board)
        self.white_layout.add_widget(HorizontalLine())
        white_clock = PlayerClock(side='white', control_system=self.control_system, size_hint=(1, 0.3))
        self.white_layout.add_widget(white_clock)

    def on_pre_enter(self, *args):
        """
        This method is called every time the screen is about to be displayed.
        It rebuilds the layout to ensure that any changes in parameter values
        are accurately reflected.
        """
        print("Entering GameScreen: rebuilding layout with updated parameters.")
        self.build_screen_layout()
        self.refresh_board(0)

    def refresh_board(self, dt):
        """
        Callback function to update widgets on the screen.
        For example, it checks the game state and updates the board or clocks.
        """
        # If the game is finished, show an endgame popup.
        if self.control_system.game_state == 'FINISHED':
            self.show_endgame_popup()
        # Additional widget refresh logic can be placed here.

    def show_endgame_popup(self):
        """
        Displays a popup when the game has ended.
        """
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text="Game Over", font_size=40))
        exit_btn = Button(text="Exit", size_hint=(1, 0.3), font_size=30)
        content.add_widget(exit_btn)
        popup = Popup(title="Endgame", content=content, size_hint=(0.5, 0.5))
        exit_btn.bind(on_release=popup.dismiss)
        popup.open()

    def on_move_update(self, *args):
        """
        Callback invoked when a move is made.
        This updates the board and executes any additional move logic.
        """
        print("Updating board after move")
        self.control_system.update_board()
        self.execute_move()

    def change_screen(self, screen_name):
        """
        Changes the active screen using the screen manager.
        """
        self.manager.transition.direction = 'left'
        self.manager.current = screen_name

    def on_stop(self):
        """
        Called when the app is stopping.
        Gracefully stops the backend control system if it is still running.
        """
        if self.control_system.is_alive():
            print("Stopping ChessBackend thread...")
            self.control_system.stop()
            self.control_system.join()
            print("ChessBackend thread stopped.")

    def execute_move(self):
        """
        Executes a move by toggling the active player's clock and performing any
        additional move-related operations.
        """
        print("Executing move")
        self.clock_logic.toggle_active_player()
        if self.control_system.first_move:
            self.clock_logic.toggle_pause()
            self.control_system.first_move = False





# '''
# Gameplay loop for playing a game of chess


# '''

# from kivy.app import App
# from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
# from kivy.uix.floatlayout import FloatLayout
# from kivy.uix.boxlayout import BoxLayout
# from kivy.uix.button import Button
# from kivy.uix.label import Label
# # from kivy.uix.image import Image
# # from kivy.uix.widget import Widget
# # from kivy.uix.behaviors import ButtonBehavior
# # from kivy.graphics import Color, Rectangle
# # from kivy.uix.scrollview import ScrollView
# from kivy.clock import Clock
# import chess

# from kivy.core.window import Window

# # --- Settings ---
# Window.fullscreen = True
# try:
#     from scripts.screens.custom_widgets import HorizontalLine, VerticalLine, IconButton, headerLayout, ChessBoard, MaterialBar, MovesHistory, CapturedPieces, PlayerClock

# except:
#     from custom_widgets import HorizontalLine, VerticalLine, IconButton, headerLayout, ChessBoard, MaterialBar, MovesHistory, CapturedPieces, PlayerClock
# from kivy.uix.popup import Popup
# from kivy.uix.label import Label
# from kivy.uix.boxlayout import BoxLayout
# from kivy.uix.button import Button
# # from .servo import Servo

# class GameScreen(Screen):
#     def __init__(self, control_system, **kwargs):
#         super(GameScreen, self).__init__(**kwargs)
#         self.control_system = control_system
#         self.font_size = self.control_system.font_size
#         self.ingame_message = self.control_system.ingame_message
#         # self.control_system = self.control_system.control_system
#         self.clock_logic = self.control_system.clock_logic

#         # General Structure of Gameplay Screen
#         root_layout = BoxLayout(orientation='vertical', padding=10, spacing=0)

#         # Vertical spacing widgets within root
#         header_layout = headerLayout(control_system=self.control_system, menu=False)
#         playarea_layout = BoxLayout(orientation='horizontal', spacing=20, size_hint=(1, 0.9))

#         # Horizontal spacing widgets within playarea
#         black_layout = BoxLayout(orientation='vertical', spacing=20, size_hint=(0.4, 1))
#         middle_layout = BoxLayout(orientation='vertical', spacing=20, size_hint=(0.2, 1))
#         white_layout = BoxLayout(orientation='vertical', spacing=20, size_hint=(0.4, 1))

#         # Add widgets to root layout
#         root_layout.add_widget(header_layout)
#         root_layout.add_widget(HorizontalLine())
#         root_layout.add_widget(playarea_layout)

#         # Add widgets to playarea layout
#         playarea_layout.add_widget(black_layout)
#         playarea_layout.add_widget(VerticalLine())
#         playarea_layout.add_widget(middle_layout)
#         playarea_layout.add_widget(VerticalLine())
#         playarea_layout.add_widget(white_layout)

    
#         self.material_possesion = MaterialBar(size_hint=(1, 0.2), control_system=self.control_system)
#         self.move_list = MovesHistory(size_hint=(1, 0.5), control_system=self.control_system)
#         self.piece_jail = CapturedPieces(size_hint=(1, 0.3), control_system=self.control_system) 

#         if self.control_system.parameters['bot_mode'] or self.control_system.parameters['demo_mode']:
#             print("bot_mode or demo_mode")

#             black_board = ChessBoard(touch_enabled_black=False, touch_enabled_white=False, bottom_colour_white=False, control_system=self.control_system, size_hint=(1, 1))
#             white_board = ChessBoard(touch_enabled_black=False, touch_enabled_white=False, bottom_colour_white=True, control_system=self.control_system, size_hint=(1, 1))

#         elif self.control_system.parameters['local_mode']:
#             print("local game agaisnt board")

#             black_board = ChessBoard(touch_enabled_black=True, touch_enabled_white=False, bottom_colour_white=False, control_system=self.control_system, size_hint=(1, 1))
#             white_board = ChessBoard(touch_enabled_black=False, touch_enabled_white=True, bottom_colour_white=True, control_system=self.control_system, size_hint=(1, 1))

#         elif self.control_system.parameters['colour'] == 'white':
#             print("white game agaisnt board")
#             white_board = ChessBoard(touch_enabled_black=False, touch_enabled_white=False, bottom_colour_white=True, control_system=self.control_system, size_hint=(1, 1))
#             black_board = Label(Text = self.ingame_message, font_size = 50)
#         else:
#             print("else")
#             black_board = ChessBoard(touch_enabled_black=True, touch_enabled_white=False, bottom_colour_white=False, control_system=self.control_system, size_hint=(1, 1))
#             white_board = Label(Text = self.ingame_message, font_size = 50)

    
        
#         black_layout.add_widget(black_board)
#         black_layout.add_widget(HorizontalLine())
#         black_clock = PlayerClock(side='black', control_system=self.control_system, size_hint=(1, 0.3))
#         black_layout.add_widget(black_clock)

        
#         # Middle layout wdigets
#         middle_layout.add_widget(Label(text="Material Possession", size_hint=(1, 0.1), font_size = self.font_size))
#         middle_layout.add_widget(self.material_possesion)
#         #middle_layout.add_widget(HorizontalLine())
#         middle_layout.add_widget(Label(text="Move History", size_hint=(1, 0.1), font_size = self.font_size))
#         middle_layout.add_widget(self.move_list)
#         #middle_layout.add_widget(HorizontalLine())
#         middle_layout.add_widget(Label(text="Piece Jail", size_hint=(1, 0.1), font_size = self.font_size))
#         middle_layout.add_widget(self.piece_jail)

#         white_layout.add_widget(white_board)  
#         white_layout.add_widget(HorizontalLine())
#         #white_layout.add_widget(PlayerClock(side='white', control_system=self.clock_logic))
#         white_clock = PlayerClock(side='white', control_system=self.control_system, size_hint=(1, 0.3))
#         white_layout.add_widget(white_clock)
        

#         self.add_widget(root_layout)

#         # self.control_system.register_observer(self.on_move_update)
#         # Clock.schedule_interval(self.refresh_board, 0.1)
#         self.control_system.ui_move_callback = self.refresh_board


#     def refresh_board(self, dt):
        
#         # Update widgets on the screen

#         if self.control_system.game_state == 'FINSIHED':
#             self.show_endgame_popup(self)

#         pass



#     def on_move_update(self, *args):
#         # Update the chess board.
#         print("This actually does stuff")
#         self.control_system.update_board()
#         self.execute_move()
        

#     def change_screen(self, screen_name):
#         self.manager.transition.direction = 'left'
#         self.manager.current = screen_name

#     def on_stop(self):
#         # This method will be called from the App's on_stop to gracefully shutdown the backend thread.
#         if self.control_system.is_alive():
#             print("Stopping ChessBackend thread...")
#             self.control_system.stop()
#             self.control_system.join()
#             print("ChessBackend thread stopped.")
        
#     def execute_move(self):  
#         print("Executing move yo")
#         self.clock_logic.toggle_active_player()
#         if self.control_system.first_move:
#             self.clock_logic.toggle_pause()
#             self.control_system.first_move=False
#         # if not self.simulation_mode:
#         #     path = self.gantry_control.interpret_move(self.control_system.move_history[-1])
#         #     movements = self.gantry_control.parse_path_to_movement(path)
#         #     commands = self.gantry_control.movement_to_gcode(movements)
#         #     self.gantry_control.send_commands(commands)


