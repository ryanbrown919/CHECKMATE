'''
Gameplay loop for playing a game of chess


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
from kivy.graphics import Color, Rectangle
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock

from kivy.core.window import Window

# --- Settings ---
Window.fullscreen = True


import chess

from chessBoard import ChessBoard, MaterialBar, MovesHistory, CapturedPieces
from chessClock import ChessClock
from lichess_test import ChessBackend
from customWidgets import HorizontalLine, VerticalLine, IconButton, headerLayout

class GameplayScreen(Screen):
    def __init__(self, **kwargs):
        super(GameplayScreen, self).__init__(**kwargs)

        self.clock = ChessClock()
        self.white_time = self.clock.player1_time
        self.black_time = self.clock.player2_time

        

        # General Structure of Gameplay Screen
        root_layout = BoxLayout(orientation='vertical', padding=10, spacing=0)

        # Vertical spacing widgets within root
        header_layout = headerLayout(menu=True)
        playarea_layout = BoxLayout(orientation='horizontal', spacing=20, size_hint=(1, 0.9))

        # Horizontal spacing widgets within playarea
        black_layout = BoxLayout(orientation='vertical', spacing=20, size_hint=(0.4, 1))
        middle_layout = BoxLayout(orientation='vertical', spacing=20, size_hint=(0.2, 1))
        white_layout = BoxLayout(orientation='vertical', spacing=20, size_hint=(0.4, 1))

        # Add widgets to root layout
        root_layout.add_widget(header_layout)
        root_layout.add_widget(HorizontalLine())
        root_layout.add_widget(playarea_layout)

        # Add widgets to playarea layout
        playarea_layout.add_widget(black_layout)
        playarea_layout.add_widget(VerticalLine())
        playarea_layout.add_widget(middle_layout)
        playarea_layout.add_widget(VerticalLine())
        playarea_layout.add_widget(white_layout)

        # Retrieve API key from file
        with open('venv/key.txt', 'r') as f:
            api_key = f.read().strip()  # .strip() removes any extra whitespace or newline characters

        def ui_callback(move):
            print("Received opponent move:", move)
            Clock.schedule_once(lambda dt: self.gameLogic_instance.notify_observers(), 0)

        # Start an instance of game logic, hard coded to bot play right now
        self.gameLogic_instance = ChessBackend(lichess_token=api_key, ui_move_callback=ui_callback, mode="offline",
                           engine_time_limit=0.1, difficulty_level=5)

        # Start a new game and start the backend thread
        #self.gameLogic_instance.start_game()
        self.gameLogic_instance.start()


    
        
        # Start a game against a bot immediately.
        # Adjust parameters (bot_username, level, clock settings) as needed.
    
        self.material_possesion = MaterialBar(size_hint=(1, 0.2), game_logic=self.gameLogic_instance)
        self.move_list = MovesHistory(size_hint=(1, 0.5), game_logic=self.gameLogic_instance)
        self.piece_jail = CapturedPieces(size_hint=(1, 0.3), game_logic=self.gameLogic_instance) 


        black_board = ChessBoard(touch_enabled_black=True, touch_enabled_white=False, bottom_colour_white=False, game_logic=self.gameLogic_instance, size_hint=(1, 1))
        white_board = ChessBoard(touch_enabled_black=False, touch_enabled_white=True, bottom_colour_white=True, game_logic=self.gameLogic_instance, size_hint=(1, 1))
        
        black_layout.add_widget(black_board)
        black_layout.add_widget(HorizontalLine())
        black_layout.add_widget(Label(text=self.clock.format_time(self.black_time), font_size=80, size_hint=(1, 0.2)))
        
        # Middle layout wdigets
        middle_layout.add_widget(Label(text="Material Possession", font_size=40, size_hint=(1, 0.1)))
        middle_layout.add_widget(self.material_possesion)
        #middle_layout.add_widget(HorizontalLine())
        middle_layout.add_widget(Label(text="Move History", font_size=40, size_hint=(1, 0.1)))
        middle_layout.add_widget(self.move_list)
        #middle_layout.add_widget(HorizontalLine())
        middle_layout.add_widget(Label(text="Piece Jail", font_size=40, size_hint=(1, 0.1)))
        middle_layout.add_widget(self.piece_jail)

        white_layout.add_widget(white_board)  
        white_layout.add_widget(HorizontalLine())
        white_layout.add_widget(Label(text=self.clock.format_time(self.white_time), font_size=80, size_hint=(1, 0.2)))
        



        
          
        

        self.add_widget(root_layout)



        self.gameLogic_instance.register_observer(self.on_move_update)

    def on_move_update(self, *args):
        # Update the chess board.
        self.gameLogic_instance.update_board()
        # Update material bar using a local calculation.
        #white, black = self.gameLogic_instance.calculate_material(self.gameLogic_instance.board)
        #self.gameLogic_instance.material_bar.update_percentages(black, white)
        # Update moves history and captured pieces if GameLogic holds that data.
        # if hasattr(self.gameLogic_instance, "move_history"):
        #     self.moves_history.update_moves()
        # if hasattr(self.gameLogic_instance, "captured_pieces"):
        #     self.captured_pieces.update_captured(self.gameLogic_instance.captured_pieces)





    def on_move_entered(self, instance):
        move_str = instance.text
        print("Move entered:", move_str)
        try:
            # Try to interpret the move as a UCI move
            move = chess.Move.from_uci(move_str)
            if move not in self.chess_board.game_board.legal_moves:
                # If the move is not legal in UCI format, try interpreting it as a SAN move
                move = self.chess_board.game_board.parse_san(move_str)
            
            instance.text = ""
        except ValueError:
            self.add_debug_message(f"Invalid move format: {move_str}")
            instance.text = ""

    def add_debug_message(self, message):
        """Add a debug message to the move list container."""
        label = Label(text=message, size_hint_y=None, height=40)
        self.move_list_container.add_widget(label)

    def update_ui(self, board, state):
        # This callback updates your chessboard UI with the new board state.
        # For instance, it might update the displayed FEN or re-render the board.
        print("UI Updated:")
        print(board)
        print("State:", state)
        self.move_list.add_move(state["move"])
        print("Captured piece:", state["captured_piece"])
        #self.add_captured_piece(state["captured_piece"])
        self.material_possesion.update_percentages(self.gameInstance_logic.calculate_material(self.gameLogic_instance.game_board))

    def change_screen(self, screen_name):
        self.manager.transition.direction = 'left'
        self.manager.current = screen_name

    def on_stop(self):
        # This method will be called from the App's on_stop to gracefully shutdown the backend thread.
        if self.gameLogic_instance.is_alive():
            print("Stopping ChessBackend thread...")
            self.gameLogic_instance.stop()
            self.gameLogic_instance.join()
            print("ChessBackend thread stopped.")

    def update_widgets(self, board, move_history, captured_pieces, move_uci, captured_piece):
        """
        Called by the backend whenever a move is made.
        Updates the moves history, captured pieces, and material bar.
        """
        self.moves_history.update_moves(move_history)
        self.captured_pieces.update_captured(captured_pieces)
        white_score, black_score = self.gameLogic_instance.calculate_material()
        self.material_bar.update_percentages(black_score, white_score)

    def update_material_bar(self, dt):
        white_score, black_score = self.gameLogic_instance.calculate_material()
        self.material_bar.update_percentages(black_score, white_score)

# class MovesHistory(ScrollView):
#     """
#     A scrollable view that displays past moves.
#     """
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.size_hint_y = 0.4
#         # Use a vertical BoxLayout to list moves.
#         self.layout = BoxLayout(orientation='vertical', size_hint_y=None)
#         self.layout.bind(minimum_height=self.layout.setter('height'))
#         self.add_widget(self.layout)

#     def add_move(self, move_text):
#         move_label = Label(text=move_text, size_hint_y=None, height=30)
#         self.layout.add_widget(move_label)
#         # Scroll to the bottom so the newest move is visible.
#         self.scroll_y = 0


# class CapturedPieces(BoxLayout):
#     """
#     A horizontal box that displays icons (or labels) of captured pieces.
#     """
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.size_hint_y = 0.1
#         self.orientation = 'horizontal'

#     def add_captured_piece(self, piece_symbol):
#         # For simplicity, we use a Label to represent the captured piece.
#         # In a real app, you might load an Image widget with an icon.
#         piece_label = Label(text=piece_symbol, size_hint=(None, None), size=(40, 40))
#         self.add_widget(piece_label)

# class MaterialBar(BoxLayout):
#     """
#     A custom widget that displays a horizontal bar.
#     The left portion (black) and right portion (white) reflect material percentages.
#     """
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.size_hint_y = 0.1
#         self.black_percentage = 50
#         self.white_percentage = 50
#         self.bind(pos=self.update_canvas, size=self.update_canvas)

#     def update_canvas(self, *args):
#         self.canvas.before.clear()
#         with self.canvas.before:
#             # Draw black portion on left
#             Color(0, 0, 0, 1)
#             black_width = self.width * self.black_percentage / 100.0
#             Rectangle(pos=self.pos, size=(black_width, self.height))
#             # Draw white portion on right
#             Color(1, 1, 1, 1)
#             Rectangle(pos=(self.x + black_width, self.y), size=(self.width - black_width, self.height))

#     def update_percentages(self, black_value, white_value):
#         total = black_value + white_value
#         if total > 0:
#             self.black_percentage = (black_value / total) * 100
#             self.white_percentage = (white_value / total) * 100
#         else:
#             self.black_percentage = 50
#             self.white_percentage = 50
#         self.update_canvas()
        


class FullApp(App):
    def build(self):

        self.chess_widget = GameplayScreen()
               
        return self.chess_widget
    
    def on_stop(self):
        # Ensure that the backend thread is stopped when the app exits.
        self.chess_widget.on_stop()

if __name__ == '__main__':
    FullApp().run()