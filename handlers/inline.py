import logging
from html import escape

from aiogram import Router, Bot
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from database import Database

logger = logging.getLogger(__name__)
router = Router()


@router.inline_query()
async def inline_query_handler(inline_query: InlineQuery, db: Database, bot: Bot):
    """Inline qidiruv: @botnomi kino nomi yoki kodi"""
    query = inline_query.query.strip()

    if not query:
        movies = await db.get_new_movies(limit=10)
    elif query.isdigit():
        movie = await db.get_movie_by_code(query)
        movies = [movie] if movie else []
        if not movies:
            movies = await db.search_movies_by_name(query, limit=10)
    else:
        movies = await db.search_movies_by_name(query, limit=10)

    bot_username = (await bot.me()).username
    results = []
    for movie in movies:
        code = movie["code"]
        year = movie.get("year") or "—"
        link = f"https://t.me/{bot_username}?start={code}"
        text = (
            f"🎬 <b>{escape(movie['title'])}</b> ({year})\n"
            f"🔑 Kod: <code>{escape(code)}</code>\n\n"
            f"👉 Ko'rish uchun: @{bot_username}"
        )
        results.append(InlineQueryResultArticle(
            id=f"m{code}"[:64],
            title=f"{movie['title']} ({year})",
            description=f"🔑 Kod: {code}" + (f" • {movie['genre']}" if movie.get("genre") else ""),
            thumbnail_url=movie.get("poster_url") or None,
            input_message_content=InputTextMessageContent(message_text=text, parse_mode="HTML"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="▶️ Botda ko'rish", url=link)]
            ]),
        ))

    if not results:
        results.append(InlineQueryResultArticle(
            id="no_results",
            title="❌ Kino topilmadi",
            description="Boshqa nom bilan qidiring",
            input_message_content=InputTextMessageContent(message_text="❌ Kino topilmadi"),
        ))

    await inline_query.answer(results, cache_time=5, is_personal=False)
