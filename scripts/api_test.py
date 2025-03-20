import berserk

with open('venv/key.txt', 'r') as f:
            api_key = f.read().strip()  # .strip() removes any extra whitespace or newline characters

session = berserk.TokenSession(api_key)
client = berserk.Client(session=session)

client.account.upgrade_to_bot()

print(client.account.get())
