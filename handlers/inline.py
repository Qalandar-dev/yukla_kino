from aiogram import Router, types
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from database import Database
import logging

logger = logging.getLogger(__name__)
router = Router()


@router.inline_query()
async def inline_query_handler(inline_query: InlineQuery, db: Database):
    """Inline qidiruv - @botnomi kino nomi"""
    query = inline_query.query.strip()
    
    if not query:
        # Agar query bo'sh bo'lsa, yangi kinolarni ko'rsatish
        movies = await db.get_new_movies(limit=5, offset=0)
    else:
        # Agar raqam bo'lsa, kod bo'yicha qidirish
        if query.isdigit():
            movie = await db.get_movie_by_code(query)
            movies = [movie] if movie else []
        else:
            # Nom bo'yicha qidirish
            movies = await db.search_movies_by_name(query, limit=5, offset=0)
    
    results = []
    
    for movie in movies:
        if not movie:
            continue
        
        title = f"{movie['title']} ({movie['year'] or 'N/A'})"
        description = f"🔑 Kod: {movie['code']}"
        
        result = InlineQueryResultArticle(
            id=movie['code'],
            title=title,
            description=description,
            input_message_content=InputTextMessageContent(
                message_text=f"🔑 {movie['code']}"
            )
        )
        results.append(result)
    
    if not results:
        results.append(
            InlineQueryResultArticle(
                id="no_results",
                title="❌ Kino topilmadi",
                description="Boshqa nom bilan qidiring",
                input_message_content=InputTextMessageContent(
                    message_text="❌ Kino topilmadi"
                )
            )
        )
    
    await inline_query.answer(results, cache_time=1)
