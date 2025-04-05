from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from kivy.core.window import Window
Window.fullscreen = True

FONT_SIZE=40
try:
    from custom_widgets import RoundedButton, MatrixWidget


except:
    from checkmate.screens.custom_widgets import RoundedButton, headerLayout, HorizontalLine, DemoToggleButton

from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle

class DemoScreen(Screen):
    def __init__(self, control_system, **kwargs):
        def __init__(self, control_system, **kwargs):
            super().__init__(**kwargs)
            self.control_system = control_system
            self.font_size = self.control_system.font_size
            root = BoxLayout(orientation='vertical', padding=10)

            header_layout = headerLayout(menu=False)


            demo_layout = BoxLayout(orientation='vertical', padding=10)

            demo1 = BoxLayout(orientation='horizontal', padding=10)
            demo2 = BoxLayout(orientation='horizontal', padding=10)
            demo3 = BoxLayout(orientation='horizontal', padding=10)
            demo3 = BoxLayout(orientation='horizontal', padding=10)
            demo4 = BoxLayout(orientation='horizontal', padding=10)
            demo5 = BoxLayout(orientation='horizontal', padding=10)


            capture_label = Label(test="Test capture", font_size=self.font_size)
            capture_toggle = DemoToggleButton(size_hint=(0.3, 1))
            capture_btn = RoundedButton(text="Test White Capture", font_size = self.font_size, size_hint=(0.4, 1))
            capture_btn.bind(on_release=lambda instace: self.white_capture())

            demo1.add_widget(capture_label)
            demo1.add_widget(capture_toggle)
            demo1.add_widget(capture_btn)

            knight_label = Label(test="Knight Movement", font_size=self.font_size)
            knight_toggle = DemoToggleButton(size_hint=(0.3, 1))
            knight_btn = RoundedButton(text="Test Knight Movement", font_size = self.font_size, size_hint=(0.4, 1))
            knight_btn.bind(on_release=lambda instace: self.white_capture())

            demo2.add_widget(knight_label)
            demo2.add_widget(knight_toggle)
            demo2.add_widget(knight_btn)

            white_capture_label = Label(test="", font_size=self.font_size)
            white_capture_btn = RoundedButton(text="Test White Capture", font_size = self.font_size, size_hint=(0.4, 1))
            white_capture_btn.bind(on_release=lambda instace: self.white_capture())

            demo3.add_widget(white_capture_label)
            demo3.add_widget(knight_toggle)
            demo3.add_widget(white_capture_btn)

            white_capture_label = Label(test="Victory Lap", font_size=self.font_size)
            white_capture_btn = RoundedButton(text="Test White Capture", font_size = self.font_size, size_hint=(0.4, 1))
            white_capture_btn.bind(on_release=lambda instace: self.white_capture())

            demo4.add_widget(white_capture_label)
            demo4.add_widget(white_capture_btn)

            white_capture_label = Label(test="Test white capture", font_size=self.font_size)
            white_capture_btn = RoundedButton(text="Test White Capture", font_size = self.font_size, size_hint=(0.4, 1))
            white_capture_btn.bind(on_release=lambda instace: self.white_capture())

            demo5.add_widget(white_capture_label)
            demo5.add_widget(white_capture_btn)




            
            # layout.add_widget(Image(source='assets/start_logo.png', size_hint=(1, 1), keep_ratio=True, allow_stretch=True))


            endgame_text = "FUCK ME"

            endgame_label = Label(text=endgame_text, font_size=40)

            reset_btn = RoundedButton(text= "Reset Board and Return to Menu", font_size = 40)
            reset_btn.bind(on_release= lambda instance:self.reset_and_return())

            layout.add_widget(board)
            layout.add_widget(endgame_label)

            root.add_widget(header_layout)

            root.add_widget(layout)

            root.add_widget(reset_btn)

            self.add_widget(root)


class MyApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(DemoScreen(control_system=None, name='boardreset'))
        return sm


if __name__ == '__main__':
    MyApp().run()