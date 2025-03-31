from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
Window.fullscreen = True

FONT_SIZE=40

from custom_widgets import RoundedButton
class BoardResetScreen(Screen):
    def __init__(self, control_system, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10)
        #layout.add_widget(Image(source='assets/start_logo.png', size_hint=(1, 1), keep_ratio=True, allow_stretch=True))
        custom1 = RoundedButton(text="[size=70][b]Play Game[/b][/size]\n[size=40]Color: White\nElo: 1500[/size]", markup=True, font_size=FONT_SIZE, size_hint=(1, 1))
        layout.add_widget(custom1)
        self.add_widget(layout)


class MyApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(BoardResetScreen(control_system=None, name='boardreset'))
        return sm


if __name__ == '__main__':
    MyApp().run()