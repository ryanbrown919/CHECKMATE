from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, NoTransition, WipeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.clock import Clock
from threading import Thread

# Import your custom widgets and screens
from scripts.gameplay import GameplayScreen
from scripts.gantryControl import GantryControlWidget, gantryControl
from scripts.customWidgets import HorizontalLine, VerticalLine, IconButton, RoundedButton, headerLayout

Window.fullscreen = True
FONT_SIZE = 40

class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super(MainMenuScreen, self).__init__(**kwargs)

        self.gantry_control = gantryControl()
        self.gantry_control.connect_to_grbl()

        # Create your main menu layout as before
        root_layout = BoxLayout(orientation='vertical', padding=10, spacing=0)
        header_layout = headerLayout()
        body_layout = BoxLayout(orientation='horizontal', padding=20, spacing=20)
        play_layout = BoxLayout(orientation='vertical', padding=20, spacing=20, size_hint=(0.9, 1))
        quickplay_layout = BoxLayout(orientation='horizontal', padding=20, spacing=20, size_hint=(1, 0.7))
        customplay_layout = BoxLayout(orientation='horizontal', padding=20, spacing=20, size_hint=(1, 0.3))
        option_layout = BoxLayout(orientation='vertical', padding=20, spacing=20, size_hint=(0.1, 1))

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

        # When "Play Game" is pressed, go to the loading screen
        custom1 = RoundedButton(text="Play Game", font_size=FONT_SIZE, size_hint=(1, 1))
        custom1.bind(on_release=lambda instance: self.change_screen("loading"))

        custom2 = RoundedButton(text="Control Gantry", font_size=FONT_SIZE, size_hint=(1, 1))
        custom2.bind(on_release=lambda instance: self.change_screen("gantry_control"))

        quickplay_layout.add_widget(custom1)
        quickplay_layout.add_widget(custom2)
        quickplay_layout.add_widget(RoundedButton(text="Set Game", size_hint=(1, 1), font_size=FONT_SIZE))
        quickplay_layout.add_widget(RoundedButton(text="Load Game", size_hint=(1, 1), font_size=FONT_SIZE))

        customplay_layout.add_widget(IconButton(source="assets/Play.png", size_hint=(None, None), size=(200, 200)))
        customplay_layout.add_widget(RoundedButton(text="Set Modes", size_hint=(0.7, 1), font_size=FONT_SIZE))

        option_layout.add_widget(IconButton(source="assets/user.png", 
                                            size_hint=(1, 0.3),
                                            allow_stretch=True,
                                            keep_ratio=True))
        option_layout.add_widget(IconButton(source="assets/settings.png", 
                                            size_hint=(1, 0.3),
                                            allow_stretch=True,
                                            keep_ratio=True))
        option_layout.add_widget(IconButton(source="assets/reset.png", 
                                            size_hint=(1, 0.3),
                                            allow_stretch=True,
                                            keep_ratio=True))
        
        self.add_widget(root_layout)

    def change_screen(self, screen_name):
        # For lazy loading, create and add screens on demand.
        if screen_name == "loading":
            # Remove any previous loading screen if it exists.
            if self.manager.has_screen("loading"):
                self.manager.remove_widget(self.manager.get_screen("loading"))
            loading_screen = LoadingScreen(name="loading", gantry_control=self.gantry_control)
            self.manager.add_widget(loading_screen)
            self.manager.transition.direction = 'right'
            self.manager.current = "loading"
        elif screen_name == "gantry_control":
            if self.manager.has_screen("gantry_control"):
                self.manager.remove_widget(self.manager.get_screen("gantry_control"))
            new_screen = GantryControlScreen(name="gantry_control", gantry_control=self.gantry_control)
            self.manager.add_widget(new_screen)
            self.manager.transition.direction = 'right'
            self.manager.current = "gantry_control"
        else:
            self.manager.transition.direction = 'right'
            self.manager.current = screen_name


class LoadingScreen(Screen):
    def __init__(self, gantry_control=None, **kwargs):
        super(LoadingScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        self.info_label = Label(text="Loading... Please wait.", font_size=FONT_SIZE)
        layout.add_widget(self.info_label)
        self.add_widget(layout)
        self.gantry_control=gantry_control

    def on_enter(self):
        # Start the heavy loading process on a separate thread so the UI stays responsive.
        Thread(target=self.load_game_background).start()

    def load_game_background(self):
        # Insert your background tasks here.
        # For demonstration, we'll simulate a heavy process with a sleep.
        import time
        time.sleep(3)  # Simulating background loading (replace with your actual tasks)

        # When done, schedule the finish on the main thread.
        Clock.schedule_once(self.finish_loading, 0)

    def finish_loading(self, dt):
        # Create a fresh ChessGameScreen instance and switch to it.
        if self.manager.has_screen("chess"):
            self.manager.remove_widget(self.manager.get_screen("chess"))
        new_game = ChessGameScreen(name="chess", gantry_control=self.gantry_control)
        self.manager.add_widget(new_game)
        self.manager.current = "chess"
        # Remove the loading screen.
        self.manager.remove_widget(self)


class BaseScreen(Screen):
    """
    Base class that adds a reusable "Back" button positioned at the top right.
    When leaving, the screen removes itself to force fresh initialization.
    """
    def add_back_button(self, parent_layout):
        back_btn = Button(text="Back", size_hint=(None, None), size=(100, 50),
                          font_size=FONT_SIZE * 0.75, pos_hint={'right': 1, 'top': 1})
        back_btn.bind(on_release=lambda instance: self.go_back())
        parent_layout.add_widget(back_btn)

    def go_back(self):
        self.manager.transition.direction = 'left'
        self.manager.current = "menu"
        self.manager.remove_widget(self)


class ChessGameScreen(BaseScreen):
    def __init__(self, gantry_control=None, **kwargs):
        super(ChessGameScreen, self).__init__(**kwargs)
        root = BoxLayout(orientation='vertical')
        self.gantry_control = gantry_control
        self.add_back_button(root)
        # Add your gameplay widget (loaded from scripts.gameplay) to fill the screen.
        root.add_widget(GameplayScreen(gantry_control=self.gantry_control))
        self.add_widget(root)


class GantryControlScreen(BaseScreen):
    def __init__(self, gantry_control, **kwargs):
        super(GantryControlScreen, self).__init__(**kwargs)
        self.gantry_control=gantry_control
        root = BoxLayout(orientation='vertical')
        root.add_widget(GantryControlWidget(gantry_control = self.gantry_control))
        self.add_back_button(root)
        self.add_widget(root)


class FullApp(App):
    def build(self):
        # Only add the main menu initially; other screens are added lazily.
        sm = ScreenManager(transition=WipeTransition())
        sm.add_widget(MainMenuScreen(name="menu"))
        return sm

if __name__ == '__main__':
    FullApp().run()




# from kivy.app import App
# from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, NoTransition, WipeTransition
# from kivy.uix.floatlayout import FloatLayout
# from kivy.uix.boxlayout import BoxLayout
# from kivy.uix.button import Button
# from kivy.uix.label import Label
# from kivy.uix.image import Image
# from kivy.uix.widget import Widget
# from kivy.uix.behaviors import ButtonBehavior
# from kivy.graphics import Color, RoundedRectangle

# from kivy.core.window import Window
# Window.fullscreen = True

# from scripts.gameplay import GameplayScreen
# #from gantryControl import GantryControlScreen
# from scripts.customWidgets import HorizontalLine, VerticalLine, IconButton, RoundedButton, headerLayout

# # Global font size for the whole application.
# FONT_SIZE = 40


# class MainMenuScreen(Screen):
#     def __init__(self, **kwargs):
#         super(MainMenuScreen, self).__init__(**kwargs)
#         # Root layout: Vertical BoxLayout to allow buttons on the top and icon on the bottom.
#         # Header layout: horizontal boxlayout for title and options.
#         # Body layout: horizontal boxlayout for gameplay buttons and side panel options.
#         # Play layout: vertical boxlayout split between quickplay and set game options.
#         root_layout = BoxLayout(orientation='vertical', padding=10, spacing=0)
#         header_layout = headerLayout()
#         body_layout = BoxLayout(orientation='horizontal', padding=20, spacing=20)
#         play_layout = BoxLayout(orientation='vertical', padding=20, spacing=20, size_hint=(0.9, 1))
#         quickplay_layout = BoxLayout(orientation='horizontal', padding=20, spacing=20, size_hint=(1, 0.7))
#         customplay_layout = BoxLayout(orientation='horizontal', padding=20, spacing=20, size_hint=(1, 0.3))
#         option_layout = BoxLayout(orientation='vertical', padding=20, spacing=20, size_hint=(0.1, 1))

#         root_layout.add_widget(header_layout)
#         root_layout.add_widget(HorizontalLine())
#         root_layout.add_widget(body_layout)
#         body_layout.add_widget(play_layout)
#         body_layout.add_widget(VerticalLine())
#         body_layout.add_widget(option_layout)
#         play_layout.add_widget(Label(text="Quickplay", font_size=50, size_hint=(0.2, 0.1), pos_hint={'left': 0}))
#         play_layout.add_widget(quickplay_layout)
#         play_layout.add_widget(HorizontalLine())
#         play_layout.add_widget(customplay_layout)

#         custom1 = RoundedButton(text="Play Game", font_size=FONT_SIZE, size_hint=(1, 1))
#         # When pressed, lazy-load the chess game screen.
#         custom1.bind(on_release=lambda instance: self.change_screen("chess"))

#         custom2 = RoundedButton(text="Control Gantry", font_size=FONT_SIZE, size_hint=(1, 1))
#         # Lazy-load the gantry control screen.
#         custom2.bind(on_release=lambda instance: self.change_screen("gantry_control"))

#         quickplay_layout.add_widget(custom1)
#         quickplay_layout.add_widget(custom2)
#         quickplay_layout.add_widget(RoundedButton(text="Set Game", size_hint=(1, 1), font_size=FONT_SIZE))
#         quickplay_layout.add_widget(RoundedButton(text="Load Game", size_hint=(1, 1), font_size=FONT_SIZE))

#         customplay_layout.add_widget(IconButton(source="assets/Play.png", size_hint=(None, None), size=(200, 200)))
#         customplay_layout.add_widget(RoundedButton(text="Set Modes", size_hint=(0.7, 1), font_size=FONT_SIZE))

#         option_layout.add_widget(IconButton(source="assets/user.png", 
#                                             size_hint=(1, 0.3),
#                                             allow_stretch=True,
#                                             keep_ratio=True))
#         option_layout.add_widget(IconButton(source="assets/settings.png", 
#                                             size_hint=(1, 0.3),
#                                             allow_stretch=True,
#                                             keep_ratio=True))
#         option_layout.add_widget(IconButton(source="assets/reset.png", 
#                                             size_hint=(1, 0.3),
#                                             allow_stretch=True,
#                                             keep_ratio=True))
        
#         self.add_widget(root_layout)

#     def change_screen(self, screen_name):
#         # Lazy-loading: remove the screen if it exists and create a new one.
#         if screen_name == "chess":
#             if self.manager.has_screen("chess"):
#                 self.manager.remove_widget(self.manager.get_screen("chess"))
#             new_screen = ChessGameScreen(name="chess")
#             self.manager.add_widget(new_screen)
#             self.manager.transition.direction = 'right'
#             self.manager.current = "chess"
#         elif screen_name == "gantry_control":
#             if self.manager.has_screen("gantry_control"):
#                 self.manager.remove_widget(self.manager.get_screen("gantry_control"))
#             new_screen = GantryControlScreen(name="gantry_control")
#             self.manager.add_widget(new_screen)
#             self.manager.transition.direction = 'right'
#             self.manager.current = "gantry_control"
#         else:
#             self.manager.transition.direction = 'right'
#             self.manager.current = screen_name


# class BaseScreen(Screen):
#     """
#     Base class that adds a reusable "Back" button positioned at the top right.
#     When leaving, the screen removes itself to allow fresh initialization next time.
#     """
#     def add_back_button(self, parent_layout):
#         back_btn = Button(text="Back", size_hint=(None, None), size=(100, 50),
#                           font_size=FONT_SIZE * 0.75, pos_hint={'right': 1, 'top': 1})
#         back_btn.bind(on_release=lambda instance: self.go_back())
#         parent_layout.add_widget(back_btn)

#     def go_back(self):
#         self.manager.transition.direction = 'left'
#         self.manager.current = "menu"
#         # Remove self to force lazy-loading the next time.
#         self.manager.remove_widget(self)


# class ChessGameScreen(BaseScreen):
#     def __init__(self, **kwargs):
#         super(ChessGameScreen, self).__init__(**kwargs)
#         # Create a layout with a back button and the gameplay area.
#         root = BoxLayout(orientation='vertical')
#         self.add_back_button(root)
#         # GameplayScreen is imported from scripts.gameplay; add it to fill the screen.
#         root.add_widget(GameplayScreen())
#         self.add_widget(root)


# class GantryControlScreen(BaseScreen):
#     def __init__(self, **kwargs):
#         super(GantryControlScreen, self).__init__(**kwargs)
#         root = BoxLayout(orientation='vertical')
#         # Placeholder for gantry control; replace with your actual widget.
#         root.add_widget(Label(text="Gantry Control Screen", font_size=FONT_SIZE))
#         self.add_back_button(root)
#         self.add_widget(root)


# class FullApp(App):
#     def build(self):
#         # Only add the main menu initially. Other screens will be added lazily.
#         sm = ScreenManager(transition=WipeTransition())
#         sm.add_widget(MainMenuScreen(name="menu"))
#         return sm

# if __name__ == '__main__':
#     FullApp().run()


# '''
# Main Menu 

# '''
# from kivy.app import App
# from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, NoTransition, WipeTransition
# from kivy.uix.floatlayout import FloatLayout
# from kivy.uix.boxlayout import BoxLayout
# from kivy.uix.button import Button
# from kivy.uix.label import Label
# from kivy.uix.image import Image
# from kivy.uix.widget import Widget
# from kivy.uix.behaviors import ButtonBehavior
# from kivy.graphics import Color, RoundedRectangle

# from kivy.core.window import Window
# Window.fullscreen = True



# from scripts.gameplay import GameplayScreen
# #from gantryControl import GantryControlScreen
# from scripts.customWidgets import HorizontalLine, VerticalLine, IconButton, RoundedButton, headerLayout




# # Global font size for the whole application.
# FONT_SIZE = 40


# class MainMenuScreen(Screen):
#     def __init__(self, **kwargs):
#         super(MainMenuScreen, self).__init__(**kwargs)
#         # Root layout: Vertical BoxLayout to allow buttons on the top and icon on the bottom.
#         # Header layout: horizontal boxlayout? between title and options
#         # Body layout: horizontal boxlayout? between buttons for gameplay and side_panel options
#         # Play layout: vertical boxlayout? split between quickplay and set game options

#         root_layout = BoxLayout(orientation='vertical', padding=10, spacing=0)
#         #header_layout = BoxLayout(orientation='horizontal', padding=10, spacing=0, size_hint=(1, 0.2))
#         header_layout = headerLayout()
#         body_layout = BoxLayout(orientation='horizontal', padding=20, spacing=20)
#         play_layout = BoxLayout(orientation='vertical', padding=20, spacing=20, size_hint=(0.9,1))
#         quickplay_layout = BoxLayout(orientation='horizontal', padding=20, spacing=20, size_hint=(1,0.7))
#         customplay_layout = BoxLayout(orientation='horizontal', padding=20, spacing=20, size_hint=(1,0.3))
#         option_layout = BoxLayout(orientation='vertical', padding=20, spacing=20, size_hint=(0.1,1))

#         root_layout.add_widget(header_layout)
#         root_layout.add_widget(HorizontalLine())
#         root_layout.add_widget(body_layout)
#         body_layout.add_widget(play_layout)
#         body_layout.add_widget(VerticalLine())
#         body_layout.add_widget(option_layout)
#         play_layout.add_widget(Label(text="Quickplay", font_size=50, size_hint=(0.2, 0.1), pos_hint={'left': 0}))
#         play_layout.add_widget(quickplay_layout)
#         play_layout.add_widget(HorizontalLine())
#         play_layout.add_widget(customplay_layout)

#         # header_layout.add_widget(Label(text="Check-M.A.T.E", font_size=120, size_hint=(0.4, 1)))
#         # header_layout.add_widget(Widget(size_hint_x=0.5))
#         # icon = Image(source='figures/logo.png', allow_stretch=True, keep_ratio=True, size_hint=(0.1, 1))
#         # header_layout.add_widget(icon)

        
#         custom1 = RoundedButton(text="Play Game", font_size=FONT_SIZE, size_hint=(1, 1))
#         custom1.bind(on_release=lambda instance: self.change_screen("chess"))

#         custom2 = RoundedButton(text="Control Gantry", font_size=FONT_SIZE, size_hint=(1, 1))
#         custom2.bind(on_release=lambda instance: self.change_screen("gantry_control"))

#         quickplay_layout.add_widget(custom1)
#         quickplay_layout.add_widget(custom2)
#         quickplay_layout.add_widget(RoundedButton(text="Set Game", size_hint=(1, 1), font_size=FONT_SIZE))
#         quickplay_layout.add_widget(RoundedButton(text="Load Game", size_hint=(1, 1), font_size=FONT_SIZE))

#         customplay_layout.add_widget(IconButton(source="assets/Play.png", size_hint=(None, None), size=(200, 200)))
#         customplay_layout.add_widget(RoundedButton(text="Set Modes", size_hint=(0.7, 1), font_size=FONT_SIZE))


#         option_layout.add_widget(IconButton(source="assets/user.png", 
#                                             size_hint=(1, 0.3),  # Disable relative sizing
#                                                        # Set explicit dimensions
#                                             allow_stretch=True,      # Allow the image to stretch to fill the widget
#                                             keep_ratio=True          # Maintain the image's aspect ratio
#                                             ))
#         option_layout.add_widget(IconButton(source="assets/settings.png", 
#                                             size_hint=(1, 0.3),  # Disable relative sizing
#                                                        # Set explicit dimensions
#                                             allow_stretch=True,      # Allow the image to stretch to fill the widget
#                                             keep_ratio=True          # Maintain the image's aspect ratio
#                                             ))
        
#         option_layout.add_widget(IconButton(source="assets/reset.png", 
#                                             size_hint=(1, 0.3),  # Disable relative sizing
#                                                        # Set explicit dimensions
#                                             allow_stretch=True,      # Allow the image to stretch to fill the widget
#                                             keep_ratio=True          # Maintain the image's aspect ratio
#                                             ))




        
        







#         self.add_widget(root_layout)

#     def change_screen(self, screen_name):
#         self.manager.transition.direction = 'right'
#         self.manager.current = screen_name

# class BaseScreen(Screen):
#     """
#     Base class that adds a reusable "Back" button positioned at the top right.
#     """
#     def add_back_button(self, parent_layout):
#         back_btn = Button(text="Back", size_hint=(None, None), size=(100, 50),
#                           font_size=FONT_SIZE * 0.75, pos_hint={'right': 1, 'top': 1})
#         back_btn.bind(on_release=lambda instance: self.go_back())
#         parent_layout.add_widget(back_btn)

#     def go_back(self):
#         self.manager.transition.direction = 'left'
#         self.manager.current = "menu"

# class ChessGameScreen(BaseScreen):
#     def __init__(self, **kwargs):
#         super(ChessGameScreen, self).__init__(**kwargs)
#         #root = FloatLayout()
#         root = BoxLayout(orientation='vertical')
#         root.add_widget(GameplayScreen())
#         #root.add_widget(content)
#         #self.add_back_button(root)
#         self.add_widget(root)

# class GantryControlScreen(BaseScreen):
#     def __init__(self, **kwargs):
#         super(GantryControlScreen, self).__init__(**kwargs)
#         root = BoxLayout(orientation='vertical')
#         root.add_widget(GantryControlScreen())
        
#         self.add_back_button(root)
#         self.add_widget(root)

# # class ChessClockTesterScreen(BaseScreen):
# #     def __init__(self, **kwargs):
# #         super(ChessClockTesterScreen, self).__init__(**kwargs)
# #         #root = FloatLayout()
# #         root = BoxLayout(orientation='vertical', spacing=10, padding = 20)
# #         root.add_widget(ChessClockWidget())
# #         #root.add_widget(content)
# #         self.add_back_button(root)
# #         self.add_widget(root)

# # class RFIDScreen(BaseScreen):
# #     def __init__(self, **kwargs):
# #         super(RFIDScreen, self).__init__(**kwargs)
# #         #root = FloatLayout()
# #         root = BoxLayout(orientation='vertical', spacing=10, padding = 20)
# #         root.add_widget(NFCWidget())
# #         #root.add_widget(content)
# #         self.add_back_button(root)
# #         self.add_widget(root)

# # class HallEffectScreen(BaseScreen):
# #     def __init__(self, **kwargs):
# #         super(HallEffectScreen, self).__init__(**kwargs)
# #         #root = FloatLayout()
# #         root = BoxLayout(orientation='vertical', spacing=10, padding = 20)
# #         root.add_widget(ChessBoardHallEffect())
# #         #root.add_widget(content)
# #         self.add_back_button(root)
# #         self.add_widget(root)

# class FullApp(App):
#     def build(self):
#         sm = ScreenManager(transition=WipeTransition())
#         sm.add_widget(MainMenuScreen(name="menu"))
#         sm.add_widget(ChessGameScreen(name="chess"))
#         sm.add_widget(GantryControlScreen(name="gantry_control"))
#         # sm.add_widget(ChessClockTesterScreen(name="clock"))
#         # sm.add_widget(RFIDScreen(name="rfid"))
#         # sm.add_widget(HallEffectScreen(name="halleffect"))
#         return sm

# if __name__ == '__main__':
#     FullApp().run()
