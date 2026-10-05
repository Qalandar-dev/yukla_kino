from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from database import Database
from keyboards.inline import (
    get_main_menu_keyboard,
    get_search_results_keyboard,
    get_category_keyboard,
    get_movie_keyboard
)
import logging

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, db: Database):
    """Start komandasi"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    # Foydalanuvchini bazaga qo'shish
    await db.add_user(user_id, username, first_name, last_name)
    
    await message.answer(
        "🎬 **Kino Botga xush kelibsiz!**\n\n"
        "Kino kodini yuboring yoki menyu orqali qidiring:",
        reply_markup=get_main_menu_keyboard()
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Yordam komandasi"""
    help_text = """
🎬 **Kino Bot yordami**

**Qidirish:**
- Kino kodini yuboring (masalan: 123)
- Kino nomini yozing
- Menyudan "Qidirish"ni bosing

**Menyu:**
- 🆕 Yangilar - eng so'nggi kinolar
- 🏆 Top 10 - eng ko'p ko'rilgan kinolar
- ❤️ Sevimlilar - sevimli kinolaringiz
- ⏰ Keyin ko'raman - keyin ko'rishni rejalashtirish

**Kino kartochkasi:**
- ❤️ Sevimlilarga qo'shish/olib tashlash
- ⏰ Keyin ko'raman ro'yxatiga qo'shish/olib tashlash
    """
    await message.answer(help_text, parse_mode="Markdown")


@router.callback_query(F.data == "search")
async def callback_search(callback: CallbackQuery):
    """Qidirishni boshlash"""
    await callback.message.edit_text(
        "🔍 Kino nomini yozing:",
        reply_markup=None
    )
    await callback.answer()


@router.callback_query(F.data == "new")
async def callback_new(callback: CallbackQuery, db: Database):
    """Yangi kinolar"""
    movies = await db.get_new_movies(limit=5, offset=0)
    
    if not movies:
        await callback.answer("❌ Bazada kinolar yo'q", show_alert=True)
        return
    
    text = "🆕 **Yangi kinolar:**\n\n"
    for movie in movies:
        text += f"🎬 {movie['title']} ({movie['year'] or 'N/A'})\n"
        text += f"🔑 Kod: `{movie['code']}`\n\n"
    
    # Sahifalash tugmalari
    total_movies = await db.get_new_movies(limit=1000, offset=0)
    total_pages = (len(total_movies) + 4) // 5 - 1
    
    keyboard = get_search_results_keyboard(movies, page=0, total_pages=total_pages, query="new", filter_type="new")
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("new_"))
async def callback_new_pagination(callback: CallbackQuery, db: Database):
    """Yangi kinolar sahifalash"""
    parts = callback.data.split("_")
    page = int(parts[1])
    
    movies = await db.get_new_movies(limit=5, offset=page * 5)
    
    if not movies:
        await callback.answer("❌ Boshqa natijalar yo'q", show_alert=True)
        return
    
    text = "🆕 **Yangi kinolar:**\n\n"
    for movie in movies:
        text += f"🎬 {movie['title']} ({movie['year'] or 'N/A'})\n"
        text += f"🔑 Kod: `{movie['code']}`\n\n"
    
    # Sahifalash tugmalari
    total_movies = await db.get_new_movies(limit=1000, offset=0)
    total_pages = (len(total_movies) + 4) // 5 - 1
    
    keyboard = get_search_results_keyboard(movies, page=page, total_pages=total_pages, query="new", filter_type="new")
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "top")
async def callback_top(callback: CallbackQuery, db: Database):
    """Top 10 kinolar"""
    movies = await db.get_top_movies(limit=10, offset=0)
    
    if not movies:
        await callback.answer("❌ Bazada kinolar yo'q", show_alert=True)
        return
    
    text = "🏆 **Top 10 eng ko'p ko'rilgan kinolar:**\n\n"
    for idx, movie in enumerate(movies, 1):
        text += f"{idx}. {movie['title']} ({movie['year'] or 'N/A'})\n"
        text += f"   👀 Ko'rishlar: {movie['view_count']}\n"
        text += f"   🔑 Kod: `{movie['code']}`\n\n"
    
    # Sahifalash tugmalari
    total_movies = await db.get_top_movies(limit=1000, offset=0)
    total_pages = (len(total_movies) + 9) // 10 - 1
    
    keyboard = get_search_results_keyboard(movies, page=0, total_pages=total_pages, query="top", filter_type="top")
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("top_"))
async def callback_top_pagination(callback: CallbackQuery, db: Database):
    """Top kinolar sahifalash"""
    parts = callback.data.split("_")
    page = int(parts[1])
    
    movies = await db.get_top_movies(limit=10, offset=page * 10)
    
    if not movies:
        await callback.answer("❌ Boshqa natijalar yo'q", show_alert=True)
        return
    
    text = "🏆 **Top eng ko'p ko'rilgan kinolar:**\n\n"
    start_idx = page * 10 + 1
    for idx, movie in enumerate(movies, start_idx):
        text += f"{idx}. {movie['title']} ({movie['year'] or 'N/A'})\n"
        text += f"   👀 Ko'rishlar: {movie['view_count']}\n"
        text += f"   🔑 Kod: `{movie['code']}`\n\n"
    
    # Sahifalash tugmalari
    total_movies = await db.get_top_movies(limit=1000, offset=0)
    total_pages = (len(total_movies) + 9) // 10 - 1
    
    keyboard = get_search_results_keyboard(movies, page=page, total_pages=total_pages, query="top", filter_type="top")
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "favorites")
async def callback_favorites(callback: CallbackQuery, db: Database):
    """Sevimlilar"""
    user_id = callback.from_user.id
    movies = await db.get_user_favorites(user_id)
    
    if not movies:
        await callback.answer("❌ Sevimlilar ro'yxati bo'sh", show_alert=True)
        return
    
    text = "❤️ **Sevimlilar:**\n\n"
    for movie in movies:
        text += f"🎬 {movie['title']} ({movie['year'] or 'N/A'})\n"
        text += f"🔑 Kod: `{movie['code']}`\n\n"
    
    keyboard = get_main_menu_keyboard()
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "watch_later")
async def callback_watch_later(callback: CallbackQuery, db: Database):
    """Keyin ko'raman ro'yxati"""
    user_id = callback.from_user.id
    movies = await db.get_user_watch_later(user_id)
    
    if not movies:
        await callback.answer("❌ Keyin ko'raman ro'yxati bo'sh", show_alert=True)
        return
    
    text = "⏰ **Keyin ko'raman:**\n\n"
    for movie in movies:
        text += f"🎬 {movie['title']} ({movie['year'] or 'N/A'})\n"
        text += f"🔑 Kod: `{movie['code']}`\n\n"
    
    keyboard = get_main_menu_keyboard()
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("genre_"))
async def callback_genre(callback: CallbackQuery, db: Database):
    """Janr bo'yicha kinolar"""
    genre = callback.data.split("_")[1]
    movies = await db.get_movies_by_genre(genre, limit=5, offset=0)
    
    if not movies:
        await callback.answer(f"❌ {genre} janrida kinolar yo'q", show_alert=True)
        return
    
    text = f"🎭 **{genre} janridagi kinolar:**\n\n"
    for movie in movies:
        text += f"🎬 {movie['title']} ({movie['year'] or 'N/A'})\n"
        text += f"🔑 Kod: `{movie['code']}`\n\n"
    
    keyboard = get_category_keyboard()
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "back")
async def callback_back(callback: CallbackQuery):
    """Orqaga"""
    keyboard = get_main_menu_keyboard()
    await callback.message.edit_text(
        "🎬 Asosiy menyu:",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("movie_"))
async def callback_movie(callback: CallbackQuery, db: Database):
    """Kino kartochkasini ko'rsatish"""
    code = callback.data.split("_")[1]
    movie = await db.get_movie_by_code(code)
    
    if not movie:
        await callback.answer("❌ Kino topilmadi", show_alert=True)
        return
    
    user_id = callback.from_user.id
    is_favorite = await db.is_favorite(user_id, code)
    is_watch_later = await db.is_watch_later(user_id, code)
    
    # Kino kartochkasi
    text = f"🎬 **{movie['title']}**\n\n"
    if movie['year']:
        text += f"📅 Yil: {movie['year']}\n"
    if movie['genre']:
        text += f"🎭 Janr: {movie['genre']}\n"
    if movie['duration']:
        text += f"⏱ Davomiyligi: {movie['duration']} daqiqa\n"
    if movie['country']:
        text += f"🌍 Davlat: {movie['country']}\n"
    if movie['language']:
        text += f"🗣 Til: {movie['language']}\n"
    text += f"👀 Ko'rishlar: {movie['view_count']}\n"
    text += f"🔑 Kod: `{movie['code']}`\n"
    
    if movie['description']:
        text += f"\n📝 **Mazmun:**\n{movie['description']}\n"
    
    keyboard = get_movie_keyboard(code, user_id, is_favorite, is_watch_later)
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("fav_"))
async def callback_favorite(callback: CallbackQuery, db: Database):
    """Sevimlilarga qo'shish/olib tashlash"""
    code = callback.data.split("_")[1]
    user_id = callback.from_user.id
    
    is_favorite = await db.is_favorite(user_id, code)
    
    if is_favorite:
        await db.remove_favorite(user_id, code)
        await callback.answer("❤️ Sevimlilardan olib tashlandi")
    else:
        await db.add_favorite(user_id, code)
        await callback.answer("🤍 Sevimlilarga qo'shildi")
    
    # Tugmalarni yangilash
    movie = await db.get_movie_by_code(code)
    if movie:
        is_favorite = await db.is_favorite(user_id, code)
        is_watch_later = await db.is_watch_later(user_id, code)
        keyboard = get_movie_keyboard(code, user_id, is_favorite, is_watch_later)
        await callback.message.edit_reply_markup(reply_markup=keyboard)


@router.callback_query(F.data.startswith("watch_"))
async def callback_watch_later_toggle(callback: CallbackQuery, db: Database):
    """Keyin ko'raman ro'yxatiga qo'shish/olib tashlash"""
    code = callback.data.split("_")[1]
    user_id = callback.from_user.id
    
    is_watch_later = await db.is_watch_later(user_id, code)
    
    if is_watch_later:
        await db.remove_watch_later(user_id, code)
        await callback.answer("🗑 Keyin ko'ramandan olib tashlandi")
    else:
        await db.add_watch_later(user_id, code)
        await callback.answer("⏰ Keyin ko'ramanga qo'shildi")
    
    # Tugmalarni yangilash
    movie = await db.get_movie_by_code(code)
    if movie:
        is_favorite = await db.is_favorite(user_id, code)
        is_watch_later = await db.is_watch_later(user_id, code)
        keyboard = get_movie_keyboard(code, user_id, is_favorite, is_watch_later)
        await callback.message.edit_reply_markup(reply_markup=keyboard)


@router.callback_query(F.data.startswith("search_"))
async def callback_search_pagination(callback: CallbackQuery, db: Database):
    """Qidiruv sahifalash"""
    parts = callback.data.split("_")
    query = parts[1]
    page = int(parts[2])
    
    movies = await db.search_movies_by_name(query, limit=5, offset=page * 5)
    
    if not movies:
        await callback.answer("❌ Boshqa natijalar yo'q", show_alert=True)
        return
    
    response_text = f"🔍 **Qidiruv natijalari ({query}):**\n\n"
    for movie in movies:
        response_text += f"🎬 {movie['title']} ({movie['year'] or 'N/A'})\n"
        response_text += f"🔑 Kod: `{movie['code']}`\n\n"
    
    # Sahifalash tugmalari
    total_movies = await db.search_movies_by_name(query, limit=1000, offset=0)
    total_pages = (len(total_movies) + 4) // 5 - 1
    
    keyboard = get_search_results_keyboard(movies, page=page, total_pages=total_pages, query=query, filter_type="search")
    await callback.message.edit_text(response_text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()


@router.message(F.text)
async def handle_text(message: Message, db: Database):
    """Matnni qayta ishlash (kod yoki nom bo'yicha qidirish)"""
    text = message.text.strip()
    
    # Agar komanda bo'lsa, e'tibor bermaslik
    if text.startswith("/"):
        return
    
    # Agar faqat raqam bo'lsa, kod bo'yicha qidirish
    if text.isdigit():
        movie = await db.get_movie_by_code(text)
        if movie:
            # Ko'rishlar sonini oshirish
            await db.increment_view_count(text)
            
            user_id = message.from_user.id
            is_favorite = await db.is_favorite(user_id, text)
            is_watch_later = await db.is_watch_later(user_id, text)
            
            # Kino kartochkasi
            text_response = f"🎬 **{movie['title']}**\n\n"
            if movie['year']:
                text_response += f"📅 Yil: {movie['year']}\n"
            if movie['genre']:
                text_response += f"🎭 Janr: {movie['genre']}\n"
            if movie['duration']:
                text_response += f"⏱ Davomiyligi: {movie['duration']} daqiqa\n"
            if movie['country']:
                text_response += f"🌍 Davlat: {movie['country']}\n"
            if movie['language']:
                text_response += f"🗣 Til: {movie['language']}\n"
            text_response += f"👀 Ko'rishlar: {movie['view_count']}\n"
            text_response += f"🔑 Kod: `{movie['code']}`\n"
            
            if movie['description']:
                text_response += f"\n📝 **Mazmun:**\n{movie['description']}\n"
            
            keyboard = get_movie_keyboard(text, user_id, is_favorite, is_watch_later)
            
            try:
                await message.answer_video(
                    movie['file_id'],
                    caption=text_response,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
            except Exception as e:
                logger.error(f"Video yuborishda xatolik: {e}")
                await message.answer(text_response, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await message.answer("❌ Kino topilmadi!")
    else:
        # Nom bo'yicha qidirish (FTS5)
        movies = await db.search_movies_by_name(text, limit=5, offset=0)
        
        if movies:
            response_text = f"🔍 **Qidiruv natijalari ({text}):**\n\n"
            for movie in movies:
                response_text += f"🎬 {movie['title']} ({movie['year'] or 'N/A'})\n"
                response_text += f"🔑 Kod: `{movie['code']}`\n\n"
            
            keyboard = get_search_results_keyboard(movies, page=0, total_pages=0, query=text, filter_type="search")
            await message.answer(response_text, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await message.answer(
                f"❌ '{text}' bo'yicha kino topilmadi.\n\n"
                "Boshqa nom bilan qidiring yoki kodni yuboring."
            )
