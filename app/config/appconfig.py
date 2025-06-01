import os
import sys
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

class AppConfig:
    def __init__(self):
        load_dotenv()
        self.DISCORD_PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY", "")
        self.DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
        self.DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")