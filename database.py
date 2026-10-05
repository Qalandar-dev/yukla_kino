import aiosqlite
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_file="movies.db"):
        self.db_file = db_file

    async def init_db(self):
        """Baza va jadvallarni yaratish"""
        async with aiosqlite.connect(self.db_file) as db:
            # Users jadvali
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_blocked BOOLEAN DEFAULT 0
                )
            """)

            # Movies jadvali (kengaytirilgan)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS movies (
                    code TEXT PRIMARY KEY,
                    file_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    poster_url TEXT,
                    year INTEGER,
                    genre TEXT,
                    duration INTEGER,
                    description TEXT,
                    country TEXT,
                    language TEXT,
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    view_count INTEGER DEFAULT 0
                )
            """)

            # Favorites jadvali
            await db.execute("""
                CREATE TABLE IF NOT EXISTS favorites (
                    user_id INTEGER,
                    code TEXT,
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, code),
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (code) REFERENCES movies(code) ON DELETE CASCADE
                )
            """)

            # Watch later jadvali
            await db.execute("""
                CREATE TABLE IF NOT EXISTS watch_later (
                    user_id INTEGER,
                    code TEXT,
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, code),
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (code) REFERENCES movies(code) ON DELETE CASCADE
                )
            """)

            # Subscriptions jadvali (janr bo'yicha obuna)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    user_id INTEGER,
                    genre TEXT,
                    subscribed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, genre),
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)

            # FTS5 full-text search uchun virtual table
            await db.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS movies_fts USING fts5(
                    title,
                    content='movies',
                    content_rowid='rowid'
                )
            """)

            # FTS5 triggerlar
            await db.execute("""
                CREATE TRIGGER IF NOT EXISTS movies_ai AFTER INSERT ON movies BEGIN
                    INSERT INTO movies_fts(rowid, title) VALUES (new.rowid, new.title);
                END
            """)

            await db.execute("""
                CREATE TRIGGER IF NOT EXISTS movies_ad AFTER DELETE ON movies BEGIN
                    DELETE FROM movies_fts WHERE rowid = old.rowid;
                END
            """)

            await db.execute("""
                CREATE TRIGGER IF NOT EXISTS movies_au AFTER UPDATE ON movies BEGIN
                    UPDATE movies_fts SET title = new.title WHERE rowid = old.rowid;
                END
            """)

            await db.commit()
            logger.info("Database initialized")

    # ==================== USERS ====================

    async def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None):
        """Foydalanuvchi qo'shish yoki yangilash"""
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("""
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            """, (user_id, username, first_name, last_name))
            await db.commit()

    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Foydalanuvchi ma'lumotlarini olish"""
        async with aiosqlite.connect(self.db_file) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_total_users(self) -> int:
        """Barcha foydalanuvchilar soni"""
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0

    async def get_new_users_today(self) -> int:
        """Bugun qo'shilgan foydalanuvchilar soni"""
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM users WHERE DATE(joined_at) = DATE('now')"
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0

    # ==================== MOVIES ====================

    async def code_exists(self, code: str) -> bool:
        """Kod bazada bor-yo'qligini tekshirish"""
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute(
                "SELECT 1 FROM movies WHERE TRIM(code) = TRIM(?)", (str(code),)
            ) as cursor:
                result = await cursor.fetchone()
                return result is not None

    async def add_movie(
        self,
        code: str,
        file_id: str,
        title: str,
        poster_url: str = None,
        year: int = None,
        genre: str = None,
        duration: int = None,
        description: str = None,
        country: str = None,
        language: str = None
    ) -> bool:
        """Kino qo'shish"""
        try:
            async with aiosqlite.connect(self.db_file) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO movies
                    (code, file_id, title, poster_url, year, genre, duration, description, country, language)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (str(code).strip(), file_id.strip(), title.strip(),
                      poster_url, year, genre, duration, description, country, language))
                await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding movie: {e}")
            return False

    async def get_movie_by_code(self, code: str) -> Optional[Dict]:
        """Kodu bo'yicha kinoni qidirish"""
        async with aiosqlite.connect(self.db_file) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM movies WHERE TRIM(code) = TRIM(?)", (str(code).strip(),)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def search_movies_by_name(self, query: str, limit: int = 5, offset: int = 0) -> List[Dict]:
        """Nom bo'yicha qidirish (FTS5)"""
        async with aiosqlite.connect(self.db_file) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT m.* FROM movies m
                INNER JOIN movies_fts fts ON m.rowid = fts.rowid
                WHERE movies_fts MATCH ?
                ORDER BY m.added_at DESC
                LIMIT ? OFFSET ?
            """, (query, limit, offset)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_movies_by_genre(self, genre: str, limit: int = 5, offset: int = 0) -> List[Dict]:
        """Janr bo'yicha kinolar"""
        async with aiosqlite.connect(self.db_file) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM movies WHERE genre LIKE ?
                ORDER BY added_at DESC
                LIMIT ? OFFSET ?
            """, (f"%{genre}%", limit, offset)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_new_movies(self, limit: int = 5, offset: int = 0) -> List[Dict]:
        """Yangi kinolar"""
        async with aiosqlite.connect(self.db_file) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM movies ORDER BY added_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_top_movies(self, limit: int = 10, offset: int = 0) -> List[Dict]:
        """Eng ko'p ko'rilgan kinolar"""
        async with aiosqlite.connect(self.db_file) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM movies ORDER BY view_count DESC
                LIMIT ? OFFSET ?
            """, (limit, offset)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def increment_view_count(self, code: str):
        """Ko'rishlar sonini oshirish"""
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute(
                "UPDATE movies SET view_count = view_count + 1 WHERE code = ?",
                (str(code).strip(),)
            )
            await db.commit()

    async def update_movie(
        self,
        code: str,
        file_id: str = None,
        title: str = None,
        poster_url: str = None,
        year: int = None,
        genre: str = None,
        duration: int = None,
        description: str = None,
        country: str = None,
        language: str = None
    ) -> bool:
        """Kinoni yangilash"""
        try:
            async with aiosqlite.connect(self.db_file) as db:
                updates = []
                params = []
                
                if file_id:
                    updates.append("file_id = ?")
                    params.append(file_id)
                if title:
                    updates.append("title = ?")
                    params.append(title)
                if poster_url:
                    updates.append("poster_url = ?")
                    params.append(poster_url)
                if year:
                    updates.append("year = ?")
                    params.append(year)
                if genre:
                    updates.append("genre = ?")
                    params.append(genre)
                if duration:
                    updates.append("duration = ?")
                    params.append(duration)
                if description:
                    updates.append("description = ?")
                    params.append(description)
                if country:
                    updates.append("country = ?")
                    params.append(country)
                if language:
                    updates.append("language = ?")
                    params.append(language)
                
                if updates:
                    params.append(str(code).strip())
                    query = f"UPDATE movies SET {', '.join(updates)} WHERE code = ?"
                    await db.execute(query, params)
                    await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating movie: {e}")
            return False

    async def delete_movie(self, code: str) -> bool:
        """Kinoni o'chirish"""
        try:
            async with aiosqlite.connect(self.db_file) as db:
                await db.execute("DELETE FROM movies WHERE TRIM(code) = TRIM(?)", (str(code).strip(),))
                await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting movie: {e}")
            return False

    async def list_all_movies(self) -> List[Dict]:
        """Barcha kinolarni ko'rish"""
        async with aiosqlite.connect(self.db_file) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM movies ORDER BY added_at DESC") as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_total_movies(self) -> int:
        """Barcha kinolar soni"""
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute("SELECT COUNT(*) FROM movies") as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0

    # ==================== FAVORITES ====================

    async def add_favorite(self, user_id: int, code: str) -> bool:
        """Sevimlilarga qo'shish"""
        try:
            async with aiosqlite.connect(self.db_file) as db:
                await db.execute(
                    "INSERT OR IGNORE INTO favorites (user_id, code) VALUES (?, ?)",
                    (user_id, str(code).strip())
                )
                await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding favorite: {e}")
            return False

    async def remove_favorite(self, user_id: int, code: str) -> bool:
        """Sevimlilardan o'chirish"""
        try:
            async with aiosqlite.connect(self.db_file) as db:
                await db.execute(
                    "DELETE FROM favorites WHERE user_id = ? AND code = ?",
                    (user_id, str(code).strip())
                )
                await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error removing favorite: {e}")
            return False

    async def get_user_favorites(self, user_id: int) -> List[Dict]:
        """Foydalanuvchi sevimlilari"""
        async with aiosqlite.connect(self.db_file) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT m.* FROM movies m
                INNER JOIN favorites f ON m.code = f.code
                WHERE f.user_id = ?
                ORDER BY f.added_at DESC
            """, (user_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def is_favorite(self, user_id: int, code: str) -> bool:
        """Sevimlilarda bor-yo'qligini tekshirish"""
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute(
                "SELECT 1 FROM favorites WHERE user_id = ? AND code = ?",
                (user_id, str(code).strip())
            ) as cursor:
                result = await cursor.fetchone()
                return result is not None

    # ==================== WATCH LATER ====================

    async def add_watch_later(self, user_id: int, code: str) -> bool:
        """Keyin ko'raman ro'yxatiga qo'shish"""
        try:
            async with aiosqlite.connect(self.db_file) as db:
                await db.execute(
                    "INSERT OR IGNORE INTO watch_later (user_id, code) VALUES (?, ?)",
                    (user_id, str(code).strip())
                )
                await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding watch later: {e}")
            return False

    async def remove_watch_later(self, user_id: int, code: str) -> bool:
        """Keyin ko'raman ro'yxatidan o'chirish"""
        try:
            async with aiosqlite.connect(self.db_file) as db:
                await db.execute(
                    "DELETE FROM watch_later WHERE user_id = ? AND code = ?",
                    (user_id, str(code).strip())
                )
                await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error removing watch later: {e}")
            return False

    async def get_user_watch_later(self, user_id: int) -> List[Dict]:
        """Foydalanuvchining keyin ko'raman ro'yxati"""
        async with aiosqlite.connect(self.db_file) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT m.* FROM movies m
                INNER JOIN watch_later w ON m.code = w.code
                WHERE w.user_id = ?
                ORDER BY w.added_at DESC
            """, (user_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def is_watch_later(self, user_id: int, code: str) -> bool:
        """Keyin ko'raman ro'yxatida bor-yo'qligini tekshirish"""
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute(
                "SELECT 1 FROM watch_later WHERE user_id = ? AND code = ?",
                (user_id, str(code).strip())
            ) as cursor:
                result = await cursor.fetchone()
                return result is not None

    # ==================== SUBSCRIPTIONS ====================

    async def add_subscription(self, user_id: int, genre: str) -> bool:
        """Janr bo'yicha obuna"""
        try:
            async with aiosqlite.connect(self.db_file) as db:
                await db.execute(
                    "INSERT OR IGNORE INTO subscriptions (user_id, genre) VALUES (?, ?)",
                    (user_id, genre.strip())
                )
                await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding subscription: {e}")
            return False

    async def remove_subscription(self, user_id: int, genre: str) -> bool:
        """Obunadan chiqish"""
        try:
            async with aiosqlite.connect(self.db_file) as db:
                await db.execute(
                    "DELETE FROM subscriptions WHERE user_id = ? AND genre = ?",
                    (user_id, genre.strip())
                )
                await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error removing subscription: {e}")
            return False

    async def get_user_subscriptions(self, user_id: int) -> List[str]:
        """Foydalanuvchi obunalari"""
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute(
                "SELECT genre FROM subscriptions WHERE user_id = ?", (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def get_subscribers_by_genre(self, genre: str) -> List[int]:
        """Janr bo'yicha obunachilar"""
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute(
                "SELECT user_id FROM subscriptions WHERE genre = ?", (genre,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]