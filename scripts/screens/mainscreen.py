from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, NoTransition, WipeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.slider import Slider
from kivy.uix.togglebutton import ToggleButton
from kivy.core.window import Window
from kivy.clock import Clock
from threading import Thread
import random
# from kivy.metrics import dp

# Import your custom widgets and screens
try:
    from scripts.screens.custom_widgets import HorizontalLine, VerticalLine, IconButton, headerLayout, RoundedButton

except:
    from custom_widgets import HorizontalLine, VerticalLine, IconButton, RoundedButton, headerLayout

Window.fullscreen = True
FONT_SIZE = 32

class MainScreen(Screen):
    def __init__(self, control_system, **kwargs):
        super(MainScreen, self).__init__(**kwargs)

        self.control_system = control_system

        self.padding = 0
        self.spacing = 0

        # self.gantry_control = gantryControl()
        # self.gantry_control.connect_to_grbl()
        # self.preferred_color = 'White'
        # self.chess_elo = 1500

        # Create your main menu layout as before
        root_layout = BoxLayout(orientation='vertical', padding=10, spacing=0)
        header_layout = headerLayout()
        body_layout = BoxLayout(orientation='horizontal', padding=0, spacing=20)
        play_layout = BoxLayout(orientation='vertical', padding=0, spacing=20, size_hint=(0.9, 1))
        quickplay_layout = BoxLayout(orientation='horizontal', padding=0, spacing=20, size_hint=(1, 0.7))
        customplay_layout = BoxLayout(orientation='horizontal', padding=0, spacing=20, size_hint=(1, 0.3))
        option_layout = BoxLayout(orientation='vertical', padding=0, spacing=20, size_hint=(0.1, 1))

        root_layout.add_widget(header_layout)
        root_layout.add_widget(HorizontalLine())
        root_layout.add_widget(body_layout)
        body_layout.add_widget(play_layout)
        body_layout.add_widget(VerticalLine())
        body_layout.add_widget(option_layout)
        play_layout.add_widget(Label(text="Quickplay", font_size=32, size_hint=(0.2, 0.1), pos_hint={'left': 0}))
        play_layout.add_widget(quickplay_layout)
        play_layout.add_widget(HorizontalLine())
        play_layout.add_widget(customplay_layout)

        # When "Play Game" is pressed, go to the loading screen
        custom1 = RoundedButton(text="[size=30][b]Play Engine[/b][/size]\n[size=25]Color: White\nElo: 1500[/size]", markup=True, font_size=FONT_SIZE, size_hint=(1, 1))        
        custom1.bind(on_release=lambda instance: self.start_custom1())

        custom2 = RoundedButton(text="[size=30][b]Play Online?[/b][/size]\n[size=25]Color: White\nElo: 1500[/size]", markup=True, font_size=FONT_SIZE, size_hint=(1, 1))        
        custom2.bind(on_release=lambda instance: self.start_custom2())

        custom3 = RoundedButton(text="[size=30][b]Bot V Bot[/b][/size]\n[size=25]\nElo: 1500[/size]", markup=True, font_size=FONT_SIZE, size_hint=(1, 1))        
        custom3.bind(on_release=lambda instance: self.start_custom3())

        custom4 = RoundedButton(text="[size=30][b]Challenge Mode[/b][/size]\n[size=25]Color: White\nElo: 3000[/size]", markup=True, font_size=FONT_SIZE, size_hint=(1, 1))        
        custom4.bind(on_release=lambda instance: self.start_custom4())


        quickplay_layout.add_widget(custom1)
        quickplay_layout.add_widget(custom2)
        quickplay_layout.add_widget(custom3)
        quickplay_layout.add_widget(custom4)


        play_btn = IconButton(source="assets/Play.png", size_hint=(0.3, 1))
        play_btn.bind(on_release=lambda instance: self.start_custom_game())
        customplay_layout.add_widget(play_btn)


        set_modes_button = RoundedButton(text="Set Modes", size_hint=(0.7, 1), font_size=FONT_SIZE)
        set_modes_button.bind(on_release=self.open_mode_popup)
        customplay_layout.add_widget(set_modes_button)

        user_btn = IconButton(source="assets/User.png", 
                                            size_hint=(1, 0.3),
                                            allow_stretch=True,
                                            keep_ratio=True)
        
        settings_btn = (IconButton(source="assets/settings.png", 
                                            size_hint=(1, 0.3),
                                            allow_stretch=True,
                                            keep_ratio=True))
        reset_btn = (IconButton(source="assets/reset.png", 
                                            size_hint=(1, 0.3),
                                            allow_stretch=True,
                                            keep_ratio=True))
        reset_btn.bind(on_release=lambda instance: self.control_system.go_to_boardreset())
        gantry_btn = IconButton(source="assets/Power.png", 
                                            size_hint=(1, 0.3),
                                            allow_stretch=True,
                                            keep_ratio=True)
        gantry_btn.bind(on_release=lambda instance: self.control_system.go_to_gantry())
        

        option_layout.add_widget(user_btn)
        option_layout.add_widget(settings_btn)
        option_layout.add_widget(reset_btn)
        option_layout.add_widget(gantry_btn)
        

        self.add_widget(root_layout)

    def start_custom_game(self):
        #Start game from bottom bar

        self.control_parameters = {'online': False, 'colour': self.preferred_color, 'elo': self.chess_elo, 'timer': False, 'engine_time_limit': 0.1, 'bot_mode': False, 'local_mode': False}  # Default parameters to be set by the user 

        self.control_system.start_game()

    # def change_screen(self, screen_name):
    #     # For lazy loading, create and add screens on demand.
    #     if screen_name == "loading":
    #         # Remove any previous loading screen if it exists.
    #         if self.manager.has_screen("loading"):
    #             self.manager.remove_widget(self.manager.get_screen("loading"))
    #         loading_screen = LoadingScreen(name="loading", gantry_control=self.gantry_control, preferred_color=self.preferred_color, elo=self.chess_elo)
    #         self.manager.add_widget(loading_screen)
    #         self.manager.transition.direction = 'right'
    #         self.manager.current = "loading"
    #     elif screen_name == "gantry_control":
    #         if self.manager.has_screen("gantry_control"):
    #             self.manager.remove_widget(self.manager.get_screen("gantry_control"))
    #         new_screen = GantryControlScreen(name="gantry_control", gantry_control=self.gantry_control)
    #         self.manager.add_widget(new_screen)
    #         self.manager.transition.direction = 'right'
    #         self.manager.current = "gantry_control"
    #     else:
    #         self.manager.transition.direction = 'right'
    #         self.manager.current = screen_name

    def open_mode_popup(self, instance):
        popup = ModePopup(current_color=getattr(self, "preferred_color", "Random"),
                        current_elo=getattr(self, "chess_elo", 1500))
        # When the user confirms, update the main menu’s stored values.
        popup.on_mode_selected = self.on_mode_selected
        popup.open()

    def on_mode_selected(self, color, elo):
        self.preferred_color = color
        self.chess_elo = elo
        print(f"Selected mode: {color}, ELO: {elo}")

        if color == 'Bot V Bot':
            self.bot_mode=True
            self.preferred_color == 'white'
        elif color == 'Random':
            self.preferred_color = random.choice('white', 'black')
            self.bot_mode = False
        else:
            self.bot_mode = False


    def start_custom1(self):

        self.control_system.parameters = {'online': False, 'colour': "white", 'elo': 1500, 'timer': False, 'engine_time_limit': 0.1, 'bot_mode': False, 'local_mode': False}  # Default parameters to be set by the user 
        self.control_system.start_game()
    
    def start_custom2(self):
        #self.parameters = {'online': True, 'colour': "white", 'elo': 1500, 'timer': False, 'engine_time_limit': 0.1, 'bot_mode': False}  # Default parameters to be set by the user 
        # If time
        pass
    def start_custom3(self):
        self.control_system.parameters = {'online': False, 'colour': "white", 'elo': 1500, 'timer': False, 'engine_time_limit': 0.1, 'bot_mode': True, 'local_mode': False}  # Default parameters to be set by the user 
        self.control_system.start_game()

    def start_custom4(self):
        self.control_system.parameters = {'online': False, 'colour': "white", 'elo': 3000, 'timer': False, 'engine_time_limit': 0.1, 'bot_mode': False, 'local_mode': False}  # Default parameters to be set by the user 
        self.control_system.start_game()


# class LoadingScreen(Screen):
#     def __init__(self, gantry_control=None, elo=None, preferred_color=None, **kwargs):
#         super(LoadingScreen, self).__init__(**kwargs)
#         layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
#         self.info_label = Label(text="Loading... Please wait.", font_size=FONT_SIZE)
#         layout.add_widget(self.info_label)
#         self.add_widget(layout)
#         self.gantry_control = gantry_control
#         self.elo = elo
#         self.preferred_color=preferred_color

#     def on_enter(self):
#         # Start the heavy loading process on a separate thread so the UI stays responsive.
#         Thread(target=self.load_game_background).start()

#     def load_game_background(self):
#         # Insert your background tasks here.
#         # For demonstration, we'll simulate a heavy process with a sleep.
#         import time
#         time.sleep(3)  # Simulating background loading (replace with your actual tasks)

#         # When done, schedule the finish on the main thread.
#         Clock.schedule_once(self.finish_loading, 0)

#     def finish_loading(self, dt):
#         # Create a fresh ChessGameScreen instance and switch to it.
#         if self.manager.has_screen("chess"):
#             self.manager.remove_widget(self.manager.get_screen("chess"))
#         new_game = ChessGameScreen(name="chess", gantry_control=self.gantry_control, elo=self.elo, preferred_color=self.preferred_color)
#         self.manager.add_widget(new_game)
#         self.manager.current = "chess"
#         # Remove the loading screen.
#         self.manager.remove_widget(self)


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


# class ChessGameScreen(BaseScreen):
#     def __init__(self, gantry_control=None, preferred_color=None, elo=None, **kwargs):
#         super(ChessGameScreen, self).__init__(**kwargs)
#         self.preferred_color=preferred_color
#         self.elo=elo
#         root = BoxLayout(orientation='vertical')
#         self.gantry_control = gantry_control
#         self.add_back_button(root)
#         # Add your gameplay widget (loaded from scripts.gameplay) to fill the screen.
#         root.add_widget(GameplayScreen(gantry_control=self.gantry_control, preferred_color=self.preferred_color, elo=self.elo))
#         self.add_widget(root)


# class GantryControlScreen(BaseScreen):
#     def __init__(self, gantry_control, **kwargs):
#         super(GantryControlScreen, self).__init__(**kwargs)
#         self.gantry_control=gantry_control
#         root = BoxLayout(orientation='vertical')
#         root.add_widget(GantryControlWidget(gantry_control = self.gantry_control))
#         self.add_back_button(root)
#         self.add_widget(root)


class ModePopup(Popup):
    def __init__(self, current_color="Random", current_elo=1500, **kwargs):
        super(ModePopup, self).__init__(**kwargs)
        self.title = "Select Mode"
        self.size_hint = (0.8, 0.5)
        self.auto_dismiss = False

        self.selected_color = current_color
        self.selected_elo = current_elo

        layout = BoxLayout(orientation="vertical", spacing=10, padding=10)

        # Color selection section
        color_layout = BoxLayout(orientation="horizontal", spacing=10)
        color_layout.add_widget(Label(text="Preferred Color:", size_hint=(0.4, 1)))
        self.white_btn = ToggleButton(text="White", group="color", allow_no_selection=False)
        self.black_btn = ToggleButton(text="Black", group="color", allow_no_selection=False)
        self.random_btn = ToggleButton(text="Random", group="color", allow_no_selection=False)
        self.botvbot_btn = ToggleButton(text="Bot V Bot", group="color", allow_no_selection=False)

        
        # Set initial selection
        if current_color == "White":
            self.white_btn.state = "down"
        elif current_color == "Black":
            self.black_btn.state = "down"
        elif current_color == 'Random':
            self.random_btn.state = "down"
        else:
            self.botvbot_btn.state = "down"

        # Bind selection to update current value
        self.white_btn.bind(on_press=self.on_color_selected)
        self.black_btn.bind(on_press=self.on_color_selected)
        self.random_btn.bind(on_press=self.on_color_selected)
        self.botvbot_btn.bind(on_press=self.on_color_selected)

        
        color_layout.add_widget(self.white_btn)
        color_layout.add_widget(self.black_btn)
        color_layout.add_widget(self.random_btn)
        color_layout.add_widget(self.botvbot_btn)
        layout.add_widget(color_layout)

        # ELO selection section
        elo_layout = BoxLayout(orientation="vertical", spacing=10)
        elo_layout.add_widget(Label(text="Engine ELO Rating:", size_hint=(1, 0.3)))
        self.elo_slider = Slider(min=1320, max=2800, value=current_elo, step=50, size_hint=(1, 0.3))
        elo_layout.add_widget(self.elo_slider)
        self.elo_label = Label(text=f"ELO: {int(self.elo_slider.value)}", size_hint=(1, 0.3))
        elo_layout.add_widget(self.elo_label)
        self.elo_slider.bind(value=self.on_elo_changed)
        layout.add_widget(elo_layout)

        # OK and Cancel buttons
        button_layout = BoxLayout(orientation="horizontal", spacing=10, size_hint=(1, 0.3))
        ok_button = Button(text="OK")
        cancel_button = Button(text="Cancel")
        ok_button.bind(on_release=self.on_ok)
        cancel_button.bind(on_release=self.on_cancel)
        button_layout.add_widget(ok_button)
        button_layout.add_widget(cancel_button)
        layout.add_widget(button_layout)
        
        self.content = layout

    def on_color_selected(self, instance):
        self.selected_color = instance.text

    def on_elo_changed(self, instance, value):
        self.selected_elo = int(value)
        self.elo_label.text = f"ELO: {self.selected_elo}"

    def on_ok(self, instance):
        # Call a callback if defined, passing the selected values
        if hasattr(self, "on_mode_selected"):
            self.on_mode_selected(self.selected_color, self.selected_elo)
        self.dismiss()

    def on_cancel(self, instance):
        self.dismiss()


class FullApp(App):
    def build(self):
        # Only add the main menu initially; other screens are added lazily.
        sm = ScreenManager(transition=NoTransition())
        sm.add_widget(MainScreen(name="menu"))
        return sm


