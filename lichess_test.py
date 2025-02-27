import berserk
import chess

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
        self.game_id = game_id
        self.is_bot = is_bot
        self.board = chess.Board()

    def start_game_against_bot(self, level=1, rated=False, 
                               clock_limit=300, clock_increment=0, variant="standard", 
                               color=None, fen=None):
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
        game_id = game.start_game_against_bot(level=3, rated=False, 
                                               clock_limit=300, clock_increment=5)
        print(f"Game started against bot. Game ID: {game_id}")
        print("Initial board FEN:", game.board_fen())
    except Exception as e:
        print("Error starting game:", e)
    
    # Example: Making a move (input can be UCI or SAN)
    try:
        print(game)
        game.client.board.make_move(game_id,"e2e4")
        print("Move played. Current board FEN:")
        print(game.board_fen())
    except ValueError as e:
        print(e)

    # To stream game updates from Lichess (this call will block)
    # game.stream_game()
