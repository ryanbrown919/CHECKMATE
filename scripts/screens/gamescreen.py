'''
Gameplay loop for playing a game of chess


'''

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
# from kivy.uix.image import Image
# from kivy.uix.widget import Widget
# from kivy.uix.behaviors import ButtonBehavior
# from kivy.graphics import Color, Rectangle
# from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
import chess

from kivy.core.window import Window

# --- Settings ---
Window.fullscreen = True
try:
    from scripts.screens.custom_widgets import HorizontalLine, VerticalLine, IconButton, headerLayout, ChessBoard, MaterialBar, MovesHistory, CapturedPieces, PlayerClock

except:
    from custom_widgets import HorizontalLine, VerticalLine, IconButton, headerLayout, ChessBoard, MaterialBar, MovesHistory, CapturedPieces, PlayerClock
# from .servo import Servo

class GameScreen(Screen):
    def __init__(self, control_system, **kwargs):
        super(GameScreen, self).__init__(**kwargs)
        self.control_system = control_system
        # self.control_system = self.control_system.control_system
        self.clock_logic = self.control_system.clock_logic

        # General Structure of Gameplay Screen
        root_layout = BoxLayout(orientation='vertical', padding=10, spacing=0)

        # Vertical spacing widgets within root
        header_layout = headerLayout(menu=True)
        playarea_layout = BoxLayout(orientation='horizontal', spacing=20, size_hint=(1, 0.9))

        # Horizontal spacing widgets within playarea
        black_layout = BoxLayout(orientation='vertical', spacing=20, size_hint=(0.4, 1))
        middle_layout = BoxLayout(orientation='vertical', spacing=20, size_hint=(0.2, 1))
        white_layout = BoxLayout(orientation='vertical', spacing=20, size_hint=(0.4, 1))

        # Add widgets to root layout
        root_layout.add_widget(header_layout)
        root_layout.add_widget(HorizontalLine())
        root_layout.add_widget(playarea_layout)

        # Add widgets to playarea layout
        playarea_layout.add_widget(black_layout)
        playarea_layout.add_widget(VerticalLine())
        playarea_layout.add_widget(middle_layout)
        playarea_layout.add_widget(VerticalLine())
        playarea_layout.add_widget(white_layout)

    
        self.material_possesion = MaterialBar(size_hint=(1, 0.2), control_system=self.control_system)
        self.move_list = MovesHistory(size_hint=(1, 0.5), control_system=self.control_system)
        self.piece_jail = CapturedPieces(size_hint=(1, 0.3), control_system=self.control_system) 


        black_board = ChessBoard(touch_enabled_black=True, touch_enabled_white=False, bottom_colour_white=False, control_system=self.control_system, size_hint=(1, 1))
        white_board = ChessBoard(touch_enabled_black=True, touch_enabled_white=True, bottom_colour_white=True, control_system=self.control_system, size_hint=(1, 1))
        
        black_layout.add_widget(black_board)
        black_layout.add_widget(HorizontalLine())
        black_clock = PlayerClock(side='black', control_system=self.control_system, size_hint=(1, 0.3))
        black_layout.add_widget(black_clock)

        
        # Middle layout wdigets
        middle_layout.add_widget(Label(text="Material Possession", font_size=40, size_hint=(1, 0.1)))
        middle_layout.add_widget(self.material_possesion)
        #middle_layout.add_widget(HorizontalLine())
        middle_layout.add_widget(Label(text="Move History", font_size=40, size_hint=(1, 0.1)))
        middle_layout.add_widget(self.move_list)
        #middle_layout.add_widget(HorizontalLine())
        middle_layout.add_widget(Label(text="Piece Jail", font_size=40, size_hint=(1, 0.1)))
        middle_layout.add_widget(self.piece_jail)

        white_layout.add_widget(white_board)  
        white_layout.add_widget(HorizontalLine())
        #white_layout.add_widget(PlayerClock(side='white', control_system=self.clock_logic))
        white_clock = PlayerClock(side='white', control_system=self.control_system, size_hint=(1, 0.3))
        white_layout.add_widget(white_clock)
        

        self.add_widget(root_layout)

        # self.control_system.register_observer(self.on_move_update)
        # Clock.schedule_interval(self.refresh_board, 0.1)
        self.control_system.ui_move_callback = self.refresh_board


    def refresh_board(self, dt):
        
        # Update widgets on the screen

        pass



    def on_move_update(self, *args):
        # Update the chess board.
        print("This actually does stuff")
        self.control_system.update_board()
        self.execute_move()
        

    def change_screen(self, screen_name):
        self.manager.transition.direction = 'left'
        self.manager.current = screen_name

    def on_stop(self):
        # This method will be called from the App's on_stop to gracefully shutdown the backend thread.
        if self.control_system.is_alive():
            print("Stopping ChessBackend thread...")
            self.control_system.stop()
            self.control_system.join()
            print("ChessBackend thread stopped.")
        
    def execute_move(self):  
        print("Executing move yo")
        self.clock_logic.toggle_active_player()
        if self.control_system.first_move:
            self.clock_logic.toggle_pause()
            self.control_system.first_move=False
        # if not self.simulation_mode:
        #     path = self.gantry_control.interpret_move(self.control_system.move_history[-1])
        #     movements = self.gantry_control.parse_path_to_movement(path)
        #     commands = self.gantry_control.movement_to_gcode(movements)
        #     self.gantry_control.send_commands(commands)


    