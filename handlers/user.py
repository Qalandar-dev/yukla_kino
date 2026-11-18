import logging

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup

from database import Database
from keyboards.inline import (
    get_main_menu_keyboard,
    get_movie_list_keyboard,
    get_category_keyboard,
    get_movie_keyboard,
    genre_subscribe_row,
)
from middlewares.channel_check import CHECK_CALLBACK, is_subscribed
from utils import PAGE_SIZE, GENRE_BY_KEY, movie_list_text, send_movie, total_pages
from html import escape

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(F.chat.type == "private")

WELCOME_TEXT = (
    "🎬 <b>Kino Botga xush kelibsiz!</b>\n\n"
    "Kino kodini yoki nomini yuboring, yoki menyudan foydalaning:"
)

HELP_TEXT = """🎬 <b>Kino Bot yordami</b>

<b>Qidirish:</b>
• Kino kodini yuboring (masalan: <code>123</code>)
• Kino nomini yozing (to'liq bo'lishi shart emas)
• Istalgan chatda: <code>@botnomi kino nomi</code>

<b>Menyu:</b>
• 🆕 Yangilar — eng so'nggi kinolar
• 🏆 Top — eng ko'p ko'rilgan kinolar
• 🎭 Janrlar — janr bo'yicha ko'rish va yangi kinolarga obuna
• 🎲 Tasodifiy — nima ko'rishni bilmasangiz (/random)
• ❤️ Sevimlilar, ⏰ Keyin ko'raman

<b>Kino kartochkasi:</b>
• ❤️ Sevimlilarga / ⏰ Keyin ko'ramanga qo'shish
• 📤 Do'stga ulashish"""


async def show(callback: CallbackQuery, text: str, keyboard: InlineKeyboardMarkup = None):
    """Xabarni tahrirlash; imkoni bo'lmasa (masalan, video xabar) yangisini yuborish"""
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            return
        await callback.message.answer(text, reply_markup=keyboard)


async def open_movie(message: Message, db: Database, code: str, user_id: int) -> bool:
    """Kinoni topib, faylini kartochka bilan yuborish"""
    movie = await db.get_movie_by_code(code)
    if not movie:
        return False
    await db.increment_view_count(movie["code"])
    movie["view_count"] = (movie.get("view_count") or 0) + 1
    keyboard = get_movie_keyboard(
        movie["code"],
        await db.is_favorite(user_id, movie["code"]),
        await db.is_watch_later(user_id, movie["code"]),
    )
    await send_movie(message, movie, keyboard)
    return True


# ==================== KOMANDALAR ====================

@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, db: Database, state: FSMContext):
    """/start va /start <kod> (ulashilgan havola orqali)"""
    await state.clear()
    user = message.from_user
    await db.add_user(user.id, user.username, user.first_name, user.last_name)

    code = (command.args or "").strip()
    if code:
        if await open_movie(message, db, code, user.id):
            return
        await message.answer("❌ Bu kod bo'yicha kino topilmadi.")

    await message.answer(WELCOME_TEXT, reply_markup=get_main_menu_keyboard())


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(HELP_TEXT)


@router.message(Command("random"))
async def cmd_random(message: Message, db: Database):
    movie = await db.get_random_movie()
    if not movie:
        await message.answer("📭 Bazada hali kinolar yo'q.")
        return
    await open_movie(message, db, movie["code"], message.from_user.id)


# ==================== MENYU ====================

@router.callback_query(F.data == "noop")
async def callback_noop(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data == CHECK_CALLBACK)
async def callback_check_sub(callback: CallbackQuery, db: Database):
    if not await is_subscribed(callback.bot, callback.from_user.id):
        await callback.answer("❌ Siz hali kanalga obuna bo'lmagansiz!", show_alert=True)
        return
    user = callback.from_user
    await db.add_user(user.id, user.username, user.first_name, user.last_name)
    await callback.answer("✅ Rahmat! Endi botdan foydalanishingiz mumkin.")
    await show(callback, WELCOME_TEXT, get_main_menu_keyboard())


@router.callback_query(F.data == "menu")
async def callback_menu(callback: CallbackQuery):
    await show(callback, WELCOME_TEXT, get_main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "search")
async def callback_search(callback: CallbackQuery):
    await show(callback, "🔍 Kino nomini yoki kodini yozing:")
    await callback.answer()


@router.callback_query(F.data == "random")
async def callback_random(callback: CallbackQuery, db: Database):
    movie = await db.get_random_movie()
    if not movie:
        await callback.answer("📭 Bazada hali kinolar yo'q", show_alert=True)
        return
    await callback.answer("🎲")
    await open_movie(callback.message, db, movie["code"], callback.from_user.id)


@router.callback_query(F.data == "genres")
async def callback_genres(callback: CallbackQuery, db: Database):
    subs = await db.get_user_subscriptions(callback.from_user.id)
    text = "🎭 <b>Janrni tanlang:</b>"
    if subs:
        text += "\n\n🔔 Obunalaringiz: " + escape(", ".join(subs))
    await show(callback, text, get_category_keyboard())
    await callback.answer()


# ==================== RO'YXATLAR ====================

LIST_TITLES = {
    "new": "🆕 <b>Yangi kinolar:</b>",
    "top": "🏆 <b>Eng ko'p ko'rilgan kinolar:</b>",
    "fav": "❤️ <b>Sevimlilar:</b>",
    "wl": "⏰ <b>Keyin ko'raman:</b>",
}
EMPTY_TEXTS = {
    "new": "📭 Bazada hali kinolar yo'q",
    "top": "📭 Bazada hali kinolar yo'q",
    "fav": "❤️ Sevimlilar ro'yxati bo'sh",
    "wl": "⏰ Keyin ko'raman ro'yxati bo'sh",
    "srch": "❌ Boshqa natijalar yo'q",
}


@router.callback_query(F.data.startswith("list:"))
async def callback_list(callback: CallbackQuery, db: Database, state: FSMContext):
    _, kind, page_str = callback.data.split(":")
    page = max(0, int(page_str))
    offset = page * PAGE_SIZE
    user_id = callback.from_user.id

    if kind == "new":
        count = await db.get_total_movies()
        movies = await db.get_new_movies(PAGE_SIZE, offset)
    elif kind == "top":
        count = await db.get_total_movies()
        movies = await db.get_top_movies(PAGE_SIZE, offset)
    elif kind in ("fav", "wl"):
        all_movies = await (db.get_user_favorites(user_id) if kind == "fav" else db.get_user_watch_later(user_id))
        count = len(all_movies)
        movies = all_movies[offset:offset + PAGE_SIZE]
    elif kind == "srch":
        query = (await state.get_data()).get("search_query")
        if not query:
            await callback.answer("⌛ Qidiruv eskirgan, qaytadan yozing", show_alert=True)
            return
        count = await db.count_search_results(query)
        movies = await db.search_movies_by_name(query, PAGE_SIZE, offset)
    else:
        await callback.answer()
        return

    if not movies:
        await callback.answer(EMPTY_TEXTS[kind], show_alert=True)
        return

    if kind == "srch":
        header = f"🔍 <b>Qidiruv natijalari ({escape(query)}):</b>"
    else:
        header = LIST_TITLES[kind]
    start_index = offset + 1 if kind == "top" else None
    text = movie_list_text(header, movies, start_index)
    keyboard = get_movie_list_keyboard(movies, f"list:{kind}", page, total_pages(count))
    await show(callback, text, keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("genre:"))
async def callback_genre(callback: CallbackQuery, db: Database):
    _, key, page_str = callback.data.split(":")
    if key not in GENRE_BY_KEY:
        await callback.answer()
        return
    label, genre = GENRE_BY_KEY[key]
    page = max(0, int(page_str))

    subscribed = await db.is_subscribed(callback.from_user.id, genre)
    movies = await db.get_movies_by_genre(genre, PAGE_SIZE, page * PAGE_SIZE)
    count = await db.count_movies_by_genre(genre)

    if movies:
        text = movie_list_text(f"{label} <b>janridagi kinolar:</b>", movies)
    else:
        text = f"{label}\n\n📭 Bu janrda hozircha kinolar yo'q."
    keyboard = get_movie_list_keyboard(
        movies, f"genre:{key}", page, total_pages(count),
        extra_rows=[genre_subscribe_row(key, subscribed)],
        back="genres",
    )
    await show(callback, text, keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("gsub:"))
async def callback_genre_subscribe(callback: CallbackQuery, db: Database):
    key = callback.data.split(":", 1)[1]
    if key not in GENRE_BY_KEY:
        await callback.answer()
        return
    label, genre = GENRE_BY_KEY[key]
    user = callback.from_user
    await db.add_user(user.id, user.username, user.first_name, user.last_name)

    if await db.is_subscribed(user.id, genre):
        await db.remove_subscription(user.id, genre)
        await callback.answer(f"🔕 {label} obunasi bekor qilindi")
        subscribed = False
    else:
        await db.add_subscription(user.id, genre)
        await callback.answer(f"🔔 Endi yangi {label} kinolari haqida xabar olasiz")
        subscribed = True

    # Faqat obuna tugmasini yangilash
    markup = callback.message.reply_markup
    if markup:
        rows = [
            genre_subscribe_row(key, subscribed)
            if row and row[0].callback_data == f"gsub:{key}" else row
            for row in markup.inline_keyboard
        ]
        try:
            await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
        except TelegramBadRequest:
            pass


# ==================== KINO KARTOCHKASI ====================

@router.callback_query(F.data.startswith("movie:"))
async def callback_movie(callback: CallbackQuery, db: Database):
    code = callback.data.split(":", 1)[1]
    if not await open_movie(callback.message, db, code, callback.from_user.id):
        await callback.answer("❌ Kino topilmadi", show_alert=True)
        return
    await callback.answer()


async def _refresh_movie_keyboard(callback: CallbackQuery, db: Database, code: str):
    user_id = callback.from_user.id
    keyboard = get_movie_keyboard(
        code, await db.is_favorite(user_id, code), await db.is_watch_later(user_id, code)
    )
    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except TelegramBadRequest:
        pass


@router.callback_query(F.data.startswith("fav:"))
async def callback_favorite(callback: CallbackQuery, db: Database):
    code = callback.data.split(":", 1)[1]
    user = callback.from_user
    if not await db.code_exists(code):
        await callback.answer("❌ Kino topilmadi", show_alert=True)
        return
    await db.add_user(user.id, user.username, user.first_name, user.last_name)

    if await db.is_favorite(user.id, code):
        await db.remove_favorite(user.id, code)
        await callback.answer("💔 Sevimlilardan olib tashlandi")
    else:
        await db.add_favorite(user.id, code)
        await callback.answer("❤️ Sevimlilarga qo'shildi")
    await _refresh_movie_keyboard(callback, db, code)


@router.callback_query(F.data.startswith("wl:"))
async def callback_watch_later_toggle(callback: CallbackQuery, db: Database):
    code = callback.data.split(":", 1)[1]
    user = callback.from_user
    if not await db.code_exists(code):
        await callback.answer("❌ Kino topilmadi", show_alert=True)
        return
    await db.add_user(user.id, user.username, user.first_name, user.last_name)

    if await db.is_watch_later(user.id, code):
        await db.remove_watch_later(user.id, code)
        await callback.answer("🗑 Keyin ko'ramandan olib tashlandi")
    else:
        await db.add_watch_later(user.id, code)
        await callback.answer("⏰ Keyin ko'ramanga qo'shildi")
    await _refresh_movie_keyboard(callback, db, code)


# ==================== MATN (kod yoki nom) ====================

@router.message(F.text, ~F.text.startswith("/"))
async def handle_text(message: Message, db: Database, state: FSMContext):
    text = message.text.strip()
    user = message.from_user
    await db.add_user(user.id, user.username, user.first_name, user.last_name)

    if text.isdigit():
        if not await open_movie(message, db, text, user.id):
            await message.answer("❌ Bu kod bo'yicha kino topilmadi!")
        return

    if len(text) < 2:
        await message.answer("🔍 Qidirish uchun kamida 2 ta harf yozing.")
        return

    count = await db.count_search_results(text)
    movies = await db.search_movies_by_name(text, PAGE_SIZE, 0)
    if not movies:
        await message.answer(
            f"❌ «{escape(text)}» bo'yicha kino topilmadi.\n\n"
            "Boshqa nom bilan qidiring yoki kodni yuboring."
        )
        return

    await state.update_data(search_query=text)
    header = f"🔍 <b>Qidiruv natijalari ({escape(text)}):</b>"
    keyboard = get_movie_list_keyboard(movies, "list:srch", 0, total_pages(count))
    await message.answer(movie_list_text(header, movies), reply_markup=keyboard)
