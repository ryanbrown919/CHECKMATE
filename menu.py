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
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle



from chessBoard_test import ChessGameWidget
from chessClock import ChessClockWidget 
from gantryControl import GantryControlScreen
from rfidScanner import NFCWidget
from hallEffects import ChessBoardHallEffect

from kivy.lang import Builder

kv="""
<RoundedButton@Button>:
    background_color: 0,0,0,0  # the last zero is the critical on, make invisible
    canvas.before:
        Color:
            rgba: (.4,.4,.4,1) if self.state=='normal' else (0,.7,.7,1)  # visual feedback of press
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [25,]
"""
class RoundedButton(Button):
    pass

Builder.load_string(kv)


class IconButton(ButtonBehavior, Image):
    pass

class RoundedButton2(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Disable the default background images
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0.2, 0.2, 0.2, 1)
        with self.canvas.before:
            self.bg_color = Color(rgba=self.background_color)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[(40, 40), (40, 40), (20, 20), (20, 20)])
        self.bind(pos=self.update_rect, size=self.update_rect, background_color=self.update_color)
        

    def update_rect(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def update_color(self, *args):
        self.bg_color.rgba = self.background_color


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

class VerticalLine(Widget):
    def __init__(self, **kwargs):
        super(VerticalLine, self).__init__(**kwargs)
        # Disable automatic sizing on the y-axis and set a fixed height (e.g., 2 pixels)
        self.size_hint_x = None
        self.width = 2
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
        body_layout.add_widget(VerticalLine())
        body_layout.add_widget(option_layout)
        play_layout.add_widget(Label(text="Quickplay", font_size=50, size_hint=(0.2, 0.1), pos_hint={'left': 0}))
        play_layout.add_widget(quickplay_layout)
        play_layout.add_widget(HorizontalLine())
        play_layout.add_widget(customplay_layout)

        header_layout.add_widget(Label(text="Check-M.A.T.E", font_size=120, size_hint=(0.4, 1)))
        header_layout.add_widget(Widget(size_hint_x=0.5))
        icon = Image(source='figures/logo.png', allow_stretch=True, keep_ratio=True, size_hint=(0.1, 1))
        header_layout.add_widget(icon)

        

        quickplay_layout.add_widget(RoundedButton(text="Quickplay", font_size=FONT_SIZE, size_hint=(1, 1)))
        quickplay_layout.add_widget(RoundedButton(text="Quick Play", size_hint=(1, 1), font_size=FONT_SIZE))
        quickplay_layout.add_widget(RoundedButton(text="Set Game", size_hint=(1, 1), font_size=FONT_SIZE))
        quickplay_layout.add_widget(RoundedButton(text="Load Game", size_hint=(1, 1), font_size=FONT_SIZE))

        customplay_layout.add_widget(IconButton(source="figures/Play.png", size_hint=(None, None), size=(200, 200)))
        customplay_layout.add_widget(RoundedButton(text="Set Modes", size_hint=(0.7, 1), font_size=FONT_SIZE))


        option_layout.add_widget(IconButton(source="figures/user.png", 
                                            size_hint=(1, 0.3),  # Disable relative sizing
                                                       # Set explicit dimensions
                                            allow_stretch=True,      # Allow the image to stretch to fill the widget
                                            keep_ratio=True          # Maintain the image's aspect ratio
                                            ))
        option_layout.add_widget(IconButton(source="figures/settings.png", 
                                            size_hint=(1, 0.3),  # Disable relative sizing
                                                       # Set explicit dimensions
                                            allow_stretch=True,      # Allow the image to stretch to fill the widget
                                            keep_ratio=True          # Maintain the image's aspect ratio
                                            ))
        
        option_layout.add_widget(IconButton(source="figures/reset.png", 
                                            size_hint=(1, 0.3),  # Disable relative sizing
                                                       # Set explicit dimensions
                                            allow_stretch=True,      # Allow the image to stretch to fill the widget
                                            keep_ratio=True          # Maintain the image's aspect ratio
                                            ))




        
        







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
