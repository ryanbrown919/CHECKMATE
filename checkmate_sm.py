from kivy.config import Config

# Set full screen mode and hide cursor globally
Config.set('graphics', 'fullscreen', '1')
Config.set('graphics', 'show_cursor', '0')



from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, NoTransition, WipeTransition, FadeTransition
from kivy.clock import Clock

from scripts.controls.control_system import ChessControlSystem

from scripts.screens.gamescreen import GameScreen
from scripts.screens.initscreen import InitScreen
from scripts.screens.loadingscreen import LoadingScreen
from scripts.screens.mainscreen import MainScreen
from scripts.screens.gantryscreen import GantryControlScreen
from scripts.screens.endgamescreen import EndGameScreen
from scripts.screens.demoscreen import DemoScreen

# A simple ScreenManager that holds our GameScreen.
class MainScreenManager(ScreenManager):
    pass

# --------------------------
# Kivy App Integration
# --------------------------
class TestApp(App):
    def build(self):
        # Create an instance of our state machine.
        self.control_system = ChessControlSystem(ui_update_callback=self.on_state_change)
        # Set engine parameters at runtime.
        self.control_system.parameters["engine_time_limit"] = 0.1
        self.control_system.parameters["elo"] = 1400
        self.control_system.parameters["bot_mode"] = True  # Set to True for engine vs. engine.

        self.sm = MainScreenManager(transition=FadeTransition())
        gamescreen = GameScreen(control_system=self.control_system, name="gamescreen")
        initscreen = InitScreen(control_system=self.control_system, name='initscreen')
        loadingscreen = LoadingScreen(control_system=self.control_system, name='loadingscreen')
        mainscreen = MainScreen(control_system=self.control_system, name='mainscreen')
        gantryscreen = GantryControlScreen(control_system=self.control_system, name="gantryscreen")
        endgamescreen = EndGameScreen(control_system=self.control_system, name="endgamescreen")
        demoscreen = DemoScreen(control_system = self.control_system, name='demoscreen')


        self.sm.add_widget(gamescreen)
        self.sm.add_widget(initscreen)
        self.sm.add_widget(loadingscreen)
        self.sm.add_widget(mainscreen)
        self.sm.add_widget(gantryscreen)
        self.sm.add_widget(endgamescreen)



        # Start in main menu.
        self.sm.current = 'initscreen'

        # Simulate UI flow.
        Clock.schedule_once(lambda dt: self.control_system.finish_loading(), 10)
        #Clock.schedule_once(lambda dt: self.control_system.finish_init(), 2)
        #Clock.schedule_once(lambda dt: self.control_system.start_game(), 10)

        return self.sm
    
    def on_state_change(self, state):
        print(f"[App] State changed: {state}")
        # Schedule the screen update on the main thread.
        Clock.schedule_once(lambda dt: self.update_screen(state))
    
    def update_screen(self, state):
        """
        This callback is called whenever the state machine updates.
        We map state machine states to screen names:
          - If state is 'mainscreen', show the main menu.
          - If state starts with 'gamescreen', show the game screen.
        """
        if state == 'mainscreen':
            self.sm.current = 'mainscreen'
        elif state.startswith('gamescreen'):
            self.trigger_game_screen_update(self.control_system)
            # self.sm.current = 'gamescreen'
        elif state == 'gantryscreen':
            self.sm.current = 'gantryscreen'
        elif state == 'endgamescreen':
            self.sm.current = 'endgamescreen'
        elif state == 'loadingscreen':
            self.sm.current = 'endgamescreen'
        elif state == 'demoscreen':
            self.sm.current = 'demoscreen'

        else:
            print("[App] Unhandled state:", state)

    def trigger_game_screen_update(self, control_system):
        # Assume 'game' is the name of your GameScreen in the ScreenManager.
        # Switch to the game screen first.
        self.sm.current = 'gamescreen'
        # Get the game screen instance.
        game_screen = self.sm.get_screen('gamescreen')
        # Schedule the layout rebuild with a short delay.
        Clock.schedule_once(lambda dt: game_screen.rebuild_layout(), 0.1)


if __name__ == '__main__':
    TestApp().run()
