"""Bazani yangi tuzilishga xavfsiz o'tkazish.

Eski versiyadagi skript bazani o'chirib, qaytadan yaratardi. Endi bunga hojat yo'q:
Database.init_db() yetishmayotgan jadval/ustunlarni qo'shadi, FTS triggerlarini
tuzatadi va qidiruv indeksini qayta quradi. Ma'lumotlar o'chirilmaydi.

Ishga tushirishdan oldin zaxira nusxa olinadi: movies_backup_<sana>.db
"""
import asyncio
import logging
import shutil
from datetime import datetime
from pathlib import Path

from config import Config
from database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    db_path = Path(Config.DB_FILE)
    if db_path.exists():
        backup = db_path.with_name(f"{db_path.stem}_backup_{datetime.now():%Y%m%d_%H%M%S}.db")
        shutil.copy2(db_path, backup)
        logger.info(f"Zaxira nusxa: {backup}")

    db = Database(str(db_path))
    await db.init_db()
    logger.info(f"Migratsiya tugadi. Kinolar soni: {await db.get_total_movies()}")


if __name__ == "__main__":
    asyncio.run(migrate())
