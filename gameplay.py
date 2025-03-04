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

from chessBoard import ChessBoard
from chessClock import ChessClockWidget

class GameplayScreen(Screen):
    def __init__(self, **kwargs):
        super(GameplayScreen, self).__init__(**kwargs)


        root_layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        header_layout = BoxLayout(orientation='horizontal', spacing=20)
        playarea_layout = BoxLayout(orientation='horizontal', spacing=20)
        black_layout = BoxLayout(orientation='vertical', spacing=20)
        white_layout = BoxLayout(orientation='vertical', spacing=20)



        root_layout.add_widget(header_layout)
        header_layout.add_widget(Label(text="Chess Game", font_size=32))
        root_layout.add_widget(playarea_layout)
        playarea_layout.add_widget(black_layout)
        playarea_layout.add_widget(white_layout)

        black_board = ChessBoard(board_size=500, board_origin=(100, 100), bottom_colour_white=False)
        white_board = ChessBoard(board_size=500, board_origin=(1200, 100), bottom_colour_white=True)
        

        black_layout.add_widget(black_board)
        white_layout.add_widget(white_board)    


        self.add_widget(root_layout)













    def change_screen(self, screen_name):
        self.manager.transition.direction = 'left'
        self.manager.current = screen_name
        


class FullApp(App):
    def build(self):
               
        return GameplayScreen()

if __name__ == '__main__':
    FullApp().run()