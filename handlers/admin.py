import asyncio
import aiosqlite
import logging
from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from database import Database
from keyboards.inline import get_admin_keyboard, get_settings_keyboard
from config import Config
from services.tmdb import tmdb_service

logger = logging.getLogger(__name__)
router = Router()


class AddMovieState(StatesGroup):
    waiting_for_title = State()
    waiting_for_confirmation = State()


class BroadcastState(StatesGroup):
    waiting_for_message = State()


def is_admin(user_id: int) -> bool:
    return user_id in Config.ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Admin paneli"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Siz admin emassiz!")
        return
    
    await message.answer(
        "⚙️ **Admin Paneli**",
        reply_markup=get_admin_keyboard()
    )


@router.callback_query(F.data == "admin_stats")
async def callback_admin_stats(callback: CallbackQuery, db: Database):
    """Admin statistikasi"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    total_users = await db.get_total_users()
    new_users_today = await db.get_new_users_today()
    total_movies = await db.get_total_movies()
    
    text = f"📊 **Statistika**\n\n"
    text += f"👥 Barcha foydalanuvchilar: {total_users}\n"
    text += f"🆕 Bugun qo'shilganlar: {new_users_today}\n"
    text += f"🎬 Barcha kinolar: {total_movies}\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "admin_list")
async def callback_admin_list(callback: CallbackQuery, db: Database):
    """Barcha kinolarni ko'rish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    movies = await db.list_all_movies()
    
    if not movies:
        await callback.answer("❌ Bazada kinolar yo'q", show_alert=True)
        return
    
    text = "📋 **Barcha kinolar:**\n\n"
    for idx, movie in enumerate(movies, 1):
        text += f"{idx}. Kod: `{movie['code']}` | Nomi: {movie['title']}\n"
    
    keyboard = get_admin_keyboard()
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "admin_add")
async def callback_admin_add(callback: CallbackQuery, state: FSMContext):
    """Kino qo'shishni boshlash"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    await state.set_state(AddMovieState.waiting_for_title)
    await callback.message.edit_text(
        "➕ **Kino qo'shish**\n\n"
        "Kinoni maxfiy kanalga yuboring. Caption format:\n"
        "1-qator: Kod (masalan: 123)\n"
        "2-qator: Kino nomi\n\n"
        "Yoki kino nomini yozing, TMDB dan ma'lumot olinadi.",
        reply_markup=get_admin_keyboard()
    )
    await callback.answer()


@router.message(AddMovieState.waiting_for_title)
async def process_movie_title(message: Message, state: FSMContext, db: Database):
    """Kino nomini qabul qilish va TMDB dan ma'lumot olish"""
    title = message.text.strip()
    
    await message.answer(f"🔍 '{title}' bo'yicha qidirilmoqda...")
    
    # TMDB dan ma'lumot olish
    tmdb_info = await tmdb_service.get_movie_info_by_name(title)
    
    if tmdb_info:
        response = f"✅ **Kino topildi:**\n\n"
        response += f"🎬 Nomi: {title}\n"
        if tmdb_info.get("year"):
            response += f"📅 Yil: {tmdb_info['year']}\n"
        if tmdb_info.get("genre"):
            response += f"🎭 Janr: {tmdb_info['genre']}\n"
        if tmdb_info.get("duration"):
            response += f"⏱ Davomiyligi: {tmdb_info['duration']} daqiqa\n"
        if tmdb_info.get("country"):
            response += f"🌍 Davlat: {tmdb_info['country']}\n"
        if tmdb_info.get("description"):
            response += f"\n📝 Mazmun: {tmdb_info['description'][:200]}...\n"
        
        response += "\n\nEndi kinoni kanalga yuboring (captionda kod va nom bo'lishi kerak)."
        
        await state.update_data(
            title=title,
            tmdb_info=tmdb_info
        )
        await state.set_state(AddMovieState.waiting_for_confirmation)
        await message.answer(response)
    else:
        await message.answer(
            f"⚠️ TMDB dan ma'lumot topilmadi.\n\n"
            "Kinoni kanalga yuboring (captionda kod va nom bo'lishi kerak)."
        )
        await state.update_data(title=title)
        await state.set_state(AddMovieState.waiting_for_confirmation)


@router.callback_query(F.data == "admin_broadcast")
async def callback_admin_broadcast(callback: CallbackQuery, state: FSMContext):
    """Ommaviy xabar yuborishni boshlash"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    await state.set_state(BroadcastState.waiting_for_message)
    await callback.message.edit_text(
        "📢 **Ommaviy xabar**\n\n"
        "Xabarni yuboring, u barcha foydalanuvchilarga yuboriladi.\n\n"
        "Bekor qilish uchun /cancel yuboring.",
        reply_markup=get_admin_keyboard()
    )
    await callback.answer()


@router.message(BroadcastState.waiting_for_message)
async def process_broadcast(message: Message, state: FSMContext, db: Database, bot):
    """Ommaviy xabarni qabul qilish va yuborish"""
    text = message.text or message.caption
    
    if not text:
        await message.answer("❌ Xabar bo'sh!")
        return
    
    await message.answer("📤 Xabar yuborilmoqda...")
    
    # Barcha foydalanuvchilarni olish
    users = await db.get_total_users()
    sent_count = 0
    failed_count = 0
    
    # Flood limitdan qochish uchun sekin yuborish
    async with aiosqlite.connect("movies.db") as conn:
        cursor = await conn.execute("SELECT user_id FROM users")
        user_ids = [row[0] for row in await cursor.fetchall()]
    
    for user_id in user_ids:
        try:
            await bot.send_message(user_id, text)
            sent_count += 1
            # Flood limitdan qochish uchun 0.1 sekund kutish
            await asyncio.sleep(0.1)
        except Exception as e:
            failed_count += 1
            logger.error(f"Failed to send to {user_id}: {e}")
    
    await state.clear()
    await message.answer(
        f"✅ Ommaviy xabar tugadi!\n\n"
        f"📤 Yuborildi: {sent_count}\n"
        f"❌ Xatolik: {failed_count}\n"
        f"👥 Jami: {users}"
    )


@router.message(Command("cancel"), StateFilter(AddMovieState, BroadcastState))
async def cancel_state(message: Message, state: FSMContext):
    """Holatni bekor qilish"""
    await state.clear()
    await message.answer("❌ Amal bekor qilindi.")


@router.callback_query(F.data == "admin_settings")
async def callback_admin_settings(callback: CallbackQuery):
    """Sozlamalar"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    keyboard = get_settings_keyboard()
    await callback.message.edit_text(
        "⚙️ **Sozlamalar**",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "admin_back")
async def callback_admin_back(callback: CallbackQuery):
    """Admin paneliga qaytish"""
    keyboard = get_admin_keyboard()
    await callback.message.edit_text(
        "⚙️ **Admin Paneli**",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "toggle_subscription")
async def callback_toggle_subscription(callback: CallbackQuery):
    """Majburiy obunani yoqish/o'chirish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    # Bu funksiya keyinroq to'liq amalga oshiriladi
    await callback.answer("⚠️ Bu funksiya hozircha ishlayapti", show_alert=True)


@router.message(Command("list"))
async def cmd_list_movies(message: Message, db: Database):
    """Barcha kinolarni ko'rish (faqat admin)"""
    if not is_admin(message.from_user.id):
        return
    
    movies = await db.list_all_movies()
    if not movies:
        await message.answer("📭 Bazada kinolar yo'q.")
        return
    
    response = "📋 **Barcha kinolar:**\n\n"
    for idx, movie in enumerate(movies, 1):
        response += f"{idx}. Kod: `{movie['code']}` | Nomi: {movie['title']}\n"
    await message.answer(response, parse_mode="Markdown")


@router.message(Command("delete"))
async def cmd_delete_movie(message: Message, db: Database):
    """Kinoni o'chirish (faqat admin)"""
    if not is_admin(message.from_user.id):
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Foydalanish: /delete <kod>")
        return
    
    code = args[1]
    if await db.delete_movie(code):
        await message.answer(f"✅ Kino o'chirildi: {code}")
    else:
        await message.answer(f"❌ Kino topilmadi: {code}")
