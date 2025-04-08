import threading
import time
import chess
import berserk  # For online play; pip install berserk
import chess.engine  # For offline UCI engine support
import sys
import random
from transitions import Machine

if sys.platform.startswith("linux"):
    running_on_pi = True
    
else:
    running_on_pi = False

running_on_mac = sys.platform.startswith("darwin")


# =========================
# State Machine Definition
# =========================

from transitions import Machine
import threading

class ChessGameStateMachine(object):
    # Define the distinct states.
    states = [
        'idle',
        'player_turn',
        'hall_polling',
        'player_move_confirmed',
        'engine_turn',
        'game_over'
    ]

    def __init__(self, backend, ui_update_callback=None):
        """
        :param backend: Reference to your game backend.
        :param ui_update_callback: Function to update UI text/status.
        """
        self.backend = backend
        self.ui_update_callback = ui_update_callback  # e.g. lambda status: update_ui_label(status)
        self.machine = Machine(model=self, states=ChessGameStateMachine.states, initial='idle')

        # Define transitions with triggers and after-callbacks.
        self.machine.add_transition(trigger='start_game', source='idle', dest='player_turn', after='on_player_turn')
        self.machine.add_transition(trigger='begin_polling', source='player_turn', dest='hall_polling', after='on_hall_polling')
        self.machine.add_transition(trigger='move_detected', source='hall_polling', dest='player_move_confirmed', after='on_player_move_confirmed')
        self.machine.add_transition(trigger='process_move', source='player_move_confirmed', dest='engine_turn', after='on_engine_turn')
        self.machine.add_transition(trigger='engine_move_complete', source='engine_turn', dest='player_turn', after='on_player_turn')
        self.machine.add_transition(trigger='end_game', source='*', dest='game_over', after='on_game_over')

    def on_player_turn(self):
        print("State: Player Turn")
        if self.ui_update_callback:
            self.ui_update_callback("Player Turn")
        # For example, when entering player's turn, you might want to start hall effect polling:
        self.begin_polling()

    def on_hall_polling(self):
        print("State: Hall Polling Active")
        if self.ui_update_callback:
            self.ui_update_callback("Polling: Awaiting Player Move")
        # Activate your hall effect sensor polling here.
        # For example, you might start a thread that monitors the sensor:
        threading.Thread(target=self.backend.activate_hall_polling).start()

    def on_player_move_confirmed(self):
        print("State: Player Move Confirmed")
        if self.ui_update_callback:
            self.ui_update_callback("Player Move Detected")
        # Once the move is confirmed by the sensor,
        # stop polling and update any UI components accordingly.
        self.backend.deactivate_hall_polling()

    def on_engine_turn(self):
        print("State: Engine Turn")
        if self.ui_update_callback:
            self.ui_update_callback("Engine Computing Move")
        # Trigger engine move processing in a separate thread.
        threading.Thread(target=self.backend.process_engine_move).start()

    def on_game_over(self):
        print("State: Game Over")
        if self.ui_update_callback:
            self.ui_update_callback("Game Over")
        # Perform any cleanup actions here.


# =========================
# Updated Chess Backend
# =========================

class ChessBackend(threading.Thread):
    def __init__(self, lichess_token, ui_move_callback, mode="online", engine_path=None,
                 engine_time_limit=1, difficulty_level=5, elo=1400, preferred_color='white',
                 clock_logic=None, bot_mode=False, gantry_control=None):
        """
        Initialization as before. (Comments omitted for brevity.)
        """
        super().__init__()
        self.mode = mode
        self.ui_move_callback = ui_move_callback
        self.lichess_token = lichess_token
        self.board = chess.Board()
        self.board_lock = threading.Lock()
        self._stop_event = threading.Event()
        self.elo = elo
        self.preferred_color = preferred_color
        self.bot_mode = bot_mode
        self.gantry_control = gantry_control
        self.clock_logic = clock_logic

        if self.preferred_color == 'Random':
            self.preferred_color = random.choice(['White', 'Black'])
        elif self.preferred_color == "Bot V Bot":
            self.bot_mode = True
            self.engine_color = chess.WHITE

        if self.preferred_color == "Black":
            self.engine_color = chess.WHITE
        else:
            self.engine_color = chess.BLACK

        # Online mode variables
        self.game_id = None
        if self.mode == "online":
            self.session = berserk.TokenSession(lichess_token)
            self.client = berserk.Client(session=self.session)

        # Offline mode engine initialization
        if running_on_pi:
            engine_path = "./bin/stockfish-android-armv8"
        elif running_on_mac:
            engine_path = "./bin/stockfish-macos-m1-apple-silicon"
        self.engine_path = engine_path
        self.engine_time_limit = engine_time_limit
        self.difficulty_level = difficulty_level  # 1 (easiest) to 10 (hardest)
        self.engine = None

        self.first_move = True
        self.game_history = []
        self.observers = []
        self.game_state = "UNFINISHED"
        self.captured_pieces = []
        self.move_history = []

        # Create an instance of our gameplay state machine
        self.game_sm = ChessGameStateMachine(self)



    def run(self):
        if self.mode == "online":
            if not self.game_id:
                print("No game started. Call start_game() first.")
                return
            self._stream_game()
        elif self.mode == "offline":
            if self.engine_path:
                try:
                    self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
                    self.engine.configure({"UCI_LimitStrength": True, "UCI_Elo": self.elo})
                    print(f"Offline engine configured at difficulty level {self.difficulty_level} (Elo {self.elo}).")
                except Exception as e:
                    print("Error initializing offline engine:", e)
                    return
            else:
                print("Offline mode requires an engine_path to a UCI engine like Stockfish.")
                return

            # Start the game by triggering the state machine.
            self.game_sm.start_game()

            # Instead of a continuous while loop doing board.turn checks,
            # the state machine will trigger engine move processing.
            while not self._stop_event.is_set():
                time.sleep(0.1)
            if self.engine:
                self.engine.quit()

    def process_engine_move(self):
        """Called when the state machine enters the engine_turn state.
           Computes the engine move, updates the board, and triggers the next transition.
        """
        with self.board_lock:
            if self.board.turn == self.engine_color or self.bot_mode:
                try:
                    result = self.engine.play(self.board, chess.engine.Limit(time=self.engine_time_limit))
                    move = result.move
                    print(f"Engine computed move: {move}")
                    self.move_history.append(move.uci())

                    if self.gantry_control:
                        # If using gantry control, send the computed move commands.
                        if self.gantry_control.simulate:
                            time.sleep(3)
                        else:
                            path = self.gantry_control.interpret_chess_move(move.uci(), self.board.is_capture(move))
                            movements = self.gantry_control.parse_path_to_movement(path)
                            commands = self.gantry_control.movement_to_gcode(movements)
                            print(f"Moving a piece via commands: {commands}")
                            self.gantry_control.send_commands(commands)

                    # Handle captures and game state checks
                    if self.board.is_capture(move):
                        captured_piece = self.board.piece_at(move.to_square)
                        if captured_piece:
                            self.captured_pieces.append(captured_piece.symbol())

                    if self.board.is_checkmate():
                        self.game_state = 'CHECKMATE'
                        # Transition to game over state
                        self.game_sm.game_over_event()
                    elif self.board.is_check():
                        self.game_state = 'CHECK'
                    else:
                        self.game_state = 'UNFINISHED'

                    self.board.push(move)
                    if self.ui_move_callback:
                        self.ui_move_callback(move.uci())
                except Exception as e:
                    print("Error computing engine move:", e)
        # If the game isn’t over, signal that the engine move is done.
        if self.game_sm.state != 'game_over':
            self.game_sm.engine_move_done()

    def push_move(self, move_text):
        """Processes a move input (UCI string) from the UI.
           Validates the move, applies it to the board, and triggers the next state.
        """
        print(f"Trying to execute: {move_text}")
        with self.board_lock:
            try:
                move = chess.Move.from_uci(move_text)
            except ValueError:
                print("Invalid UCI move notation:", move_text)
                return

            if move not in self.board.legal_moves:
                print("Illegal move attempted:", move_text)
                return

            if self.board.is_capture(move):
                captured_piece = self.board.piece_at(move.to_square)
                if captured_piece:
                    self.captured_pieces.append(captured_piece.symbol())

            self.move_history.append(move_text)
            self.board.push(move)
            self.notify_observers()

            if self.ui_move_callback:
                self.ui_move_callback(move.uci())

            # After a valid player move, check for game over conditions.
            if self.board.is_checkmate():
                self.game_state = 'CHECKMATE'
                self.game_sm.game_over_event()
            else:
                # Transition to engine turn after player move.
                self.game_sm.player_move_done()

    def _stream_game(self):
        """Online mode: Streams game events from Lichess and processes moves."""
        try:
            stream = self.client.bots.stream_game_state(self.game_id)
        except Exception as e:
            print("Error starting game stream:", e)
            return

        for event in stream:
            if self._stop_event.is_set():
                break
            event_type = event.get("type")
            if event_type == "gameFull":
                moves_str = event.get("state", {}).get("moves", "")
                self._process_moves(moves_str)
            elif event_type == "gameState":
                moves_str = event.get("moves", "")
                self._process_moves(moves_str)

    def _process_moves(self, moves_str):
        if not moves_str:
            return
        moves_list = moves_str.split()
        with self.board_lock:
            applied_moves = list(self.board.move_stack)
            if len(moves_list) > len(applied_moves):
                new_moves = moves_list[len(applied_moves):]
                for move_uci in new_moves:
                    try:
                        move = chess.Move.from_uci(move_uci)
                        self.push_move(move.uci())
                    except Exception as e:
                        print("Error processing move:", move_uci, e)

    def start_game(self):
        """Starts a new game. In online mode, requests a game from Lichess."""
        if self.mode == "online":
            try:
                game = self.client.bots.create_game(challenge={'color': 'white'})
                self.game_id = game["id"]
                print("Online game started with game_id:", self.game_id)
            except Exception as e:
                print("Error starting online game:", e)
        else:
            print("Offline mode: game state already initialized.")

    def register_observer(self, observer_callback):
        """Register a UI callback to update on board changes."""
        self.observers.append(observer_callback)

    def notify_observers(self):
        for callback in self.observers:
            callback(self.board, self.game_state)

    def select_piece(self, square):
        # Find legal moves for the selected piece, update any boards with hgihlighted squares

        legal_moves = [move for move in self.board.legal_moves if move.from_square == square]
        self.notify_observers()
        return legal_moves
    
    def calculate_material(self, board):
        # Standard piece values: pawn=1, knight=3, bishop=3, rook=5, queen=9, king=0
        values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0
        }
        white_score = 0
        black_score = 0

        if board is None:
            board = self.board

        for square, piece in board.piece_map().items():
            if piece.color == chess.WHITE:
                white_score += values[piece.piece_type]
            else:
                black_score += values[piece.piece_type]

        print(f"White: {white_score}, Black: {black_score}")
        
        # A positive result indicates a material advantage for White,
        # while a negative result indicates an advantage for Black.
        return white_score, black_score

    def stop(self):
        self._stop_event.set()

    # The remaining methods (select_piece, square, etc.) and clock/servo classes remain unchanged.
    # ...

# =========================
# Example usage
# =========================

if __name__ == "__main__":
    def ui_callback(move_uci):
        print("UI updated with move:", move_uci)

    TOKEN = "your-lichess-api-token"
    if running_on_pi:
        STOCKFISH_PATH = "./bin/stockfish-android-armv8"
    elif running_on_mac:
        STOCKFISH_PATH = "./bin/stockfish-macos-m1-apple-silicon"
    else:
        STOCKFISH_PATH = "/usr/local/bin/stockfish"  # Adjust if necessary

    # Create backend in offline mode.
    backend = ChessBackend(
        lichess_token=TOKEN,
        ui_move_callback=ui_callback,
        mode="offline",
        engine_path=STOCKFISH_PATH,
        engine_time_limit=0.1,
        difficulty_level=5
    )
    backend.start()

    print("Game started. Enter moves in UCI notation. Type 'q' to quit.")
    while True:
        move_str = input("Your move: ").strip()
        if move_str.lower() == 'q':
            print("Exiting game loop.")
            break
        backend.push_move(move_str)

    time.sleep(5)
    backend.stop()
    backend.join()
