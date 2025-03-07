import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.core.window import Window

from chessBoard_mar6 import ChessBoard

import threading
import time
import random
import berserk  # Python client for the Lichess API using Berserk

# ------------------------------------------------------------
# Lichess API Wrapper Using Berserk
# ------------------------------------------------------------
import berserk
class LichessBerserkAPI:
    """
    A modular wrapper for Lichess using the Berserk library.
    
    Methods provided:
      • challenge_ai(): Challenge the AI.
      • challenge_user(): Challenge a human opponent.
      • challenge(): Unified method to challenge (use opponent="ai" for the AI).
      • join_challenge(): Accept a challenge.
      • make_move(): Send a move to an active game. For correspondence games (the default for standard accounts),
                     since live move submission isn’t supported, the move is simulated.
      • stream_game(): Stream game events.
    
    Note: In this version, only parameters supported by Berserk are passed.
    """
    def __init__(self, api_key):
        self.api_key = api_key
        self.session = berserk.TokenSession(api_key)
        self.client = berserk.Client(session=self.session)
        self.game_id = None
        self.game_speed = None  # e.g. "correspondence" or "real-time"

    def challenge_ai(self, level=3, color="black"):
        """
        Challenge the AI. (For a standard account this typically creates a correspondence game.)
        """
        try:
            response = self.client.challenges.create_ai(level=level, color=color)
            # Look for the game id at the top level first:
            self.game_id = (response.get("id") or 
                            response.get("challenge", {}).get("id") or 
                            response.get("game", {}).get("id"))
            self.game_speed = response.get("speed", "unknown")
            return response
        except Exception as e:
            raise Exception(f"Error challenging AI: {e}")


    def challenge_user(self, username):
        """
        Challenge a human opponent by username.
        """
        try:
            response = self.client.challenges.create(username)
            self.game_id = (response.get("challenge", {}).get("id")
                            or response.get("game", {}).get("id"))
            self.game_speed = response.get("speed", "unknown")
            return response
        except Exception as e:
            raise Exception(f"Error challenging user '{username}': {e}")

    def challenge(self, opponent, **kwargs):
        """
        Unified method to challenge an opponent. 
        If opponent.lower() == "ai", it calls challenge_ai; otherwise, it calls challenge_user.
        """
        if opponent.lower() == "ai":
            return self.challenge_ai(**kwargs)
        else:
            return self.challenge_user(opponent)

    def join_challenge(self, challenge_id):
        """
        Accept a challenge by its challenge ID.
        """
        try:
            response = self.client.challenges.accept(challenge_id)
            self.game_id = (response.get("challenge", {}).get("id")
                            or response.get("game", {}).get("id"))
            self.game_speed = response.get("speed", "unknown")
            return response
        except Exception as e:
            raise Exception(f"Error joining challenge {challenge_id}: {e}")

    def make_move(self, game_id, move):
        """
        Send a move (in UCI format) to the game.
        
        For correspondence games (which standard accounts create when challenging the AI),
        the Lichess Board API for move submission isn’t available. In that case,
        this method simulates a move response.
        """
        if self.game_speed == "correspondence":
            # Simulate a successful move submission for correspondence games.
            print(f"Simulating move {move} in correspondence game {game_id}")
            return {"boardState": f"simulated_board_after_{move}"}
        try:
            DebugLog().log(f"Making move {move} in game {game_id}")
            ChessBoard.execute_move(move)
            result = self.client.board.make_move(game_id, move)
            return result
        except Exception as e:
            raise Exception(f"Error making move {move} in game {game_id}: {e}")

    def stream_game(self, game_id, callback):
        """
        Stream game events for a given game. The callback is invoked for each event.
        This call blocks and should be run in a separate thread.
        """
        try:
            for event in self.client.board.stream_game_state(game_id):
                callback(event)
        except Exception as e:
            callback({"error": f"Stream error: {e}"})

# ------------------------------------------------------------
# Debug Log Widget
# ------------------------------------------------------------
class DebugLog(ScrollView):
    """
    A ScrollView that contains a Label which wraps text.
    Logs messages to help you debug the app’s activity.
    """
    def __init__(self, **kwargs):
        super(DebugLog, self).__init__(**kwargs)
        self.log_label = Label(size_hint_y=None, markup=True)
        self.log_label.halign = 'left'
        self.log_label.valign = 'top'
        # Set text_size to enable wrapping
        self.bind(width=lambda inst, val: setattr(self.log_label, 'text_size', (val, None)))
        self.log_label.bind(texture_size=self.log_label.setter('size'))
        self.add_widget(self.log_label)
        self.log("Debug log initialized.")

    def log(self, message):
        current_text = self.log_label.text
        new_text = current_text + "\n" + message
        self.log_label.text = new_text
        Clock.schedule_once(lambda dt: setattr(self, 'scroll_y', 0))
# ------------------------------------------------------------
# ChessBoard Widget
# (This widget represents your chessboard.
#  We assume that your pre-developed chessboard can accept UCI moves.)
# For this example, we create a simple board that registers touches
# and converts two touches into a UCI move (e.g. "e2e4").
# ------------------------------------------------------------
# class ChessBoardWidget(Widget):
#     def __init__(self, **kwargs):
#         super(ChessBoardWidget, self).__init__(**kwargs)
#         self.rows = 8
#         self.cols = 8
#         self.selected_square = None  # will store (row, col)
#         self.bind(pos=self.draw_board, size=self.draw_board)
#         self.draw_board()

#     def draw_board(self, *args):
#         self.canvas.clear()
#         square_size = min(self.width, self.height) / 8.0
#         with self.canvas:
#             for row in range(self.rows):
#                 for col in range(self.cols):
#                     if (row + col) % 2 == 0:
#                         Color(1, 1, 1)
#                     else:
#                         Color(0.9, 0.9, 0.9)
#                     Rectangle(pos=(self.x + col * square_size, self.y + row * square_size),
#                               size=(square_size, square_size))
#             if self.selected_square is not None:
#                 Color(1, 0, 0, 0.5)
#                 row, col = self.selected_square
#                 Rectangle(pos=(self.x + col * square_size, self.y + row * square_size),
#                           size=(square_size, square_size))

#     def on_touch_down(self, touch):
#         if not self.collide_point(*touch.pos):
#             return False
#         square_size = min(self.width, self.height) / 8.0
#         col = int((touch.pos[0] - self.x) // square_size)
#         row = int((touch.pos[1] - self.y) // square_size)
#         notation = self.to_algebraic((row, col))
#         self.parent.debug_log.log(f"Square touched: {notation}")
#         if self.selected_square is None:
#             self.selected_square = (row, col)
#             self.draw_board()
#         else:
#             start = self.to_algebraic(self.selected_square)
#             end = self.to_algebraic((row, col))
#             move = start + end  # e.g. "e2e4"
#             self.parent.debug_log.log(f"Player move: {move}")
#             self.parent.handle_player_move(move)
#             self.selected_square = None
#             self.draw_board()
#         return True

#     def to_algebraic(self, square):
#         row, col = square
#         return chr(ord('a') + col) + str(row + 1)

# ------------------------------------------------------------
# Main Layout: Chessboard on left, Debug Log on right.
# ------------------------------------------------------------
class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super(MainLayout, self).__init__(**kwargs)
        self.orientation = 'horizontal'
        # Chessboard takes 70% of width.

        panel_width = 100  # width (in pixels) for left (captured pieces) and right (move list) panels
        screen_width = 1920
        screen_height = 1080

        # The board size will be the maximum square that fits in the central area.
        board_size = min(screen_height, screen_width - 2 * panel_width)
        self.square_size = board_size / 8

        # Center the board in the area between the panels, leaving space for labels.
        board_origin_x = panel_width + ((screen_width - 2 * panel_width - board_size) / 2) - self.square_size
        board_origin_y = ((screen_height - board_size) / 2) + self.square_size
        board_origin = (board_origin_x, board_origin_y)
        self.chess_board = ChessBoard(board_origin=board_origin, board_size=board_size)

        self.add_widget(self.chess_board)
        # Debug log takes 30% of width.
        self.debug_log = DebugLog(size_hint=(0.4, 1))
        self.add_widget(self.debug_log)

        # # Load API key from file
        try:
            with open('venv/key.txt', 'r') as f:
                self.api_key = f.read().strip()
            self.debug_log.log("API key loaded successfully.")
        except Exception as e:
            self.debug_log.log(f"Error loading API key: {e}")
            self.api_key = None

        # Initialize Lichess API (real API calls)
        self.api = LichessBerserkAPI(self.api_key)

        # Start a game against the AI in a separate thread (to avoid blocking the UI)
        threading.Thread(target=self.start_game_against_ai, daemon=True).start()


    def start_game_against_ai(self):
        """
        Call the Lichess API to challenge the AI.
        When the game starts, store the game id and start listening for game events.
        """
        self.debug_log.log("Challenging the AI...")
        try:
            game_data = self.api.challenge_ai(level=3, color="random")
            self.game_id = self.api.game_id
            self.debug_log.log(f"Game started! Game ID: {self.game_id}")
            # (You might want to update your chessboard state based on game_data["boardState"])
            # Now start the stream to listen for bot moves.
            threading.Thread(target=self.api.stream_game, args=(self.game_id, self.on_game_event), daemon=True).start()
        except Exception as e:
            self.debug_log.log(f"Error starting game: {e}")

    def handle_player_move(self, move):
        """
        When the user makes a move on the chessboard,
        send it to Lichess and log the response.
        """
        self.debug_log.log(f"Sending move {move} to Lichess...")
        try:
            response = self.api.make_move(self.game_id, move)
            new_state = response.get("boardState", "unknown")
            self.debug_log.log(f"Move accepted. New board state: {new_state}")
            # Here, call your existing chessboard engine to update the displayed board using UCI moves.
            # For example: self.chessboard.apply_move(move)
        except Exception as e:
            self.debug_log.log(f"Error sending move: {e}")

    def on_game_event(self, event_data):
        """
        This callback is invoked by the streaming thread when Lichess sends a game event.
        We schedule the UI update on the main thread.
        """
        if "error" in event_data:
            Clock.schedule_once(lambda dt: self.debug_log.log(f"Stream error: {event_data['error']}"))
        else:
            event_type = event_data.get("type", "")
            if event_type in ["gameState", "gameFull"]:
                board_state = event_data.get("boardState", "unknown")
                last_move = event_data.get("lastMove", "none")
                message = f"Bot moved {last_move}. New board state: {board_state}"
                Clock.schedule_once(lambda dt: self.debug_log.log(message))
                # Also, update your local chessboard with the bot move if needed.
            else:
                Clock.schedule_once(lambda dt: self.debug_log.log(f"Received event: {event_data}"))

# ------------------------------------------------------------
# Main Kivy App
# ------------------------------------------------------------
class ChessApp(App):
    def build(self):
        Window.fullscreen = True
        return MainLayout()

if __name__ == '__main__':
    ChessApp().run()
