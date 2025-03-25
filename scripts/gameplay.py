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

from kivy.core.window import Window

# --- Settings ---
Window.fullscreen = True



from .chessBoard import ChessBoard, MaterialBar, MovesHistory, CapturedPieces, PlayerClock
from .chessBackend import ChessBackend, clock_logic
from .customWidgets import HorizontalLine, VerticalLine, IconButton, headerLayout
from .gantryControl import gantryControl

class GameplayScreen(Screen):
    def __init__(self, gantry_control=None, preferred_color=None, elo=None, bot_mode=False, **kwargs):
        super(GameplayScreen, self).__init__(**kwargs)

        self.elo = elo
        self.preferred_color = preferred_color
        self.bot_mode=bot_mode
        print(f"Elo: {self.elo}, Color: {self.preferred_color}, Bot Game: {self.bot_mode}")


        self.gantry_control=gantry_control
        if self.gantry_control is None:
            self.gantry_control=gantryControl()
            self.gantry_control.connect_to_grbl()
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

        # Retrieve API key from file
        with open('venv/key.txt', 'r') as f:
            api_key = f.read().strip()  # .strip() removes any extra whitespace or newline characters

        def ui_callback(move):
            print("Received opponent move:", move)
            Clock.schedule_once(lambda dt: self.gameLogic_instance.notify_observers(), 0)

        self.clock_logic = clock_logic(timer_enabled=False)

        # Start an instance of game logic, hard coded to bot play right now
        self.gameLogic_instance = ChessBackend(lichess_token=api_key, ui_move_callback=ui_callback, mode="offline",
                           engine_time_limit=0.1, difficulty_level=5, elo=self.elo, preferred_color=self.preferred_color, clock_logic = self.clock_logic, bot_mode=self.bot_mode, gantry_control=self.gantry_control)

        # Start a new game and start the backend thread
        #self.gameLogic_instance.start_game()
        self.gameLogic_instance.start()

        # self.gantry_control = gantryControl()
        # try:
        #     self.gantry_control.connect_to_grbl()
        # except:
        #     pass
        self.simulation_mode = self.gantry_control.simulate

    
        
        # Start a game against a bot immediately.
        # Adjust parameters (bot_username, level, clock settings) as needed.
    
        self.material_possesion = MaterialBar(size_hint=(1, 0.2), game_logic=self.gameLogic_instance)
        self.move_list = MovesHistory(size_hint=(1, 0.5), game_logic=self.gameLogic_instance)
        self.piece_jail = CapturedPieces(size_hint=(1, 0.3), game_logic=self.gameLogic_instance) 


        black_board = ChessBoard(touch_enabled_black=True, touch_enabled_white=False, bottom_colour_white=False, game_logic=self.gameLogic_instance, size_hint=(1, 1))
        white_board = ChessBoard(touch_enabled_black=True, touch_enabled_white=True, bottom_colour_white=True, game_logic=self.gameLogic_instance, size_hint=(1, 1))
        
        black_layout.add_widget(black_board)
        black_layout.add_widget(HorizontalLine())
        black_clock = PlayerClock(side='black', clock_instance=self.clock_logic, size_hint=(1, 0.3))
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
        #white_layout.add_widget(PlayerClock(side='white', clock_instance=self.clock_logic))
        white_clock = PlayerClock(side='white', clock_instance=self.clock_logic, size_hint=(1, 0.3))
        white_layout.add_widget(white_clock)
        



        
          
        

        self.add_widget(root_layout)



        self.gameLogic_instance.register_observer(self.on_move_update)

    def on_move_update(self, *args):
        # Update the chess board.
        print("This actually does stuff")
        self.gameLogic_instance.update_board()
        self.execute_move()
        

    def change_screen(self, screen_name):
        self.manager.transition.direction = 'left'
        self.manager.current = screen_name

    def on_stop(self):
        # This method will be called from the App's on_stop to gracefully shutdown the backend thread.
        if self.gameLogic_instance.is_alive():
            print("Stopping ChessBackend thread...")
            self.gameLogic_instance.stop()
            self.gameLogic_instance.join()
            print("ChessBackend thread stopped.")
        
    def execute_move(self):  
        print("Executing move yo")
        self.clock_logic.toggle_active_player()
        if self.gameLogic_instance.first_move:
            self.clock_logic.toggle_pause()
            self.gameLogic_instance.first_move=False
        # if not self.simulation_mode:
        #     path = self.gantry_control.interpret_move(self.gameLogic_instance.move_history[-1])
        #     movements = self.gantry_control.parse_path_to_movement(path)
        #     commands = self.gantry_control.movement_to_gcode(movements)
        #     self.gantry_control.send_commands(commands)


        


class FullApp(App):
    def build(self):

        self.chess_widget = GameplayScreen()
               
        return self.chess_widget
    
    def on_stop(self):
        # Ensure that the backend thread is stopped when the app exits.
        self.chess_widget.on_stop()

if __name__ == '__main__':
    FullApp().run()