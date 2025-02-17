import kivy
kivy.require('2.0.0')

# Kivy imports for the UI
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.core.window import Window

# Standard libraries for threading and simulation
import threading
import time
import random

from chessBoard import ChessBoard

# ------------------------------------------------------------
# Simulated Lichess API Class
# ------------------------------------------------------------
class LichessAPI:
    """
    This is a dummy implementation of a Lichess API wrapper.
    In practice, you would use real HTTP/WebSocket calls to Lichess's API.
    """
    def __init__(self, api_token):
        with open('venv/key.txt', 'r') as f:
            api_key = f.read().strip()  # .strip() removes any extra whitespace or newline characters

        self.api_token =  api_key
        self.game_id = None
        print("LichessAPI initialized with token:", self.api_token)

    def start_game(self, opponent_id=None, variant='standard', rated=False, time_control={'limit':300, 'increment':10}):
        """
        Simulate creating a new game against a bot.
        In the real implementation, you'd POST to the /challenge/open endpoint.
        """
        print("Starting game against bot...")
        time.sleep(1)  # Simulate network delay
        # Generate a fake game id
        self.game_id = f"game_{random.randint(1000, 9999)}"
        # Return a simulated game data object
        game_data = {
            "id": self.game_id,
            "challengeUrl": f"https://lichess.org/{self.game_id}?color=white",
            "boardState": self.initial_board_state()
        }
        print("Game started:", game_data)
        return game_data

    def make_move(self, game_id, move):
        """
        Simulate sending a move to Lichess.
        In a real scenario, you would send a POST to something like
        /board/game/{gameId}/move/{move} and get back an updated board state.
        """
        print(f"Making move {move} in game {game_id}")
        time.sleep(0.5)  # Simulate delay
        # Return a dummy updated board state
        return {"boardState": f"updated_board_after_{move}"}

    def initial_board_state(self):
        """
        Return the starting board state (could be a FEN string).
        """
        return "startpos"

    def connect_to_game_stream(self, game_id, callback):
        """
        Simulate connecting to a WebSocket stream that notifies the client of game events,
        such as the bot making a move.
        The callback function is called with simulated event data.
        """
        def simulate_stream():
            while True:
                time.sleep(3)  # Wait before simulating a bot move
                # Simulate a bot move (choose one at random)
                bot_move = random.choice(["e2e4", "d2d4", "g1f3"])
                event_data = {
                    "type": "gameState",
                    "boardState": f"updated_board_after_bot_move_{bot_move}",
                    "lastMove": bot_move
                }
                # Call the callback to update the UI (remember to schedule on main thread)
                callback(event_data)
        # Run the simulated stream in a daemon thread so it doesn't block the app
        t = threading.Thread(target=simulate_stream, daemon=True)
        t.start()

# ------------------------------------------------------------
# Debug Log Widget
# ------------------------------------------------------------
class DebugLog(ScrollView):
    """
    A ScrollView containing a Label that logs debug messages.
    """
    def __init__(self, **kwargs):
        super(DebugLog, self).__init__(**kwargs)
        # Create a label that will contain our debug text.
        self.log_label = Label(size_hint_y=None, markup=True)
        self.log_label.bind(texture_size=self.log_label.setter('size'))
        self.add_widget(self.log_label)
        self.log("Debug log initialized.")

    def log(self, message):
        """
        Append a new message to the log.
        """
        current_text = self.log_label.text
        new_text = current_text + "\n" + message
        self.log_label.text = new_text
        # Ensure we scroll to the bottom so the latest message is visible.
        Clock.schedule_once(lambda dt: setattr(self, 'scroll_y', 0))

# ------------------------------------------------------------
# ChessBoard Widget
# ------------------------------------------------------------
# class ChessBoardWidget(Widget):
#     """
#     A simple widget that draws an 8x8 chessboard.
#     It listens for touch events so the player can select a square,
#     then select a destination square to perform a move.
#     """
#     def __init__(self, **kwargs):
#         super(ChessBoardWidget, self).__init__(**kwargs)
#         self.rows = 8
#         self.cols = 8
#         self.selected_square = None  # Will hold a tuple (row, col)
#         self.bind(pos=self.update_board, size=self.update_board)
#         self.update_board()

#     def update_board(self, *args):
#         """
#         Draw the board. Alternate colors for squares.
#         Highlight the selected square if one is chosen.
#         """
#         self.canvas.clear()
#         square_size = min(self.width, self.height) / 8.0
#         with self.canvas:
#             for row in range(self.rows):
#                 for col in range(self.cols):
#                     # Alternate colors: white and light gray
#                     if (row + col) % 2 == 0:
#                         Color(1, 1, 1)  # white
#                     else:
#                         Color(0.6, 0.6, 0.6)  # light gray
#                     Rectangle(pos=(self.x + col * square_size, self.y + row * square_size), size=(square_size, square_size))
#             # If a square is selected, draw a semi-transparent red overlay
#             if self.selected_square is not None:
#                 Color(1, 0, 0, 0.5)
#                 row, col = self.selected_square
#                 Rectangle(pos=(self.x + col * square_size, self.y + row * square_size), size=(square_size, square_size))

#     def on_touch_down(self, touch):
#         """
#         Detect when a square is touched.
#         Convert the touch position to board coordinates and either
#         select a square or, if one is already selected, interpret as a move.
#         """
#         if not self.collide_point(*touch.pos):
#             return False
#         square_size = min(self.width, self.height) / 8.0
#         col = int((touch.pos[0] - self.x) // square_size)
#         row = int((touch.pos[1] - self.y) // square_size)
#         # Log the square touched via the parent debug log
#         self.parent.debug_log.log(f"Touched square: row {row}, col {col}")
#         if self.selected_square is None:
#             self.selected_square = (row, col)
#             self.update_board()
#         else:
#             # Convert selected square and new square into a move string (simplified)
#             start = self.square_to_coord(self.selected_square)
#             end = self.square_to_coord((row, col))
#             move = start + end
#             self.parent.debug_log.log(f"Attempting move: {move}")
#             # Call the parent's method to handle the player's move
#             self.parent.handle_player_move(move)
#             self.selected_square = None
#             self.update_board()
#         return True

#     def square_to_coord(self, square):
#         """
#         Convert board coordinates (row, col) to algebraic notation.
#         (Assumes row 0 is rank 1 and col 0 is file 'a'.)
#         """
#         row, col = square
#         file = chr(ord('a') + col)
#         rank = str(row + 1)
#         return file + rank

# ------------------------------------------------------------
# Main Layout Combining the Board and Debug Log
# ------------------------------------------------------------
class MainLayout(BoxLayout):
    """
    The main layout of the app. It uses a vertical BoxLayout with:
      - The ChessBoardWidget (80% of the screen)
      - The DebugLog (20% of the screen)
    It also instantiates the LichessAPI and starts a game against a bot.
    """
    def __init__(self, **kwargs):
        super(MainLayout, self).__init__(**kwargs)
        self.orientation = 'vertical'

        # --- Define panel sizes ---
        panel_width = 400  # width (in pixels) for left (captured pieces) and right (move list) panels
        #screen_width = Window.width
        #screen_height = Window.height
        screen_width = 1920
        screen_height = 1080

        # The board size will be the maximum square that fits in the central area.
        board_size = min(screen_height, screen_width - 2 * panel_width)

        # Center the board in the area between the panels.
        board_origin_x = panel_width + ((screen_width - 2 * panel_width - board_size) / 2)
        board_origin_y = (screen_height - board_size) / 2
        board_origin = (board_origin_x, board_origin_y)

        self.chess_board = ChessBoard(board_origin=board_origin, board_size=board_size)

        # Add the chessboard widget
        #self.chess_board = ChessBoard()
        self.add_widget(self.chess_board)
        # Add the debug log widget
        self.debug_log = DebugLog(size_hint=(1, 0.2))
        self.add_widget(self.debug_log)
        # Initialize the API wrapper with your token (keep your token secret!)
        self.api = LichessAPI("YOUR_API_TOKEN_HERE")
        # Start the game in a separate thread so the UI isn’t blocked
        threading.Thread(target=self.start_game_against_bot, daemon=True).start()

    def start_game_against_bot(self):
        """
        Start a game against a bot and log all events.
        Connect to the simulated game stream to receive bot moves.
        """
        self.debug_log.log("Starting game against bot...")
        game_data = self.api.start_game(opponent_id="bot", variant="standard", rated=False, time_control={'limit':300, 'increment':10})
        self.game_id = game_data["id"]
        self.debug_log.log(f"Game started with ID: {self.game_id}")
        # (Optional) Update any internal board state with game_data["boardState"]
        # Connect to the game stream to listen for bot moves:
        self.api.connect_to_game_stream(self.game_id, self.on_game_event)

    def handle_player_move(self, move):
        """
        Called when the user makes a move on the board.
        Sends the move to Lichess via the API and logs the new board state.
        """
        self.debug_log.log(f"Player move: {move}")
        response = self.api.make_move(self.game_id, move)
        new_state = response.get("boardState", "unknown")
        self.debug_log.log(f"Board updated after your move: {new_state}")

    def on_game_event(self, event_data):
        """
        Callback function for events from the game stream (e.g., bot moves).
        This method is called from a background thread so we schedule UI updates on the main thread.
        """
        event_type = event_data.get("type")
        if event_type == "gameState":
            board_state = event_data.get("boardState")
            last_move = event_data.get("lastMove")
            message = f"Bot moved: {last_move}. New board state: {board_state}"
            # Schedule the update on the main thread
            Clock.schedule_once(lambda dt: self.debug_log.log(message))

# ------------------------------------------------------------
# Main Kivy App
# ------------------------------------------------------------
class ChessApp(App):
    def build(self):
        # Set the window to fullscreen
        Window.fullscreen = True
        return MainLayout()

if __name__ == '__main__':
    ChessApp().run()
