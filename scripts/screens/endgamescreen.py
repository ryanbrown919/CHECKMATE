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

        header_layout = headerLayout(control_system = self.control_system, menu=False)


        layout = BoxLayout(orientation='horizontal', padding=10)

        right_layout = BoxLayout(orientation='vertical')
        # layout.add_widget(Image(source='assets/start_logo.png', size_hint=(1, 1), keep_ratio=True, allow_stretch=True))

        board = ChessBoard(touch_enabled_black=False, touch_enabled_white=True, bottom_colour_white=True, control_system=self.control_system, size_hint=(1, 1))

        endgame_text = self.control_system.endgame_message

        endgame_label = Label(text=endgame_text, font_size=40)

        reset_btn = RoundedButton(text= "Reset Board", font_size = 40)
        reset_btn.bind(on_release= lambda instance:self.reset_and_return())

        home_btn = RoundedButton(text= "Return to Menu", font_size = 40)
        home_btn.bind(on_release= lambda instance:self.return_to_menu())

        

        
        right_layout.add_widget(endgame_label)
        right_layout.add_widget(reset_btn)
        right_layout.add_widget(home_btn)

        root.add_widget(header_layout)
        layout.add_widget(board)

        layout.add_widget(right_layout)


        root.add_widget(layout)

        layout.add_widget(reset_btn)

        self.add_widget(root)

    def reset_and_return(self):
        
        # self.control_system.go_to_mainscreen()
        self.control_system.resetboard()

    def return_home(self):

        self.control_system.go_to_mainscreen()






class MyApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(EndGameScreen(control_system=None, name='init'))
        return sm


if __name__ == '__main__':
    MyApp().run()