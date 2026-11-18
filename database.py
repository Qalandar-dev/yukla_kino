import aiosqlite
import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

# Kino jadvalidagi tahrirlash mumkin bo'lgan ustunlar
EDITABLE_FIELDS = {
    "title", "poster_url", "year", "genre", "duration",
    "description", "country", "language", "file_id", "file_type",
}


def build_fts_query(text: str) -> str:
    """Foydalanuvchi matnidan xavfsiz FTS5 so'rovini yasash.

    Har bir so'z qo'shtirnoq ichiga olinadi (maxsus belgilar xato bermasligi uchun)
    va prefiks qidiruv uchun oxiriga * qo'shiladi: "spider"* "man"*
    """
    tokens = []
    for raw in text.replace('"', " ").split():
        word = "".join(ch for ch in raw if ch.isalnum() or ch in "'")
        if word:
            tokens.append(f'"{word}"*')
    return " ".join(tokens)


class Database:
    def __init__(self, db_file: str = "movies.db"):
        self.db_file = db_file

    def _connect(self):
        return aiosqlite.connect(self.db_file)

    async def init_db(self):
        """Baza va jadvallarni yaratish (hamda eski bazani yangilash)"""
        async with self._connect() as db:
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
                    view_count INTEGER DEFAULT 0,
                    file_type TEXT DEFAULT 'video'
                )
            """)

            # Eski bazalar uchun yangi ustun
            async with db.execute("PRAGMA table_info(movies)") as cursor:
                columns = {row[1] for row in await cursor.fetchall()}
            if "file_type" not in columns:
                await db.execute("ALTER TABLE movies ADD COLUMN file_type TEXT DEFAULT 'video'")

            await db.execute("""
                CREATE TABLE IF NOT EXISTS favorites (
                    user_id INTEGER,
                    code TEXT,
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, code)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS watch_later (
                    user_id INTEGER,
                    code TEXT,
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, code)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    user_id INTEGER,
                    genre TEXT,
                    subscribed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, genre)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            await db.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS movies_fts USING fts5(
                    title,
                    content='movies',
                    content_rowid='rowid'
                )
            """)

            # External-content FTS5 uchun to'g'ri triggerlar.
            # Eski (noto'g'ri) triggerlar o'chirilib, qayta yaratiladi.
            for name in ("movies_ai", "movies_ad", "movies_au"):
                await db.execute(f"DROP TRIGGER IF EXISTS {name}")

            await db.execute("""
                CREATE TRIGGER movies_ai AFTER INSERT ON movies BEGIN
                    INSERT INTO movies_fts(rowid, title) VALUES (new.rowid, new.title);
                END
            """)
            await db.execute("""
                CREATE TRIGGER movies_ad AFTER DELETE ON movies BEGIN
                    INSERT INTO movies_fts(movies_fts, rowid, title)
                    VALUES ('delete', old.rowid, old.title);
                END
            """)
            await db.execute("""
                CREATE TRIGGER movies_au AFTER UPDATE ON movies BEGIN
                    INSERT INTO movies_fts(movies_fts, rowid, title)
                    VALUES ('delete', old.rowid, old.title);
                    INSERT INTO movies_fts(rowid, title) VALUES (new.rowid, new.title);
                END
            """)

            # Indeksni movies jadvalidan qayta qurish (eski buzilgan indeksni tuzatadi)
            await db.execute("INSERT INTO movies_fts(movies_fts) VALUES ('rebuild')")

            await db.commit()
            logger.info("Database initialized")

    # ==================== SETTINGS ====================

    async def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        async with self._connect() as db:
            async with db.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else default

    async def set_setting(self, key: str, value: str):
        async with self._connect() as db:
            await db.execute("""
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (key, value))
            await db.commit()

    # ==================== USERS ====================

    async def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None):
        """Foydalanuvchi qo'shish yoki yangilash (joined_at saqlanib qoladi)"""
        async with self._connect() as db:
            await db.execute("""
                INSERT INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    is_blocked = 0
            """, (user_id, username, first_name, last_name))
            await db.commit()

    async def get_user(self, user_id: int) -> Optional[Dict]:
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_all_user_ids(self) -> List[int]:
        async with self._connect() as db:
            async with db.execute("SELECT user_id FROM users WHERE is_blocked = 0") as cursor:
                return [row[0] for row in await cursor.fetchall()]

    async def set_user_blocked(self, user_id: int, blocked: bool = True):
        async with self._connect() as db:
            await db.execute("UPDATE users SET is_blocked = ? WHERE user_id = ?", (int(blocked), user_id))
            await db.commit()

    async def get_total_users(self) -> int:
        async with self._connect() as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0

    async def get_blocked_users(self) -> int:
        async with self._connect() as db:
            async with db.execute("SELECT COUNT(*) FROM users WHERE is_blocked = 1") as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0

    async def get_new_users_today(self) -> int:
        async with self._connect() as db:
            async with db.execute(
                "SELECT COUNT(*) FROM users WHERE DATE(joined_at) = DATE('now')"
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0

    # ==================== MOVIES ====================

    async def code_exists(self, code: str) -> bool:
        async with self._connect() as db:
            async with db.execute("SELECT 1 FROM movies WHERE code = ?", (str(code).strip(),)) as cursor:
                return await cursor.fetchone() is not None

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
        language: str = None,
        file_type: str = "video",
    ) -> bool:
        """Kino qo'shish yoki mavjudini yangilash (ko'rishlar soni saqlanadi)"""
        try:
            async with self._connect() as db:
                await db.execute("""
                    INSERT INTO movies
                    (code, file_id, title, poster_url, year, genre, duration,
                     description, country, language, file_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(code) DO UPDATE SET
                        file_id = excluded.file_id,
                        title = excluded.title,
                        poster_url = excluded.poster_url,
                        year = excluded.year,
                        genre = excluded.genre,
                        duration = excluded.duration,
                        description = excluded.description,
                        country = excluded.country,
                        language = excluded.language,
                        file_type = excluded.file_type
                """, (str(code).strip(), file_id.strip(), title.strip(),
                      poster_url, year, genre, duration, description, country, language, file_type))
                await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding movie: {e}")
            return False

    async def get_movie_by_code(self, code: str) -> Optional[Dict]:
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM movies WHERE code = ?", (str(code).strip(),)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def search_movies_by_name(self, query: str, limit: int = 5, offset: int = 0) -> List[Dict]:
        """Nom bo'yicha qidirish (FTS5, xavfsiz + prefiks), topilmasa LIKE bilan"""
        fts_query = build_fts_query(query)
        if not fts_query:
            return []
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            try:
                async with db.execute("""
                    SELECT m.* FROM movies_fts
                    JOIN movies m ON m.rowid = movies_fts.rowid
                    WHERE movies_fts MATCH ?
                    ORDER BY rank
                    LIMIT ? OFFSET ?
                """, (fts_query, limit, offset)) as cursor:
                    rows = await cursor.fetchall()
                    if rows:
                        return [dict(row) for row in rows]
            except aiosqlite.Error as e:
                logger.warning(f"FTS search error: {e}")

            async with db.execute("""
                SELECT * FROM movies WHERE title LIKE ? COLLATE NOCASE
                ORDER BY added_at DESC LIMIT ? OFFSET ?
            """, (f"%{query.strip()}%", limit, offset)) as cursor:
                return [dict(row) for row in await cursor.fetchall()]

    async def count_search_results(self, query: str) -> int:
        fts_query = build_fts_query(query)
        if not fts_query:
            return 0
        async with self._connect() as db:
            try:
                async with db.execute(
                    "SELECT COUNT(*) FROM movies_fts WHERE movies_fts MATCH ?", (fts_query,)
                ) as cursor:
                    count = (await cursor.fetchone())[0]
                    if count:
                        return count
            except aiosqlite.Error:
                pass
            async with db.execute(
                "SELECT COUNT(*) FROM movies WHERE title LIKE ? COLLATE NOCASE", (f"%{query.strip()}%",)
            ) as cursor:
                return (await cursor.fetchone())[0]

    async def get_movies_by_genre(self, genre: str, limit: int = 5, offset: int = 0) -> List[Dict]:
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM movies WHERE genre LIKE ? COLLATE NOCASE
                ORDER BY added_at DESC
                LIMIT ? OFFSET ?
            """, (f"%{genre}%", limit, offset)) as cursor:
                return [dict(row) for row in await cursor.fetchall()]

    async def count_movies_by_genre(self, genre: str) -> int:
        async with self._connect() as db:
            async with db.execute(
                "SELECT COUNT(*) FROM movies WHERE genre LIKE ? COLLATE NOCASE", (f"%{genre}%",)
            ) as cursor:
                return (await cursor.fetchone())[0]

    async def get_new_movies(self, limit: int = 5, offset: int = 0) -> List[Dict]:
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM movies ORDER BY added_at DESC, rowid DESC
                LIMIT ? OFFSET ?
            """, (limit, offset)) as cursor:
                return [dict(row) for row in await cursor.fetchall()]

    async def get_top_movies(self, limit: int = 10, offset: int = 0) -> List[Dict]:
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM movies ORDER BY view_count DESC, added_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset)) as cursor:
                return [dict(row) for row in await cursor.fetchall()]

    async def get_random_movie(self) -> Optional[Dict]:
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM movies ORDER BY RANDOM() LIMIT 1") as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def increment_view_count(self, code: str):
        async with self._connect() as db:
            await db.execute(
                "UPDATE movies SET view_count = view_count + 1 WHERE code = ?",
                (str(code).strip(),)
            )
            await db.commit()

    async def update_movie_field(self, code: str, field: str, value) -> bool:
        """Kinoning bitta maydonini yangilash. Kino topilmasa False."""
        if field not in EDITABLE_FIELDS:
            raise ValueError(f"Noma'lum maydon: {field}")
        async with self._connect() as db:
            cursor = await db.execute(
                f"UPDATE movies SET {field} = ? WHERE code = ?", (value, str(code).strip())
            )
            await db.commit()
            return cursor.rowcount > 0

    async def delete_movie(self, code: str) -> bool:
        """Kinoni o'chirish. Kino topilmasa False qaytaradi."""
        code = str(code).strip()
        try:
            async with self._connect() as db:
                cursor = await db.execute("DELETE FROM movies WHERE code = ?", (code,))
                await db.execute("DELETE FROM favorites WHERE code = ?", (code,))
                await db.execute("DELETE FROM watch_later WHERE code = ?", (code,))
                await db.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting movie: {e}")
            return False

    async def list_all_movies(self) -> List[Dict]:
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM movies ORDER BY added_at DESC") as cursor:
                return [dict(row) for row in await cursor.fetchall()]

    async def get_total_movies(self) -> int:
        async with self._connect() as db:
            async with db.execute("SELECT COUNT(*) FROM movies") as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0

    async def get_total_views(self) -> int:
        async with self._connect() as db:
            async with db.execute("SELECT COALESCE(SUM(view_count), 0) FROM movies") as cursor:
                return (await cursor.fetchone())[0]

    # ==================== FAVORITES ====================

    async def add_favorite(self, user_id: int, code: str) -> bool:
        try:
            async with self._connect() as db:
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
        try:
            async with self._connect() as db:
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
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT m.* FROM movies m
                INNER JOIN favorites f ON m.code = f.code
                WHERE f.user_id = ?
                ORDER BY f.added_at DESC
            """, (user_id,)) as cursor:
                return [dict(row) for row in await cursor.fetchall()]

    async def is_favorite(self, user_id: int, code: str) -> bool:
        async with self._connect() as db:
            async with db.execute(
                "SELECT 1 FROM favorites WHERE user_id = ? AND code = ?",
                (user_id, str(code).strip())
            ) as cursor:
                return await cursor.fetchone() is not None

    # ==================== WATCH LATER ====================

    async def add_watch_later(self, user_id: int, code: str) -> bool:
        try:
            async with self._connect() as db:
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
        try:
            async with self._connect() as db:
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
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT m.* FROM movies m
                INNER JOIN watch_later w ON m.code = w.code
                WHERE w.user_id = ?
                ORDER BY w.added_at DESC
            """, (user_id,)) as cursor:
                return [dict(row) for row in await cursor.fetchall()]

    async def is_watch_later(self, user_id: int, code: str) -> bool:
        async with self._connect() as db:
            async with db.execute(
                "SELECT 1 FROM watch_later WHERE user_id = ? AND code = ?",
                (user_id, str(code).strip())
            ) as cursor:
                return await cursor.fetchone() is not None

    # ==================== SUBSCRIPTIONS (janr bo'yicha) ====================

    async def add_subscription(self, user_id: int, genre: str) -> bool:
        try:
            async with self._connect() as db:
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
        try:
            async with self._connect() as db:
                await db.execute(
                    "DELETE FROM subscriptions WHERE user_id = ? AND genre = ?",
                    (user_id, genre.strip())
                )
                await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error removing subscription: {e}")
            return False

    async def is_subscribed(self, user_id: int, genre: str) -> bool:
        async with self._connect() as db:
            async with db.execute(
                "SELECT 1 FROM subscriptions WHERE user_id = ? AND genre = ?", (user_id, genre)
            ) as cursor:
                return await cursor.fetchone() is not None

    async def get_user_subscriptions(self, user_id: int) -> List[str]:
        async with self._connect() as db:
            async with db.execute(
                "SELECT genre FROM subscriptions WHERE user_id = ?", (user_id,)
            ) as cursor:
                return [row[0] for row in await cursor.fetchall()]

    async def get_subscribers_for_genres(self, genre_text: str) -> List[int]:
        """Kino janrlari matniga mos keladigan obunachilar (takrorlarsiz)"""
        if not genre_text:
            return []
        async with self._connect() as db:
            async with db.execute("""
                SELECT DISTINCT s.user_id FROM subscriptions s
                JOIN users u ON u.user_id = s.user_id
                WHERE u.is_blocked = 0 AND ? LIKE '%' || s.genre || '%' COLLATE NOCASE
            """, (genre_text,)) as cursor:
                return [row[0] for row in await cursor.fetchall()]
