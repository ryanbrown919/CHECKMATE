'''
Main Menu 

'''
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.widget import Widget

from chessBoard import ChessGameWidget
from chessClock import ChessClockWidget 
from gantryControl import GantryControlWidget
from rfidScanner import NFCWidget
from hallEffects import ChessBoardHallEffect

# Global font size for the whole application.
FONT_SIZE = 32

from kivy.graphics import Color, Rectangle

class HorizontalLine(Widget):
    def __init__(self, **kwargs):
        super(HorizontalLine, self).__init__(**kwargs)
        # Disable automatic sizing on the y-axis and set a fixed height (e.g., 2 pixels)
        self.size_hint_y = None
        self.height = 2
        with self.canvas:
            # Set the line color (black in this example)
            Color(255, 255, 255, 1)
            # Draw a rectangle that will act as the horizontal line
            self.rect = Rectangle(pos=self.pos, size=self.size)
        # Bind updates so the rectangle resizes/repositions with the widget
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super(MainMenuScreen, self).__init__(**kwargs)
        # Root layout: Vertical BoxLayout to allow buttons on the top and icon on the bottom.
        # Header layout: horizontal boxlayout? between title and options
        # Body layout: horizontal boxlayout? between buttons for gameplay and side_panel options
        # Play layout: vertical boxlayout? split between quickplay and set game options

        root_layout = BoxLayout(orientation='vertical', padding=10, spacing=0)
        header_layout = BoxLayout(orientation='horizontal', padding=10, spacing=0, size_hint=(1, 0.2))
        body_layout = BoxLayout(orientation='horizontal', padding=20, spacing=20)
        play_layout = BoxLayout(orientation='vertical', padding=20, spacing=20, size_hint=(0.9,1))
        quickplay_layout = BoxLayout(orientation='horizontal', padding=20, spacing=20, size_hint=(1,0.7))
        customplay_layout = BoxLayout(orientation='horizontal', padding=20, spacing=20, size_hint=(1,0.3))
        option_layout = BoxLayout(orientation='vertical', padding=20, spacing=20, size_hint=(0.1,1))

        root_layout.add_widget(header_layout)
        root_layout.add_widget(HorizontalLine())
        root_layout.add_widget(body_layout)
        body_layout.add_widget(play_layout)
        body_layout.add_widget(option_layout)
        play_layout.add_widget(Label(text="Quickplay", font_size=FONT_SIZE, size_hint=(1, 0.1), pos_hint={'left': 0}))
        play_layout.add_widget(quickplay_layout)
        play_layout.add_widget(customplay_layout)

        header_layout.add_widget(Label(text="Check-M.A.T.E", font_size=120, size_hint=(0.4, 1)))
        header_layout.add_widget(Widget(size_hint_x=0.5))
        icon = Image(source='figures/logo.png', allow_stretch=True, keep_ratio=True, size_hint=(0.1, 1))
        header_layout.add_widget(icon)

        

        quickplay_layout.add_widget(Button(text="Quickplay", font_size=FONT_SIZE, size_hint=(1, 1)))
        quickplay_layout.add_widget(Button(text="Quick Play", size_hint=(1, 1), font_size=FONT_SIZE))
        quickplay_layout.add_widget(Button(text="Set Game", size_hint=(1, 1), font_size=FONT_SIZE))
        quickplay_layout.add_widget(Button(text="Load Game", size_hint=(1, 1), font_size=FONT_SIZE))

        customplay_layout.add_widget(Button(text="Start Game", font_size=FONT_SIZE, size_hint=(0.4, 1)))
        customplay_layout.add_widget(Button(text="Set Modes", size_hint=(0.6, 1), font_size=FONT_SIZE))


        option_layout.add_widget(Button(text="Settings", size_hint=(1, 0.1), font_size=FONT_SIZE))
        option_layout.add_widget(Button(text="Help", size_hint=(1, 0.1), font_size=FONT_SIZE))
        option_layout.add_widget(Button(text="About", size_hint=(1, 0.1), font_size=FONT_SIZE))




        
        







        self.add_widget(root_layout)


        # Left side: vertical BoxLayout for buttons.
        











        # header_layout = BoxLayout(orientation='vertical', padding=20, spacing=10, size_hint=(1,1))

        # header_layout.add_widget(Label(text="Welcome to the Chess Robot!", font_size=FONT_SIZE))

        # option_layout = BoxLayout(orientation='horizontal', padding=20, spacing=20, size_hint=(0.1,0.7))

        # root_layout = BoxLayout(orientation='horizontal', padding=20, spacing=20)
        
        # # Left side: vertical BoxLayout for buttons.
        # button_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint=(0.6, 1))

        
        # btn_chess = Button(text="Chess Playing Mode", size_hint=(1, 0.15), font_size=FONT_SIZE)
        # btn_chess.bind(on_release=lambda instance: self.change_screen("chess"))
        # button_layout.add_widget(btn_chess)

        # btn_gantry = Button(text="Manual Gantry Control", size_hint=(1, 0.15), font_size=FONT_SIZE)
        # btn_gantry.bind(on_release=lambda instance: self.change_screen("gantry"))
        # button_layout.add_widget(btn_gantry)

        # btn_clock = Button(text="Chess Clock Tester", size_hint=(1, 0.15), font_size=FONT_SIZE)
        # btn_clock.bind(on_release=lambda instance: self.change_screen("clock"))
        # button_layout.add_widget(btn_clock)
        
        # # Fourth button for a new widget/screen.
        # btn_new = Button(text="RFID Test", size_hint=(1, 0.15), font_size=FONT_SIZE)
        # btn_new.bind(on_release=lambda instance: self.change_screen("rfid"))
        # button_layout.add_widget(btn_new)

        # # Fourth button for a new widget/screen.
        # btn_new = Button(text="Hall Effect Test", size_hint=(1, 0.15), font_size=FONT_SIZE)
        # btn_new.bind(on_release=lambda instance: self.change_screen("halleffect"))
        # button_layout.add_widget(btn_new)

        # root_layout.add_widget(button_layout)

        # # Right side: a large icon.
        # # Replace 'icon.png' with your icon file.
        # icon = Image(source='figures/logo.png', allow_stretch=True, keep_ratio=True, size_hint=(0.4, 1))
        # root_layout.add_widget(icon)

        # column = BoxLayout(orientation='vertical', spacing=10, padding = 20, size_hint=(0.1, 1))
        # column.add_widget(Label(text="Welcome to the Chess Robot!", font_size=FONT_SIZE))
        # root_layout.add_widget(column)

        # header_layout.add_widget(root_layout)
        # header_layout.add_widget(option_layout)
        # self.add_widget(header_layout)

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
        #root = FloatLayout()
        root = BoxLayout(orientation='vertical', spacing=10, padding = 20)
        root.add_widget(ChessGameWidget())
        #root.add_widget(content)
        self.add_back_button(root)
        self.add_widget(root)

class GantryControlScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(GantryControlScreen, self).__init__(**kwargs)
        #root = FloatLayout()
        root = BoxLayout(orientation='vertical', spacing=10, padding = 20)
        root.add_widget(GantryControlWidget())
        
        self.add_back_button(root)
        self.add_widget(root)

class ChessClockTesterScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(ChessClockTesterScreen, self).__init__(**kwargs)
        #root = FloatLayout()
        root = BoxLayout(orientation='vertical', spacing=10, padding = 20)
        root.add_widget(ChessClockWidget())
        #root.add_widget(content)
        self.add_back_button(root)
        self.add_widget(root)

class RFIDScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(RFIDScreen, self).__init__(**kwargs)
        #root = FloatLayout()
        root = BoxLayout(orientation='vertical', spacing=10, padding = 20)
        root.add_widget(NFCWidget())
        #root.add_widget(content)
        self.add_back_button(root)
        self.add_widget(root)

class HallEffectScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(HallEffectScreen, self).__init__(**kwargs)
        #root = FloatLayout()
        root = BoxLayout(orientation='vertical', spacing=10, padding = 20)
        root.add_widget(ChessBoardHallEffect())
        #root.add_widget(content)
        self.add_back_button(root)
        self.add_widget(root)

class FullApp(App):
    def build(self):
        sm = ScreenManager(transition=SlideTransition())
        sm.add_widget(MainMenuScreen(name="menu"))
        sm.add_widget(ChessGameScreen(name="chess"))
        sm.add_widget(GantryControlScreen(name="gantry"))
        sm.add_widget(ChessClockTesterScreen(name="clock"))
        sm.add_widget(RFIDScreen(name="rfid"))
        sm.add_widget(HallEffectScreen(name="halleffect"))
        return sm

if __name__ == '__main__':
    FullApp().run()
