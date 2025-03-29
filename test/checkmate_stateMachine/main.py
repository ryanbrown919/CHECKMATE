# main.py
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from backend_scripts.control_system import ChessControlSystem
from test.checkmate_stateMachine.frontend_scripts.initscreen import InitScreen
from test.checkmate_stateMachine.backend_scripts.main_screen import MainMenuScreen
from test.checkmate_stateMachine.frontend_scripts.gamescreen import GameScreen
from test.checkmate_stateMachine.frontend_scripts.gantryscreen import GantryControlScreen
from frontend_scripts.settings_screen import SettingsScreen

class ChessApp(App):
    def build(self):
        self.control_system = ChessControlSystem()
        sm = ScreenManager(transition=FadeTransition())

        # Create and add screens
        sm.add_widget(InitScreen(self.control_system, name='init'))
        sm.add_widget(MainMenuScreen(self.control_system, name='main_menu'))
        sm.add_widget(GameScreen(self.control_system, name='game'))
        sm.add_widget(GantryControlScreen(self.control_system, name='manual'))
        sm.add_widget(SettingsScreen(self.control_system, name='settings'))

        # Start with a desired screen
        sm.current = 'init'
        return sm

if __name__ == '__main__':
    ChessApp().run()