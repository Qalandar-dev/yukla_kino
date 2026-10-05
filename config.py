import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []
    PRIVATE_CHANNEL_ID = os.getenv("PRIVATE_CHANNEL_ID")
    TMDB_API_KEY = os.getenv("TMDB_API_KEY")
    FORCE_CHANNEL_ID = os.getenv("FORCE_CHANNEL_ID")
    FORCE_CHANNEL_CHECK = os.getenv("FORCE_CHANNEL_CHECK", "false").lower() == "true"
    
    @classmethod
    def validate(cls):
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required in .env file")
        if not cls.ADMIN_IDS:
            raise ValueError("ADMIN_IDS is required in .env file")
