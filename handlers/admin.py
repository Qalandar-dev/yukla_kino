import asyncio
import logging
from html import escape

from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup

from config import Config
from database import Database, EDITABLE_FIELDS
from keyboards.inline import (
    get_admin_keyboard,
    get_admin_back_keyboard,
    get_settings_keyboard,
    get_broadcast_confirm_keyboard,
)
from services.tmdb import tmdb_service

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in Config.ADMIN_IDS


# Routerdagi barcha handlerlar faqat adminlar uchun
router.message.filter(F.from_user.func(lambda u: is_admin(u.id)))
router.callback_query.filter(F.from_user.func(lambda u: is_admin(u.id)))


class AddMovieState(StatesGroup):
    waiting_for_title = State()


class BroadcastState(StatesGroup):
    waiting_for_message = State()
    waiting_for_confirm = State()


ADMIN_TITLE = "⚙️ <b>Admin paneli</b>"

ADMIN_HELP = (
    "\n\n<b>Komandalar:</b>\n"
    "/list — barcha kinolar\n"
    "/delete &lt;kod&gt; — kinoni o'chirish\n"
    "/edit &lt;kod&gt; &lt;maydon&gt; &lt;qiymat&gt; — kinoni tahrirlash\n"
    "/tmdb &lt;kod&gt; — ma'lumotlarni TMDB dan qayta olish\n"
    "/cancel — joriy amalni bekor qilish"
)


async def safe_edit(callback: CallbackQuery, text: str, keyboard: InlineKeyboardMarkup = None):
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            await callback.message.answer(text, reply_markup=keyboard)


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(ADMIN_TITLE + ADMIN_HELP, reply_markup=get_admin_keyboard())


@router.message(Command("cancel"), StateFilter(AddMovieState, BroadcastState))
async def cancel_state(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Amal bekor qilindi.", reply_markup=get_admin_keyboard())


@router.callback_query(F.data == "admin_back")
async def callback_admin_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await safe_edit(callback, ADMIN_TITLE + ADMIN_HELP, get_admin_keyboard())
    await callback.answer()


# ==================== STATISTIKA ====================

@router.callback_query(F.data == "admin_stats")
async def callback_admin_stats(callback: CallbackQuery, db: Database):
    total_users = await db.get_total_users()
    blocked = await db.get_blocked_users()
    new_today = await db.get_new_users_today()
    total_movies = await db.get_total_movies()
    total_views = await db.get_total_views()
    top = await db.get_top_movies(limit=5)

    text = (
        "📊 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar: {total_users}\n"
        f"🚫 Botni bloklaganlar: {blocked}\n"
        f"🆕 Bugun qo'shilganlar: {new_today}\n"
        f"🎬 Kinolar: {total_movies}\n"
        f"👀 Jami ko'rishlar: {total_views}\n"
    )
    if top:
        text += "\n🏆 <b>Eng ko'p ko'rilganlar:</b>\n"
        for i, movie in enumerate(top, 1):
            text += f"{i}. {escape(movie['title'])} — {movie['view_count']} 👀\n"

    await safe_edit(callback, text, get_admin_back_keyboard())
    await callback.answer()


# ==================== KINOLAR RO'YXATI ====================

def _movies_list_chunks(movies) -> list:
    """Uzun ro'yxatni Telegram cheklovi (4096) bo'yicha bo'laklarga ajratish"""
    chunks, current = [], "📋 <b>Barcha kinolar:</b>\n\n"
    for idx, movie in enumerate(movies, 1):
        line = f"{idx}. <code>{escape(movie['code'])}</code> — {escape(movie['title'])} (👀 {movie['view_count']})\n"
        if len(current) + len(line) > 4000:
            chunks.append(current)
            current = ""
        current += line
    chunks.append(current)
    return chunks


@router.callback_query(F.data == "admin_list")
async def callback_admin_list(callback: CallbackQuery, db: Database):
    movies = await db.list_all_movies()
    if not movies:
        await callback.answer("📭 Bazada kinolar yo'q", show_alert=True)
        return
    chunks = _movies_list_chunks(movies)
    if len(chunks) == 1:
        await safe_edit(callback, chunks[0], get_admin_back_keyboard())
    else:
        for chunk in chunks:
            await callback.message.answer(chunk)
    await callback.answer()


@router.message(Command("list"))
async def cmd_list_movies(message: Message, db: Database):
    movies = await db.list_all_movies()
    if not movies:
        await message.answer("📭 Bazada kinolar yo'q.")
        return
    for chunk in _movies_list_chunks(movies):
        await message.answer(chunk)


# ==================== O'CHIRISH / TAHRIRLASH ====================

@router.message(Command("delete"))
async def cmd_delete_movie(message: Message, command: CommandObject, db: Database):
    code = (command.args or "").strip()
    if not code:
        await message.answer("❌ Foydalanish: <code>/delete &lt;kod&gt;</code>")
        return
    if await db.delete_movie(code):
        await message.answer(f"✅ Kino o'chirildi: <code>{escape(code)}</code>")
    else:
        await message.answer(f"❌ Kino topilmadi: <code>{escape(code)}</code>")


INT_FIELDS = {"year", "duration"}
EDIT_HELP = (
    "✏️ <b>Foydalanish:</b>\n"
    "<code>/edit &lt;kod&gt; &lt;maydon&gt; &lt;qiymat&gt;</code>\n\n"
    "Maydonlar: " + ", ".join(f"<code>{f}</code>" for f in sorted(EDITABLE_FIELDS - {"file_id", "file_type"})) +
    "\n\nMasalan: <code>/edit 12 year 2019</code>\n"
    "Qiymatni o'chirish uchun: <code>/edit 12 description -</code>"
)


@router.message(Command("edit"))
async def cmd_edit_movie(message: Message, command: CommandObject, db: Database):
    parts = (command.args or "").split(maxsplit=2)
    if len(parts) < 3:
        await message.answer(EDIT_HELP)
        return

    code, field, value = parts[0], parts[1].lower(), parts[2].strip()
    if field not in EDITABLE_FIELDS or field in ("file_id", "file_type"):
        await message.answer(f"❌ Noma'lum maydon: <code>{escape(field)}</code>\n\n" + EDIT_HELP)
        return

    if value == "-":
        if field == "title":
            await message.answer("❌ Kino nomini o'chirib bo'lmaydi.")
            return
        new_value = None
    elif field in INT_FIELDS:
        if not value.isdigit():
            await message.answer(f"❌ <code>{field}</code> butun son bo'lishi kerak.")
            return
        new_value = int(value)
    else:
        new_value = value

    if await db.update_movie_field(code, field, new_value):
        await message.answer(f"✅ <code>{escape(code)}</code> kinosining <b>{field}</b> maydoni yangilandi.")
    else:
        await message.answer(f"❌ Kino topilmadi: <code>{escape(code)}</code>")


@router.message(Command("tmdb"))
async def cmd_refresh_tmdb(message: Message, command: CommandObject, db: Database):
    code = (command.args or "").strip()
    movie = await db.get_movie_by_code(code) if code else None
    if not movie:
        await message.answer("❌ Foydalanish: <code>/tmdb &lt;kod&gt;</code> (kino bazada bo'lishi kerak)")
        return
    if not Config.TMDB_API_KEY:
        await message.answer("⚠️ TMDB_API_KEY sozlanmagan.")
        return
    info = await tmdb_service.get_movie_info_by_name(movie["title"])
    if not info:
        await message.answer("⚠️ TMDB dan ma'lumot topilmadi.")
        return
    for field, value in info.items():
        if value is not None:
            await db.update_movie_field(code, field, value)
    await message.answer(f"✅ <code>{escape(code)}</code> ma'lumotlari TMDB dan yangilandi.")


# ==================== KINO QO'SHISH (TMDB ko'rib chiqish) ====================

@router.callback_query(F.data == "admin_add")
async def callback_admin_add(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddMovieState.waiting_for_title)
    await safe_edit(
        callback,
        "➕ <b>Kino qo'shish</b>\n\n"
        "Kinoni maxfiy kanalga yuboring. Caption formati:\n"
        "1-qator: kod (masalan: <code>123</code>)\n"
        "2-qator: kino nomi\n\n"
        "TMDB da qanday ma'lumot topilishini oldindan ko'rish uchun kino nomini shu yerga yozing.\n"
        "Bekor qilish: /cancel",
        get_admin_back_keyboard(),
    )
    await callback.answer()


@router.message(AddMovieState.waiting_for_title, F.text, ~F.text.startswith("/"))
async def process_movie_title(message: Message, state: FSMContext):
    title = message.text.strip()
    await state.clear()

    if not Config.TMDB_API_KEY:
        await message.answer("⚠️ TMDB_API_KEY sozlanmagan. Kinoni to'g'ridan-to'g'ri kanalga yuboring.")
        return

    await message.answer(f"🔍 «{escape(title)}» bo'yicha qidirilmoqda...")
    info = await tmdb_service.get_movie_info_by_name(title)
    if not info:
        await message.answer(
            "⚠️ TMDB dan ma'lumot topilmadi.\n"
            "Kinoni baribir kanalga yuborishingiz mumkin — asosiy ma'lumotlar saqlanadi."
        )
        return

    text = f"✅ <b>TMDB da topildi:</b>\n\n🎬 {escape(title)}\n"
    if info.get("year"):
        text += f"📅 Yil: {info['year']}\n"
    if info.get("genre"):
        text += f"🎭 Janr: {escape(info['genre'])}\n"
    if info.get("duration"):
        text += f"⏱ Davomiyligi: {info['duration']} daqiqa\n"
    if info.get("country"):
        text += f"🌍 Davlat: {escape(info['country'])}\n"
    if info.get("description"):
        text += f"\n📝 {escape(info['description'][:300])}…\n"
    text += "\nEndi kinoni kanalga yuboring — bu ma'lumotlar avtomatik qo'shiladi."
    await message.answer(text)


# ==================== OMMAVIY XABAR ====================

@router.callback_query(F.data == "admin_broadcast")
async def callback_admin_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BroadcastState.waiting_for_message)
    await safe_edit(
        callback,
        "📢 <b>Ommaviy xabar</b>\n\n"
        "Xabarni yuboring (matn, rasm, video — istalgan turdagi).\n"
        "Bekor qilish: /cancel",
        get_admin_back_keyboard(),
    )
    await callback.answer()


@router.message(BroadcastState.waiting_for_message, F.func(lambda m: not (m.text or "").startswith("/")))
async def process_broadcast_message(message: Message, state: FSMContext, db: Database):
    total = len(await db.get_all_user_ids())
    await state.update_data(chat_id=message.chat.id, message_id=message.message_id)
    await state.set_state(BroadcastState.waiting_for_confirm)
    await message.answer(
        f"Yuqoridagi xabar <b>{total}</b> ta foydalanuvchiga yuboriladi. Tasdiqlaysizmi?",
        reply_markup=get_broadcast_confirm_keyboard(),
    )


@router.callback_query(BroadcastState.waiting_for_confirm, F.data == "bc_cancel")
async def callback_broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await safe_edit(callback, "❌ Ommaviy xabar bekor qilindi.")
    await callback.answer()


@router.callback_query(BroadcastState.waiting_for_confirm, F.data == "bc_send")
async def callback_broadcast_send(callback: CallbackQuery, state: FSMContext, db: Database, bot: Bot):
    data = await state.get_data()
    await state.clear()
    await safe_edit(callback, "📤 Xabar yuborilmoqda...")
    await callback.answer()

    sent, failed, blocked = await broadcast_copy(bot, db, data["chat_id"], data["message_id"])
    await callback.message.answer(
        "✅ <b>Ommaviy xabar tugadi!</b>\n\n"
        f"📤 Yuborildi: {sent}\n"
        f"🚫 Botni bloklagan: {blocked}\n"
        f"❌ Boshqa xatolik: {failed}"
    )


async def broadcast_copy(bot: Bot, db: Database, from_chat_id: int, message_id: int):
    sent = failed = blocked = 0
    for user_id in await db.get_all_user_ids():
        for _ in range(2):
            try:
                await bot.copy_message(user_id, from_chat_id, message_id)
                sent += 1
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)
                continue
            except TelegramForbiddenError:
                blocked += 1
                await db.set_user_blocked(user_id)
            except Exception as e:
                failed += 1
                logger.error(f"Failed to send to {user_id}: {e}")
            break
        # ~20 xabar/sekund — Telegram flood limitidan past
        await asyncio.sleep(0.05)
    return sent, failed, blocked


# ==================== SOZLAMALAR ====================

@router.callback_query(F.data == "admin_settings")
async def callback_admin_settings(callback: CallbackQuery):
    text = "⚙️ <b>Sozlamalar</b>"
    if not Config.FORCE_CHANNEL_ID:
        text += "\n\n⚠️ Majburiy obuna uchun .env da FORCE_CHANNEL_ID ko'rsatilmagan."
    await safe_edit(callback, text, get_settings_keyboard(Config.FORCE_CHANNEL_CHECK))
    await callback.answer()


@router.callback_query(F.data == "toggle_subscription")
async def callback_toggle_subscription(callback: CallbackQuery, db: Database):
    if not Config.FORCE_CHANNEL_ID:
        await callback.answer("⚠️ Avval .env da FORCE_CHANNEL_ID ni ko'rsating", show_alert=True)
        return
    Config.FORCE_CHANNEL_CHECK = not Config.FORCE_CHANNEL_CHECK
    await db.set_setting("force_channel_check", "1" if Config.FORCE_CHANNEL_CHECK else "0")
    try:
        await callback.message.edit_reply_markup(reply_markup=get_settings_keyboard(Config.FORCE_CHANNEL_CHECK))
    except TelegramBadRequest:
        pass
    await callback.answer("✅ Yoqildi" if Config.FORCE_CHANNEL_CHECK else "❌ O'chirildi")
