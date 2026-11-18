"""Umumiy yordamchi funksiyalar: matn formatlash va kinoni yuborish."""
import logging
from html import escape
from typing import Dict, List, Optional

from aiogram.types import Message, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

PAGE_SIZE = 5
CAPTION_LIMIT = 1024

# (kalit, tugma matni, TMDB dagi inglizcha janr nomi)
GENRES = [
    ("drama", "🎭 Drama", "Drama"),
    ("action", "💥 Jangari", "Action"),
    ("comedy", "😂 Komediya", "Comedy"),
    ("horror", "😱 Qo'rqinchli", "Horror"),
    ("fantasy", "🔮 Fantastika", "Fantasy"),
    ("romance", "💕 Romantik", "Romance"),
    ("scifi", "🚀 Ilmiy-fantastik", "Science Fiction"),
    ("thriller", "🔪 Triller", "Thriller"),
    ("animation", "🧸 Multfilm", "Animation"),
    ("adventure", "🗺 Sarguzasht", "Adventure"),
    ("crime", "🕵️ Kriminal", "Crime"),
    ("family", "👨‍👩‍👧 Oilaviy", "Family"),
]
GENRE_BY_KEY = {key: (label, name) for key, label, name in GENRES}


def total_pages(count: int, page_size: int = PAGE_SIZE) -> int:
    return max(1, (count + page_size - 1) // page_size)


def movie_line(movie: Dict, index: Optional[int] = None) -> str:
    prefix = f"{index}. " if index is not None else "🎬 "
    year = movie.get("year") or "—"
    return (
        f"{prefix}{escape(movie['title'])} ({year})\n"
        f"🔑 Kod: <code>{escape(str(movie['code']))}</code>\n"
    )


def movie_list_text(header: str, movies: List[Dict], start_index: Optional[int] = None) -> str:
    lines = [header, ""]
    for i, movie in enumerate(movies):
        idx = start_index + i if start_index is not None else None
        lines.append(movie_line(movie, idx))
    return "\n".join(lines)


def movie_card(movie: Dict, limit: int = 4096) -> str:
    """Kino kartochkasi matni (HTML). limit — Telegram cheklovi."""
    text = f"🎬 <b>{escape(movie['title'])}</b>\n\n"
    if movie.get("year"):
        text += f"📅 Yil: {movie['year']}\n"
    if movie.get("genre"):
        text += f"🎭 Janr: {escape(movie['genre'])}\n"
    if movie.get("duration"):
        text += f"⏱ Davomiyligi: {movie['duration']} daqiqa\n"
    if movie.get("country"):
        text += f"🌍 Davlat: {escape(movie['country'])}\n"
    if movie.get("language"):
        text += f"🗣 Til: {escape(movie['language'])}\n"
    text += f"👀 Ko'rishlar: {movie.get('view_count') or 0}\n"
    text += f"🔑 Kod: <code>{escape(str(movie['code']))}</code>\n"

    description = movie.get("description")
    if description:
        header = "\n📝 <b>Mazmun:</b>\n"
        room = limit - len(text) - len(header) - 1
        if room > 20:
            if len(description) > room:
                description = description[: room - 1].rstrip() + "…"
            text += header + escape(description)
    return text


async def send_movie(message: Message, movie: Dict, keyboard: InlineKeyboardMarkup):
    """Kino faylini kartochka bilan yuborish (video / hujjat / animatsiya)"""
    caption = movie_card(movie, CAPTION_LIMIT)
    file_type = movie.get("file_type") or "video"
    senders = {
        "video": message.answer_video,
        "document": message.answer_document,
        "animation": message.answer_animation,
    }
    sender = senders.get(file_type, message.answer_video)
    try:
        await sender(movie["file_id"], caption=caption, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Kino yuborishda xatolik (kod={movie['code']}): {e}")
        await message.answer(
            movie_card(movie) + "\n\n⚠️ Fayl yuborib bo'lmadi, adminga xabar bering.",
            reply_markup=keyboard,
        )
