import sys
import os
sys.path.append(os.getcwd())
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.config.AppConfig import AppConfig
from app.bot.bot_client import PixelPetBot

if __name__ == "__main__":
    config = AppConfig()
    if not config.DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN not found in .env file")
        sys.exit(1)

    bot = PixelPetBot(config)
    bot.run(config.DISCORD_TOKEN)
