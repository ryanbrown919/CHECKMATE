from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
Window.fullscreen = True

class InitScreen(Screen):
    def __init__(self, control_system, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10)
        layout.add_widget(Image(source='assets/start_logo.png', size_hint=(1, 1), keep_ratio=True, allow_stretch=True))
        self.add_widget(layout)


class MyApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(InitScreen(control_system=None, name='init'))
        return sm


if __name__ == '__main__':
    MyApp().run()