'''
Gameplay loop for playing a game of chess


'''

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.scrollview import ScrollView

import chess

from chessBoard import ChessBoard
from chessClock import ChessClockWidget
from game_logic import gameLogic
from menu import HorizontalLine

class GameplayScreen(Screen):
    def __init__(self, **kwargs):
        super(GameplayScreen, self).__init__(**kwargs)


        root_layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        header_layout = BoxLayout(orientation='horizontal', spacing=20, size_hint=(1, 0.1))
        playarea_layout = BoxLayout(orientation='horizontal', spacing=20)
        black_layout = BoxLayout(orientation='vertical', spacing=20)
        middle_layout = BoxLayout(orientation='vertical', spacing=20)
        white_layout = BoxLayout(orientation='vertical', spacing=20)


        root_layout.add_widget(header_layout)
        header_layout.add_widget(Label(text="Check-M.A.T.E", font_size=120, size_hint=(0.4, 1)))
        header_layout.add_widget(Widget(size_hint_x=0.5))
        icon = Image(source='figures/logo.png', allow_stretch=True, keep_ratio=True, size_hint=(0.1, 1))
        header_layout.add_widget(icon)
        root_layout.add_widget(HorizontalLine())

        root_layout.add_widget(playarea_layout)
        playarea_layout.add_widget(black_layout)
        playarea_layout.add_widget(middle_layout)
        playarea_layout.add_widget(white_layout)

        gameLogic_instance = gameLogic()

        move_list = ScrollView()
        piece_jail = BoxLayout(orientation='horizontal', spacing=20)

        black_board = ChessBoard(board_size=600, board_origin=(100, 100), bottom_colour_white=False, game_logic=gameLogic_instance)
        white_board = ChessBoard(board_size=600, board_origin=(1200, 100), bottom_colour_white=True, game_logic=gameLogic_instance)
        

        black_layout.add_widget(black_board)
        middle_layout.add_widget(move_list)
        middle_layout.add_widget(piece_jail)
        white_layout.add_widget(white_board)    


        self.add_widget(root_layout)









    def on_move_entered(self, instance):
        move_str = instance.text
        try:
            # Try to interpret the move as a UCI move
            move = chess.Move.from_uci(move_str)
            if move not in self.chess_board.game_board.legal_moves:
                # If the move is not legal in UCI format, try interpreting it as a SAN move
                move = self.chess_board.game_board.parse_san(move_str)
            
            instance.text = ""
        except ValueError:
            self.add_debug_message(f"Invalid move format: {move_str}")
            instance.text = ""

    def add_debug_message(self, message):
        """Add a debug message to the move list container."""
        label = Label(text=message, size_hint_y=None, height=40)
        self.move_list_container.add_widget(label)

    def change_screen(self, screen_name):
        self.manager.transition.direction = 'left'
        self.manager.current = screen_name
        


class FullApp(App):
    def build(self):
               
        return GameplayScreen()

if __name__ == '__main__':
    FullApp().run()