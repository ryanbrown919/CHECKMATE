import threading
import time
import chess
import berserk  # For online play; pip install berserk
import chess.engine  # For offline UCI engine support
import sys

running_on_pi = sys.platform.startswith("linux")
running_on_mac = sys.platform.startswith("darwin")

class ChessBackend(threading.Thread):
    def __init__(self, lichess_token, ui_move_callback, mode="online", engine_path=None,
                 engine_time_limit=0.1, difficulty_level=5, elo=1400):
        """
        :param lichess_token: Your Lichess API token (used in online mode).
        :param ui_move_callback: A callback function to update the UI with opponent moves.
        :param mode: "online" or "offline" to select the mode of play.
        :param engine_path: Path to the UCI engine binary (e.g., Stockfish) for offline mode.
        :param engine_time_limit: Time limit (in seconds) for the engine to compute a move.
        :param difficulty_level: Difficulty level on a scale of 1 (easiest) to 10 (hardest) for offline mode.
        """
        super().__init__()
        self.mode = mode
        self.ui_move_callback = ui_move_callback
        self.lichess_token = lichess_token
        self.board = chess.Board()
        self.board_lock = threading.Lock()
        self._stop_event = threading.Event()
        self.elo = elo
        
        # Online mode variables
        self.game_id = None
        if self.mode == "online":
            self.session = berserk.TokenSession(lichess_token)
            self.client = berserk.Client(session=self.session)
        
        # Offline mode variables

        if running_on_pi:
            engine_path = "./bin/stockfish-android-armv8"
        elif running_on_mac:
            engine_path = "./bin/stockfish-macos-m1-apple-silicon"


        self.engine_path = engine_path
        self.engine_time_limit = engine_time_limit
        self.difficulty_level = difficulty_level  # Scale 1 (easiest) to 10 (hardest)
        self.engine = None  # Will be initialized in offline mode



        self.game_history = []
        self.SQUARES = chess.SQUARES
        self.observers = []
        self.game_state = "UNFINISHED"
        self.captured_pieces = []
        self.move_history = []



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
                    # Configure the engine for a variable difficulty.
                    # Map difficulty_level (1 to 10) to an Elo value between 1350 and 2850.
                    #elo = int(1350 + (self.difficulty_level - 1) * (1500 / 9))
                    self.engine.configure({"UCI_LimitStrength": True, "UCI_Elo": self.elo})
                    print(f"Offline engine configured at difficulty level {self.difficulty_level} (Elo {self.elo}).")
                except Exception as e:
                    print("Error initializing offline engine:", e)
                    return
            else:
                print("Offline mode requires an engine_path to a UCI engine like Stockfish.")
                return

            # Main offline loop: wait for the opponent's turn and compute a move when needed.
            while not self._stop_event.is_set():
                with self.board_lock:
                    # In this example, the offline bot plays as Black.
                    if self.board.turn == chess.BLACK:
                        try:
                            result = self.engine.play(self.board, chess.engine.Limit(time=self.engine_time_limit))
                            move = result.move
                            print(f"Test move: {move}")
                            self.move_history.append(f"{move}")

                            if self.board.is_capture(move):
                            # For a normal capture, the captured piece is on the destination square.
                                captured_piece = self.board.piece_at(move.to_square)
                                if captured_piece:
                                    self.captured_pieces.append(captured_piece.symbol())
                                    # Note: You might need special handling for en passant captures.
                                

                            self.board.push(move)
                            #self.notify_observers()
                            #self.push_move(move)
                            if self.ui_move_callback:
                                self.ui_move_callback(move.uci())
                        except Exception as e:
                            print("Error computing engine move:", e)
                time.sleep(0.1)
            self.engine.quit()

    def _stream_game(self):
        """
        Streams online game events from Lichess and updates the board accordingly.
        """
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
        """
        Processes a space-separated string of moves from Lichess, pushing any new moves to the local board.
        """
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
                        # self.move_history.append(move)

                        ##self.board.push(move)
                        self.push_move(move)

                        # if self.board.is_capture(move):
                        #     # For a normal capture, the captured piece is on the destination square.
                        #     captured_piece = self.board.piece_at(move.to_square)
                        #     if captured_piece:
                        #         self.captured_pieces.append(captured_piece.symbol())
                        #         # Note: You might need special handling for en passant captures.
                        
                        # #self.move_history.append(move)


                        if self.ui_move_callback:
                            self.ui_move_callback(move.uci())
                    except Exception as e:
                        print("Error processing move:", move_uci, e)

    def start_game(self):
        """
        Starts a new game in online mode.
        In offline mode, the board is already initialized.
        """
        if self.mode == "online":
            try:
                # Request a game as white.
                game = self.client.bots.create_game(challenge={'color': 'white'})
                self.game_id = game["id"]
                print("Online game started with game_id:", self.game_id)
            except Exception as e:
                print("Error starting online game:", e)
        else:
            print("Offline mode: game state already initialized.")

    def push_move(self, move_text):
        """
        Processes a move input (as a UCI string, e.g., "e2e4") from the UI.
        Validates and applies the move to the board, then sends it online if in online mode.
        """

        print(f"Trying to execute: {move_text}")
        with self.board_lock:
            print("ollo")
            try:
                move = chess.Move.from_uci(move_text)
            except ValueError as e:
                print("Invalid UCI move notation:", move_text)
                return

            if move not in self.board.legal_moves:
                print("Illegal move attempted:", move_text)
                return
            
                    # Check if the move is a capture before pushing it.
            if self.board.is_capture(move):
                # For a normal capture, the captured piece is on the destination square.
                captured_piece = self.board.piece_at(move.to_square)
                if captured_piece:
                    self.captured_pieces.append(captured_piece.symbol())
                    # Note: You might need special handling for en passant captures.
            
            self.move_history.append(move_text)


            print("hi")

            self.board.push(move)

            print("you made it")

            self.notify_observers()

        if self.mode == "online":
            try:
                self.client.bots.make_move(self.game_id, move_text)
            except Exception as e:
                print("Error sending move to Lichess:", e)





    def stop(self):
        self._stop_event.set()

    def select_piece(self, square):
        # Find legal moves for the selected piece, update any boards with hgihlighted squares

        legal_moves = [move for move in self.board.legal_moves if move.from_square == square]
        self.update_board()
        return legal_moves
    
    def register_observer(self, observer_callback):
        """Register a callback (from your chessboard widget) to update the UI."""
        self.observers.append(observer_callback)

    def notify_observers(self):
        for callback in self.observers:
            callback(self.board, self.game_state)

    def update_board(self):
        return self.board
    
    def square(self, col, row):
        return chess.square(col, row)
    
    def square_file(self, sq):
        return chess.square_file(sq)
    
    def square_rank(self, sq):
        return chess.square_rank(sq)
    import chess

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



# Example usage:
if __name__ == "__main__":
    # Dummy UI callback for demonstration purposes.
    def ui_callback(move_uci):
        print("UI update with move:", move_uci)
    
    # Replace with your actual Lichess token and the path to the Stockfish binary.
    TOKEN = "your-lichess-api-token"

    if running_on_pi:
        STOCKFISH_PATH = "./bin/stockfish-android-armv8"
    elif running_on_mac:
        STOCKFISH_PATH = "./bin/stockfish-macos-m1-apple-silicon"
    #STOCKFISH_PATH = "/usr/local/bin/stockfish"  # Adjust as necessary for your OS.

    # Create the backend in offline mode with a chosen difficulty level.
    backend = ChessBackend(lichess_token=TOKEN, ui_move_callback=ui_callback,
                           mode="offline", engine_path=STOCKFISH_PATH,
                           engine_time_limit=0.1, difficulty_level=5)
    backend.start()


    print("Game started. Enter moves in UCI or SAN notation. Type 'q' to quit.")
    while True:
        move_str = input("Your move: ").strip()
        if move_str.lower() == 'q':
            print("Exiting game loop.")
            break
        backend.push_move(move_str)


    # Later, when shutting down:
    time.sleep(5)
    backend.stop()
    backend.join()
