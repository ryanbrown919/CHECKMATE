import berserk

with open('venv/key.txt', 'r') as f:
            api_key = f.read().strip()  # .strip() removes any extra whitespace or newline characters

session = berserk.TokenSession(api_key)
client = berserk.Client(session=session)

client.challenges.create_ai(
    level=3,
    clock_limit=300,
    clock_increment=0,
    color="white",
    variant="standard"
)


client.games.get_game_state(client.games.)
