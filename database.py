import sqlite3
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_file="movies.db"):
        self.db_file = db_file
        self.init_db()

    def init_db(self):
        """Baza va jadvalni yaratish"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                code TEXT PRIMARY KEY,
                file_id TEXT NOT NULL,
                title TEXT NOT NULL,
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
        logger.info("Database initialized")

    def code_exists(self, code: str) -> bool:
        """Kod bazada bor-yo'qligini tekshirish"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM movies WHERE TRIM(code) = TRIM(?)", (str(code),))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def add_movie(self, code: str, file_id: str, title: str) -> bool:
        """Kino qo'shish"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO movies (code, file_id, title) VALUES (?, ?, ?)",
                (str(code).strip(), file_id.strip(), title.strip())
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error adding movie: {e}")
            return False

    def get_movie_by_code(self, code: str):
        """Kodu bo'yicha kinoni qidirish"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT file_id, title FROM movies WHERE TRIM(code) = TRIM(?)",
                (str(code).strip(),)
            )
            result = cursor.fetchone()
            conn.close()
            return result
        except Exception as e:
            logger.error(f"Error getting movie: {e}")
            return None

    def delete_movie(self, code: str) -> bool:
        """Kinoni o'chirish"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM movies WHERE TRIM(code) = TRIM(?)", (str(code).strip(),))
            deleted = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return deleted
        except Exception as e:
            logger.error(f"Error deleting movie: {e}")
            return False

    def list_all_movies(self):
        """Barcha kinolarni ko'rish"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT code, title, added_at FROM movies ORDER BY added_at DESC")
            results = cursor.fetchall()
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Error listing movies: {e}")
            return []