from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
Window.fullscreen = True

FONT_SIZE=40
try:
    from custom_widgets import RoundedButton, MatrixWidget


except:
    from scripts.screens.custom_widgets import RoundedButton

from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
class BoardResetScreen(Screen):
    def __init__(self, control_system, **kwargs):
        super().__init__(**kwargs)

        self.control_system = control_system
        layout = BoxLayout(orientation='vertical', padding=10)
        #layout.add_widget(Image(source='assets/start_logo.png', size_hint=(1, 1), keep_ratio=True, allow_stretch=True))



   

        #custom1 = MatrixWidget(control_system = self.control_system)

        reset_btn = RoundedButton(text="Reset Board from FEN", size_hint=(0.6, 0.4), font_size=50)
        reset_btn.bind(on_release=lambda instance: self.control_system.reset_control.full_reset())
        



        #layout.add_widget(custom1)
        layout.add_widget(reset_btn)
        self.add_widget(layout)


class MyApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(BoardResetScreen(control_system=None, name='boardreset'))
        return sm


if __name__ == '__main__':
    MyApp().run()