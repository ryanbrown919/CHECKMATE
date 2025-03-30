import chess
import chess.engine
import threading
import time
from kivy.clock import Clock

# A simple state machine class.
class SimpleStateMachine:
    def __init__(self, initial_state):
        self.state = initial_state
        # transitions maps (source_state, event) -> (target_state, callback, condition)
        self.transitions = {}

    def add_transition(self, source, event, target, callback=None, condition=None):
        # condition is a function that returns True/False; default is always True.
        if condition is None:
            condition = lambda: True
        self.transitions[(source, event)] = (target, callback, condition)

    def trigger(self, event, *args, **kwargs):
        key = (self.state, event)
        if key in self.transitions:
            target, callback, condition = self.transitions[key]
            if condition():
                print(f"[StateMachine] Transitioning from '{self.state}' to '{target}' on event '{event}'")
                self.state = target
                if callback:
                    callback(*args, **kwargs)
            else:
                print(f"[StateMachine] Condition for transition '{event}' not met in state '{self.state}'")
        else:
            print(f"[StateMachine] No transition defined for state '{self.state}' on event '{event}'")


# A simplified ChessControlSystem using the simple state machine.
class ChessControlSystem:
    def __init__(self, ui_update_callback=None):
        self.ui_update_callback = ui_update_callback

        # Our chess board.
        self.board = chess.Board()
        self.running = True

        # Set some default parameters.
        self.parameters = {
            'online': False,
            'colour': 'white',  # "white" means player goes first, "black" means engine goes first.
            'elo': 1500,
            'timer': False,
            'engine_time_limit': 0.1,
            'bot_mode': False
        }
        self.auto_engine = self.parameters.get("bot_mode", False)
        self.engine_path = "./bin/stockfish-macos-m1-apple-silicon"  # Adjust as needed.
        self.engine = None
        self.clock_logic = None

        # Initialize our simple state machine with an initial state.
        # We'll use these states: "initscreen", "mainscreen", and then a composite "gamescreen" with substates.
        # For simplicity, we flatten the hierarchy.
        self.sm = SimpleStateMachine("initscreen")

        # Add transitions:
        self.sm.add_transition("initscreen", "finish_loading", "mainscreen", callback=self.update_ui)
        # When starting a game from mainscreen, decide based on the "colour" parameter.
        self.sm.add_transition("mainscreen", "start_game", "gamescreen_player_turn",
                                 callback=lambda: [self.on_player_turn(), self.init_game(), self.update_ui()],
                                 condition=lambda: self.parameters.get("colour", "white") == "white")
        self.sm.add_transition("mainscreen", "start_game", "gamescreen_engine_turn",
                                 callback=lambda: [self.on_engine_turn(), self.init_game(), self.update_ui()],
                                 condition=lambda: self.parameters.get("colour", "white") == "black")
        # Transition from player turn to engine turn when processing a move.
        self.sm.add_transition("gamescreen_player_turn", "process_move", "gamescreen_engine_turn",
                                 callback=lambda: [self.on_board_turn(), self.notify_observers()])
        # Transition from engine turn back to player turn (unless auto_engine is on).
        self.sm.add_transition("gamescreen_engine_turn", "engine_move_complete", "gamescreen_player_turn",
                                 callback=lambda: [self.on_player_turn(), self.notify_observers()],
                                 condition=lambda: not self.auto_engine)
        # If auto_engine mode is on, engine move completes and remains in engine turn.
        self.sm.add_transition("gamescreen_engine_turn", "engine_move_complete", "gamescreen_engine_turn",
                                 callback=lambda: [self.on_board_turn(), self.notify_observers()],
                                 condition=lambda: self.auto_engine)
        # Add an end game transition.
        self.sm.add_transition("gamescreen_player_turn", "end_game", "gamescreen_end_game", callback=self.on_end_game)
        self.sm.add_transition("gamescreen_engine_turn", "end_game", "gamescreen_end_game", callback=self.on_end_game)

        # Start a background thread to run a loop if needed.
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        while self.running:
            time.sleep(0.1)

    def update_ui(self):
        state = self.sm.state
        print(f"[UI] Updated to state: {state}")
        if self.ui_update_callback:
            # Use Clock to schedule UI updates on the main thread.
            Clock.schedule_once(lambda dt: self.ui_update_callback(state), 0)

    def notify_observers(self):
        # Here you would call any callbacks that update the UI based on board changes.
        print("[Control] Notifying observers of board change.")
        if self.ui_update_callback:
            Clock.schedule_once(lambda dt: self.ui_update_callback(self.sm.state), 0)

    # State entry callbacks:
    def init_game(self):
        print("Initializing game with parameters:", self.parameters)
        # (Initialize gantry, engine, etc.)
        # For offline play, initialize engine:
        if not self.parameters['online'] and self.engine_path:
            try:
                import chess.engine
                self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
                self.engine.configure({"UCI_LimitStrength": True, "UCI_Elo": self.parameters['elo']})
                print(f"[Engine] Initialized engine at Elo {self.parameters['elo']}")
            except Exception as e:
                print("[Engine] Error initializing engine:", e)
                self.engine = None

    def on_player_turn(self):
        print("[State] Entering Player Turn")
        self.update_ui()
        # Here, for example, you might start polling for user input.
        # In a real implementation, sensor or UI input would trigger a move.
        
    def on_engine_turn(self):
        print("[State] Entering Engine Turn")
        self.update_ui()
        # Start engine move in a background thread.
        threading.Thread(target=self.compute_engine_move, daemon=True).start()

    def on_board_turn(self):
        # This callback is used when transitioning from player move to engine move.
        print("[State] Processing board turn (engine move)")
        self.update_ui()

    def on_end_game(self):
        print("[State] Game Over")
        self.running = False
        self.update_ui()
        if self.engine:
            self.engine.quit()
            self.engine = None

    def compute_engine_move(self):
        # Simulate engine thinking.
        time.sleep(1)
        if self.engine:
            try:
                result = self.engine.play(self.board, chess.engine.Limit(time=self.parameters.get("engine_time_limit", 0.1)))
                move = result.move
                print(f"[Engine] Engine move: {move}")
                self.board.push(move)
            except Exception as e:
                print("[Engine] Error computing engine move:", e)
            finally:
                # For simplicity, we close the engine after each move.
                self.engine.quit()
                self.engine = None
        else:
            # Fallback: choose first legal move.
            legal_moves = list(self.board.legal_moves)
            if legal_moves:
                move = legal_moves[0]
                print(f"[Engine] Fallback move: {move}")
                self.board.push(move)
        # After engine move, trigger the event.
        self.sm.trigger("engine_move_complete")

    # Example method to handle UI moves (from a chessboard widget).
    def handle_ui_move(self, move_uci):
        print(f"[Control] Received UI move: {move_uci}")
        try:
            move = chess.Move.from_uci(move_uci)
        except Exception as e:
            print(f"[Control] Invalid move notation: {move_uci} ({e})")
            return False

        if move not in self.board.legal_moves:
            print(f"[Control] Illegal move attempted: {move_uci}")
            return False

        self.board.push(move)
        print(f"[Control] Move applied: {move_uci}")
        self.notify_observers()

        # Schedule a transition to engine turn.
        Clock.schedule_once(lambda dt: self.sm.trigger("process_move"), 0.1)
        return True

    # Convenience trigger methods to allow UI to call the simple state machine.
    def finish_loading(self):
        self.sm.trigger("finish_loading")

    def start_game(self):
        self.sm.trigger("start_game")

    def end_game(self):
        self.sm.trigger("end_game")


# Example usage:
if __name__ == '__main__':
    # For demonstration, define a simple UI update callback.
    def ui_callback(state):
        print(f"[UI Callback] New state: {state}")

    control = ChessControlSystem(ui_update_callback=ui_callback)
    # Simulate finishing loading then starting a game.
    Clock.schedule_once(lambda dt: control.finish_loading(), 2)
    Clock.schedule_once(lambda dt: control.start_game(), 4)

    # Keep the program running.
    while control.running:
        time.sleep(0.1)
