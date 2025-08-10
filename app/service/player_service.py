class PlayerService:
    def __init__(self):
        self.players = {}  # { discord_id: { "inventory": [Character, ...] } }

    def create_account(self, discord_id):
        self.players.setdefault(discord_id, {"inventory": []})

    def add_character(self, discord_id, char):
        self.players[discord_id]["inventory"].append(char)

    def get_inventory(self, discord_id):
        return self.players[discord_id]["inventory"]
