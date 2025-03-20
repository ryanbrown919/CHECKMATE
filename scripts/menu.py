'''
Main Menu 

'''
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, NoTransition, WipeTransition
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle

from kivy.core.window import Window
Window.fullscreen = True



from gameplay import GameplayScreen
from chessClock import ChessClockWidget 
#from gantryControl import GantryControlScreen
from rfidScanner import NFCWidget
from hallEffects import ChessBoardHallEffect
from customWidgets import HorizontalLine, VerticalLine, IconButton, RoundedButton, headerLayout




# Global font size for the whole application.
FONT_SIZE = 40


class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super(MainMenuScreen, self).__init__(**kwargs)
        # Root layout: Vertical BoxLayout to allow buttons on the top and icon on the bottom.
        # Header layout: horizontal boxlayout? between title and options
        # Body layout: horizontal boxlayout? between buttons for gameplay and side_panel options
        # Play layout: vertical boxlayout? split between quickplay and set game options

        root_layout = BoxLayout(orientation='vertical', padding=10, spacing=0)
        #header_layout = BoxLayout(orientation='horizontal', padding=10, spacing=0, size_hint=(1, 0.2))
        header_layout = headerLayout()
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

        # header_layout.add_widget(Label(text="Check-M.A.T.E", font_size=120, size_hint=(0.4, 1)))
        # header_layout.add_widget(Widget(size_hint_x=0.5))
        # icon = Image(source='figures/logo.png', allow_stretch=True, keep_ratio=True, size_hint=(0.1, 1))
        # header_layout.add_widget(icon)

        
        custom1 = RoundedButton(text="Run it back", font_size=FONT_SIZE, size_hint=(1, 1))
        custom1.bind(on_release=lambda instance: self.change_screen("chess"))

        quickplay_layout.add_widget(custom1)
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
        self.manager.transition.direction = 'right'
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
        self.manager.transition.direction = 'left'
        self.manager.current = "menu"

class ChessGameScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(ChessGameScreen, self).__init__(**kwargs)
        #root = FloatLayout()
        root = BoxLayout(orientation='vertical')
        root.add_widget(GameplayScreen())
        #root.add_widget(content)
        self.add_back_button(root)
        self.add_widget(root)

# class GantryControlScreen(BaseScreen):
#     def __init__(self, **kwargs):
#         super(GantryControlScreen, self).__init__(**kwargs)
#         #root = FloatLayout()
#         root = BoxLayout(orientation='vertical', spacing=10, padding = 20)
#         root.add_widget(GantryControlWidget())
        
#         self.add_back_button(root)
#         self.add_widget(root)

# class ChessClockTesterScreen(BaseScreen):
#     def __init__(self, **kwargs):
#         super(ChessClockTesterScreen, self).__init__(**kwargs)
#         #root = FloatLayout()
#         root = BoxLayout(orientation='vertical', spacing=10, padding = 20)
#         root.add_widget(ChessClockWidget())
#         #root.add_widget(content)
#         self.add_back_button(root)
#         self.add_widget(root)

# class RFIDScreen(BaseScreen):
#     def __init__(self, **kwargs):
#         super(RFIDScreen, self).__init__(**kwargs)
#         #root = FloatLayout()
#         root = BoxLayout(orientation='vertical', spacing=10, padding = 20)
#         root.add_widget(NFCWidget())
#         #root.add_widget(content)
#         self.add_back_button(root)
#         self.add_widget(root)

# class HallEffectScreen(BaseScreen):
#     def __init__(self, **kwargs):
#         super(HallEffectScreen, self).__init__(**kwargs)
#         #root = FloatLayout()
#         root = BoxLayout(orientation='vertical', spacing=10, padding = 20)
#         root.add_widget(ChessBoardHallEffect())
#         #root.add_widget(content)
#         self.add_back_button(root)
#         self.add_widget(root)

class FullApp(App):
    def build(self):
        sm = ScreenManager(transition=WipeTransition())
        sm.add_widget(MainMenuScreen(name="menu"))
        sm.add_widget(ChessGameScreen(name="chess"))
        # sm.add_widget(GantryControlScreen(name="gantry"))
        # sm.add_widget(ChessClockTesterScreen(name="clock"))
        # sm.add_widget(RFIDScreen(name="rfid"))
        # sm.add_widget(HallEffectScreen(name="halleffect"))
        return sm

if __name__ == '__main__':
    FullApp().run()
