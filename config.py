import os
from dotenv import load_dotenv

load_dotenv()


def _parse_ids(value: str):
    return [int(x) for x in value.replace(" ", "").split(",") if x]


class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_IDS = _parse_ids(os.getenv("ADMIN_IDS", ""))
    PRIVATE_CHANNEL_ID = os.getenv("PRIVATE_CHANNEL_ID")
    TMDB_API_KEY = os.getenv("TMDB_API_KEY")
    FORCE_CHANNEL_ID = os.getenv("FORCE_CHANNEL_ID")
    # Ixtiyoriy: kanal havolasi (https://t.me/kanal yoki taklif havolasi).
    # Ko'rsatilmasa, bot kanal ma'lumotidan o'zi aniqlaydi.
    FORCE_CHANNEL_LINK = os.getenv("FORCE_CHANNEL_LINK")
    FORCE_CHANNEL_CHECK = os.getenv("FORCE_CHANNEL_CHECK", "false").lower() == "true"
    DB_FILE = os.getenv("DB_FILE", "movies.db")

    @classmethod
    def validate(cls):
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required in .env file")
        if not cls.ADMIN_IDS:
            raise ValueError("ADMIN_IDS is required in .env file")
