from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.core.window import Window
Window.fullscreen = True

try:
    from custom_widgets import ChessBoard, headerLayout, RoundedButton
except:
    from scripts.screens.custom_widgets import ChessBoard, headerLayout, RoundedButton


class EndGameScreen(Screen):
    def __init__(self, control_system, **kwargs):
        super().__init__(**kwargs)
        self.control_system = control_system
        root = BoxLayout(orientation='vertical', padding=10)

        header_layout = headerLayout(menu=False)


        layout = BoxLayout(orientation='horizontal', padding=10)
        # layout.add_widget(Image(source='assets/start_logo.png', size_hint=(1, 1), keep_ratio=True, allow_stretch=True))

        board = ChessBoard(touch_enabled_black=False, touch_enabled_white=True, bottom_colour_white=True, control_system=self.control_system, size_hint=(1, 1))

        endgame_text = "FUCK ME"

        endgame_label = Label(text=endgame_text, font_size=40)

        reset_btn = RoundedButton(text= "Reset Board and Return to Menu", font_size = 40)
        reset_btn.bind(on_release= lambda instance:self.reset_and_return())

        layout.add_widget(board)
        layout.add_widget(endgame_text)

        root.add_widget(header_layout)

        root.add_widget(layout)

        root.add_widget()


        self.add_widget(root)

    def reset_and_return(self):
        
        self.control_system.go_to_mainscreen()
        #self.control_system.reset_board_from_game()




class MyApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(EndGameScreen(control_system=None, name='init'))
        return sm


if __name__ == '__main__':
    MyApp().run()