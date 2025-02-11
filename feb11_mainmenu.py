# main.py
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image

# Global font size for the whole application.
FONT_SIZE = 32

class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super(MainMenuScreen, self).__init__(**kwargs)
        # Root layout: horizontal to allow buttons on the left and icon on the right.
        root_layout = BoxLayout(orientation='horizontal', padding=20, spacing=20)
        
        # Left side: vertical BoxLayout for buttons.
        button_layout = BoxLayout(orientation='vertical', spacing=10, size_hint=(0.6, 1))
        
        btn_chess = Button(text="Chess Playing Mode", size_hint=(1, 0.2), font_size=FONT_SIZE)
        btn_chess.bind(on_release=lambda instance: self.change_screen("chess"))
        button_layout.add_widget(btn_chess)

        btn_gantry = Button(text="Manual Gantry Control", size_hint=(1, 0.2), font_size=FONT_SIZE)
        btn_gantry.bind(on_release=lambda instance: self.change_screen("gantry"))
        button_layout.add_widget(btn_gantry)

        btn_clock = Button(text="Chess Clock Tester", size_hint=(1, 0.2), font_size=FONT_SIZE)
        btn_clock.bind(on_release=lambda instance: self.change_screen("clock"))
        button_layout.add_widget(btn_clock)
        
        # Fourth button for a new widget/screen.
        btn_new = Button(text="RFID Test", size_hint=(1, 0.2), font_size=FONT_SIZE)
        btn_new.bind(on_release=lambda instance: self.change_screen("rfid"))
        button_layout.add_widget(btn_new)

        root_layout.add_widget(button_layout)

        # Right side: a large icon.
        # Replace 'icon.png' with your icon file.
        icon = Image(source='figures/logo.png', allow_stretch=True, keep_ratio=True, size_hint=(0.4, 1))
        root_layout.add_widget(icon)

        self.add_widget(root_layout)

    def change_screen(self, screen_name):
        self.manager.transition.direction = 'left'
        self.manager.current = screen_name

class BaseScreen(Screen):
    """
    Base class that adds a reusable "Back" button positioned at the top right.
    """
    def add_back_button(self, parent_layout):
        back_btn = Button(text="Back", size_hint=(None, None), size=(100, 50),
                          font_size=FONT_SIZE * 0.75, pos_hint={'right': 1, 'top': 1})
        back_btn.bind(on_release=lambda instance: self.go_back())
        parent_layout.add_widget(back_btn)

    def go_back(self):
        self.manager.transition.direction = 'right'
        self.manager.current = "menu"

class ChessGameScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(ChessGameScreen, self).__init__(**kwargs)
        root = FloatLayout()
        content = BoxLayout(orientation='vertical', size_hint=(1, 1), padding=[0, 60, 0, 0])
        content.add_widget(Label(text="Chess Playing Mode\n(Chessboard UI goes here)", font_size=FONT_SIZE))
        root.add_widget(content)
        self.add_back_button(root)
        self.add_widget(root)

class GantryControlScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(GantryControlScreen, self).__init__(**kwargs)
        root = FloatLayout()
        content = BoxLayout(orientation='vertical', size_hint=(1, 1), padding=[0, 60, 0, 0])
        content.add_widget(Label(text="Manual Gantry Control", font_size=FONT_SIZE))
        root.add_widget(content)
        self.add_back_button(root)
        self.add_widget(root)

class ChessClockTesterScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(ChessClockTesterScreen, self).__init__(**kwargs)
        root = FloatLayout()
        content = BoxLayout(orientation='vertical', size_hint=(1, 1), padding=[0, 60, 0, 0])
        content.add_widget(Label(text="Chess Clock Tester", font_size=FONT_SIZE))
        root.add_widget(content)
        self.add_back_button(root)
        self.add_widget(root)

class RFIDScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(RFIDScreen, self).__init__(**kwargs)
        root = FloatLayout()
        content = BoxLayout(orientation='vertical', size_hint=(1, 1), padding=[0, 60, 0, 0])
        content.add_widget(Label(text="New Widget Screen\n(Place your new widget here)", font_size=FONT_SIZE))
        root.add_widget(content)
        self.add_back_button(root)
        self.add_widget(root)

class FullApp(App):
    def build(self):
        sm = ScreenManager(transition=SlideTransition())
        sm.add_widget(MainMenuScreen(name="menu"))
        sm.add_widget(ChessGameScreen(name="chess"))
        sm.add_widget(GantryControlScreen(name="gantry"))
        sm.add_widget(ChessClockTesterScreen(name="clock"))
        sm.add_widget(RFIDScreen(name="newwidget"))
        return sm

if __name__ == '__main__':
    FullApp().run()
