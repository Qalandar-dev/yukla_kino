import asyncio
import logging
import re
from html import escape

from aiogram import Router, Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from config import Config
from database import Database
from services.tmdb import tmdb_service

logger = logging.getLogger(__name__)
router = Router()


def is_private_channel(message: Message) -> bool:
    """Faqat .env dagi PRIVATE_CHANNEL_ID kanalidan kelgan postlar qabul qilinadi"""
    if not Config.PRIVATE_CHANNEL_ID:
        logger.warning("PRIVATE_CHANNEL_ID sozlanmagan — kanal postlari e'tiborsiz qoldiriladi")
        return False
    return str(message.chat.id) == str(Config.PRIVATE_CHANNEL_ID).strip()


def extract_media(message: Message):
    """(file_id, file_type) yoki None"""
    if message.video:
        return message.video.file_id, "video"
    if message.animation:
        return message.animation.file_id, "animation"
    if message.document:
        return message.document.file_id, "document"
    return None


@router.channel_post()
@router.edited_channel_post()
async def handle_channel_post(message: Message, db: Database, bot: Bot):
    """Maxfiy kanaldan kinolarni avtomatik saqlash"""
    if not is_private_channel(message):
        return

    media = extract_media(message)
    if not media:
        return
    file_id, file_type = media

    caption = (message.caption or "").strip()
    lines = [line.strip() for line in caption.split("\n") if line.strip()]
    if not lines:
        logger.warning(f"Kanal posti {message.message_id}: caption yo'q, o'tkazib yuborildi")
        return

    code_match = re.search(r"\d+", lines[0])
    if not code_match:
        logger.warning(f"Kanal posti {message.message_id}: birinchi qatorda kod topilmadi: {lines[0]!r}")
        return

    code = code_match.group()
    title = lines[1] if len(lines) > 1 else "Noma'lum kino"
    is_new = not await db.code_exists(code)

    tmdb_info = await tmdb_service.get_movie_info_by_name(title) if title != "Noma'lum kino" else {}
    if not tmdb_info:
        logger.info(f"TMDB ma'lumoti topilmadi: {title}")

    saved = await db.add_movie(code=code, file_id=file_id, title=title, file_type=file_type, **tmdb_info)
    if not saved:
        return
    logger.info(f"Kino saqlandi: {code} | {title} ({'yangi' if is_new else 'yangilandi'})")

    if is_new and tmdb_info.get("genre"):
        asyncio.create_task(notify_subscribers(bot, db, code))


async def notify_subscribers(bot: Bot, db: Database, code: str):
    """Janrga obuna bo'lganlarga yangi kino haqida xabar yuborish"""
    movie = await db.get_movie_by_code(code)
    if not movie:
        return
    user_ids = await db.get_subscribers_for_genres(movie["genre"])
    if not user_ids:
        return

    text = (
        "🔔 <b>Yangi kino qo'shildi!</b>\n\n"
        f"🎬 {escape(movie['title'])} ({movie.get('year') or '—'})\n"
        f"🎭 {escape(movie['genre'])}\n"
        f"🔑 Kod: <code>{escape(code)}</code>"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Ko'rish", callback_data=f"movie:{code}")]
    ])

    sent = 0
    for user_id in user_ids:
        try:
            await bot.send_message(user_id, text, reply_markup=keyboard)
            sent += 1
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
        except TelegramForbiddenError:
            await db.set_user_blocked(user_id)
        except Exception as e:
            logger.error(f"Obunachiga yuborilmadi ({user_id}): {e}")
        await asyncio.sleep(0.05)
    logger.info(f"Yangi kino {code} haqida {sent} ta obunachiga xabar yuborildi")
