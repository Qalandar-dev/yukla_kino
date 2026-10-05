import sqlite3
import aiosqlite
import asyncio
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    """Eski bazadan yangi bazaga ma'lumotlarni ko'chirish"""
    old_db = "movies.db"
    new_db = "movies.db"
    
    # Avval eski bazadan ma'lumotlarni o'qish
    logger.info("Eski bazadan ma'lumotlarni o'qish...")
    old_conn = sqlite3.connect(old_db)
    old_cursor = old_conn.cursor()
    
    # Eski jadval tuzilishi: code, file_id, title, added_at
    old_cursor.execute("SELECT code, file_id, title, added_at FROM movies")
    old_movies = old_cursor.fetchall()
    old_conn.close()
    
    logger.info(f"{len(old_movies)} ta kino topildi")
    
    # Eski bazani o'chirish (yangi strukturaga o'tish uchun)
    logger.info("Eski jadvalni o'chirish...")
    os.remove(old_db)
    
    # Yangi bazani yaratish
    from database import Database
    db = Database(new_db)
    await db.init_db()
    
    # Ma'lumotlarni ko'chirish
    logger.info("Ma'lumotlarni yangi bazaga ko'chirish...")
    for code, file_id, title, added_at in old_movies:
        await db.add_movie(
            code=code,
            file_id=file_id,
            title=title
        )
        logger.info(f"Ko'chirildi: {code} - {title}")
    
    logger.info("Migratsiya muvaffaqiyatli tugadi!")


if __name__ == "__main__":
    asyncio.run(migrate())
