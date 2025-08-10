import discord
from discord.ext import commands
from app.service.pull_service import PullService
from app.service.player_service import PlayerService

class PixelPetBot(commands.Bot):
    def __init__(self, config):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.config = config
        self.gacha_service = PullService()
        self.player_service = PlayerService()

    async def setup_hook(self):
        from app.bot import bot_commands
        await bot_commands.setup(self)

    async def on_ready(self):
        print(f"✅ Logged in as {self.user}")
