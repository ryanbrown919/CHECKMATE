# '''
# Used to track game state, register moves, check game codition, legal moves etc
# '''

import chess
import chess.pgn
import threading
import time
import berserk

class GameLogic:
    def __init__(self, token, is_bot=True):
        self.game_board = chess.Board()
        self.game = BerserkChessGame(token, is_bot=is_bot)
        self.game_state = "UNFINISHED"
        self.game_history = []
        self.game_pgn = chess.pgn.Game()
        self.observers = []  # UI callbacks for board updates
        self.SQUARES = chess.SQUARES

    def register_observer(self, observer_callback):
        """Register a callback (from your chessboard widget) to update the UI."""
        self.observers.append(observer_callback)

    def square(self, col, row):
        return chess.square(col, row)
    
    def square_file(self, sq):
        return chess.square_file(sq)
    
    def square_rank(self, sq):
        return chess.square_rank(sq)

    def notify_observers(self):
        for callback in self.observers:
            callback(self.game_board, self.game_state)

    def create_fen(self, fen):
        return chess.Board(fen)
    
    def update_board(self):
        return self.game_board

    def select_piece(self, square):
        # Find legal moves for the selected piece, update any boards with hgihlighted squares

        self.legal_moves = [move for move in self.game_board.legal_moves if move.from_square == square]

    def start_game(self, opponent="bot", **kwargs):
        if opponent == "bot":
            bot_username = kwargs.get("bot_username", "lichess-bot")
            level = kwargs.get("level", 1)
            rated = kwargs.get("rated", False)
            clock_limit = kwargs.get("clock_limit", 300)
            clock_increment = kwargs.get("clock_increment", 0)
            game_id = self.game.start_game_against_bot(bot_username=bot_username,
                                                          level=level,
                                                          rated=rated,
                                                          clock_limit=clock_limit,
                                                          clock_increment=clock_increment)
            self.game_board.reset()
            print(f"Started bot game. Game ID: {game_id}")
        elif opponent == "human":
            print("Human game selected. Ensure game_id is set and game stream is handled.")
        else:
            raise ValueError("Unsupported opponent type.")
            
        self.game_state = "IN_PROGRESS"
        self.notify_observers()

    def push_move(self, move_str):
        """
        Process a move made by the user, update the board, send the move via berserk,
        and notify the UI.
        """
        try:
            try:
                move = chess.Move.from_uci(move_str)
                if move not in self.game_board.legal_moves:
                    move = None
            except Exception:
                move = None

            if move is None:
                move = self.game_board.parse_san(move_str)
                
            if move not in self.game_board.legal_moves:
                raise ValueError("Illegal move: " + move_str)
        except Exception as e:
            print("Error parsing move:", e)
            return

        self.game_board.push(move)
        self.game_history.append(move)
        self.game.make_move(move.uci())
        self.notify_observers()
        self.check_game_status()


    def handle_opponent_move(self, move_str):
        """
        Process an opponent's move (e.g., received from the bot or Lichess stream),
        update the board, and notify the UI.
        """
        try:
            try:
                move = chess.Move.from_uci(move_str)
                if move not in self.game_board.legal_moves:
                    move = None
            except Exception:
                move = None

            if move is None:
                move = self.game_board.parse_san(move_str)
                
            if move not in self.game_board.legal_moves:
                raise ValueError("Illegal opponent move: " + move_str)
        except Exception as e:
            print("Error parsing opponent move:", e)
            return

        self.game_board.push(move)
        self.game_history.append(move)
        self.notify_observers()
        self.check_game_status()

    def check_game_status(self):
        if self.game_board.is_checkmate():
            self.game_state = "CHECKMATE"
            print("Checkmate detected!")
            self.notify_observers()
        elif self.game_board.is_stalemate():
            self.game_state = "STALEMATE"
            print("Stalemate detected!")
            self.notify_observers()
        elif self.game_board.is_insufficient_material():
            self.game_state = "DRAW - Insufficient Material"
            print("Draw detected: insufficient material.")
            self.notify_observers()
        # Additional game condition checks can be added here.

    def end_game(self):
        self.game_state = "FINISHED"
        print("Game finished.")
        self.notify_observers()


class BerserkChessGame:
    def __init__(self, token, game_id=None, is_bot=True):
        """
        Initialize the game backend.

        :param token: Your Lichess API token.
        :param game_id: The game ID on Lichess (if already started).
        :param is_bot: Set True if using a bot account (uses client.bots endpoints).
        """
        # Create an authenticated session with Lichess
        self.session = berserk.TokenSession(token)
        self.client = berserk.Client(session=self.session)
        self.client.account.upgrade_to_bot()


        self.game_id = game_id
        self.is_bot = is_bot
        self.board = chess.Board()

    def start_game_against_bot(self, bot_username, level=1, rated=False, clock_limit=300, clock_increment=0, variant="standard", color=None, fen=None):

        """
        Start a game against a bot by challenging it.

        :param bot_username: The username of the bot to challenge.
        :param level: The bot level (typically 1 to 8).
        :param rated: Whether the game is rated.
        :param clock_limit: Total time (in seconds) for the game.
        :param clock_increment: Increment per move (in seconds).
        :param variant: Chess variant, default "standard".
        :param color: Preferred color ("white" or "black"), if any.
        :param fen: Optional starting position in FEN notation.
        :return: The game ID of the newly started game.
        :raises NotImplementedError: If not using a bot account.
        """

        print("1")
        if not self.is_bot:
            raise NotImplementedError("Starting a game against a bot is only supported for bot accounts.")
        
        # Set up challenge parameters per Lichess API documentation.
        challenge_params = {
            "clock_limit": clock_limit, 
            "clock_increment": clock_increment,
            "variant": variant,
            "level": 2
        }
        if color:
            challenge_params["color"] = color
        if fen:
            challenge_params["fen"] = fen

        print("Challenge params:", challenge_params)

        # Send a challenge request to the bot.
        response = self.client.challenges.create_ai(level=2, color="white", variant="standard")
        # Expecting a response structure with a challenge id.
        print(response)
        self.game_id = response["id"]

        # Initialize board state from response (if moves already exist).
        moves = response.get("state", {}).get("moves", "")
        self.board.reset()
        if moves:
            for move in moves.split():
                self.board.push_uci(move)
        return self.game_id

    def stream_game(self):
        """
        Streams game events from Lichess to keep the local board updated.
        Blocks while streaming.
        """
        if not self.game_id:
            raise ValueError("Game ID must be provided to stream game events.")
        # Use different endpoints based on whether this is a bot game or a normal game.
        stream = (self.client.bots.stream_game_state(self.game_id) if self.is_bot 
                  else self.client.games.stream(self.game_id))
        for event in stream:
            self.handle_event(event)

    def handle_event(self, event):
        """
        Processes game events from Lichess. In a "gameFull" event the complete
        game state is provided; subsequent "gameState" events update the moves.
        """
        event_type = event.get("type")
        if event_type == "gameFull":
            # Initialize board from the full game state.
            moves = event.get("state", {}).get("moves", "")
            self.board.reset()
            if moves:
                for move in moves.split():
                    self.board.push_uci(move)
        elif event_type == "gameState":
            # Update board based on new moves.
            moves = event.get("moves", "")
            self.board.reset()
            if moves:
                for move in moves.split():
                    self.board.push_uci(move)
        # Other event types (e.g., chat messages) can be handled as needed.

    def make_move(self, move_str):
        """
        Makes a move on the local board and sends it to Lichess.
        The move can be provided in UCI (e.g. "e2e4") or SAN (e.g. "e4") notation.

        :param move_str: The move string.
        :raises ValueError: If the move is illegal.
        """
        try:
            # First try interpreting the move as UCI.
            move = chess.Move.from_uci(move_str)
            if move not in self.board.legal_moves:
                # If not legal, attempt to parse it as SAN.
                move = self.board.parse_san(move_str)
        except Exception:
            # Fallback: try to parse as SAN notation.
            move = self.board.parse_san(move_str)

        if move not in self.board.legal_moves:
            raise ValueError("Illegal move: " + move_str)

        # Update the local board state.
        self.board.push(move)

        # Send the move to Lichess.
        if self.is_bot:
            self.client.bots.make_move(self.game_id, move.uci())
        else:
            self.client.games.make_move(self.game_id, move.uci())

    def legal_moves(self):
        """
        Returns the current legal moves in Standard Algebraic Notation (SAN).

        :return: A list of legal moves.
        """
        return [self.board.san(move) for move in self.board.legal_moves]

    def board_fen(self):
        """
        Returns the current board state in FEN notation.
        """
        return self.board.fen()

    def get_board(self):
        """
        Returns the internal python-chess Board object.
        """
        return self.board





# Example usage:
if __name__ == "__main__":
    # Replace with your Lichess API token.

    with open('venv/key.txt', 'r') as f:
            api_key = f.read().strip()  # .strip() removes any extra whitespace or newline characters

    TOKEN = api_key
    
    # Initialize the game backend as a bot account.
    game = BerserkChessGame(TOKEN, is_bot=True)
    
    # Start a game against a specific bot.
    BOT_USERNAME = "lichess-bot"  # Replace with the bot's username you want to challenge.
    try:
        print("Trying to start game")
        game_id = game.lichess.start_game_against_bot(level=3, rated=False, 
                                               clock_limit=300, clock_increment=5)
        print(f"Game started against bot. Game ID: {game_id}")
        print("Initial board FEN:", game.board_fen())
    except Exception as e:
        print("Error starting game:", e)

    # Create a lock for synchronizing board state updates.
    state_lock = threading.Lock()

    # Start streaming game updates in a background thread.
    def stream_updates():
        # If game.stream_game() modifies the board, you can add locking inside that method,
        # or here if possible.
        game.stream_game()   # This call will block, hence running it in its own thread.

    stream_thread = threading.Thread(target=stream_updates, daemon=True)
    stream_thread.start()

    # Interactive game loop.
    while True:
        human_move = input("Enter your move in UCI or SAN format (or type 'quit' to exit): ")
        if human_move.lower() == "quit":
            print("Exiting game.")
            break

        try:
            # Lock the board state while making a move.
            with state_lock:
                game.client.bots.make_move(game_id, human_move)
                print("Move played. Current board FEN:")
                print(game.board_fen())
        except ValueError as e:
            print("Invalid move:", e)
            continue

        # Wait a bit for the bot's move to be processed.
        print("Waiting for bot move...")
        time.sleep(2)  # Adjust the delay as needed based on bot response time.

        with state_lock:
            print("Updated board FEN (after bot move):")
            print(game.board_fen())










