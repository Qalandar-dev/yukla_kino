import logging
from typing import Callable, Dict, Any, Awaitable, Optional

from aiogram import BaseMiddleware, Bot
from aiogram.types import Update, InlineKeyboardMarkup, InlineKeyboardButton

from config import Config

logger = logging.getLogger(__name__)

CHECK_CALLBACK = "check_sub"

_channel_link_cache: Optional[str] = None


async def get_channel_link(bot: Bot) -> Optional[str]:
    """Majburiy kanal havolasini aniqlash (bir marta, keyin keshdan)"""
    global _channel_link_cache
    if Config.FORCE_CHANNEL_LINK:
        return Config.FORCE_CHANNEL_LINK
    if _channel_link_cache:
        return _channel_link_cache
    try:
        chat = await bot.get_chat(Config.FORCE_CHANNEL_ID)
        if chat.username:
            _channel_link_cache = f"https://t.me/{chat.username}"
        elif chat.invite_link:
            _channel_link_cache = chat.invite_link
        else:
            _channel_link_cache = await bot.export_chat_invite_link(Config.FORCE_CHANNEL_ID)
    except Exception as e:
        logger.error(f"Kanal havolasini olib bo'lmadi: {e}")
    return _channel_link_cache


async def is_subscribed(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(Config.FORCE_CHANNEL_ID, user_id)
        return member.status not in ("left", "kicked")
    except Exception as e:
        # Bot kanalda admin bo'lmasa va h.k. — foydalanuvchini bloklamaymiz
        logger.error(f"Channel check error: {e}")
        return True


def subscribe_keyboard(link: Optional[str]) -> InlineKeyboardMarkup:
    buttons = []
    if link:
        buttons.append([InlineKeyboardButton(text="📢 Kanalga o'tish", url=link)])
    buttons.append([InlineKeyboardButton(text="✅ Obuna bo'ldim", callback_data=CHECK_CALLBACK)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


SUBSCRIBE_TEXT = (
    "⚠️ <b>Diqqat!</b>\n\n"
    "Botdan foydalanish uchun quyidagi kanalga obuna bo'lishingiz shart.\n"
    "Obuna bo'lgach, «✅ Obuna bo'ldim» tugmasini bosing."
)


class ChannelCheckMiddleware(BaseMiddleware):
    """Majburiy kanal obuna tekshiruvi (xabarlar va tugmalar uchun)"""

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        if not Config.FORCE_CHANNEL_CHECK or not Config.FORCE_CHANNEL_ID:
            return await handler(event, data)

        if event.message and event.message.chat.type == "private":
            user = event.message.from_user
        elif event.callback_query and event.callback_query.data != CHECK_CALLBACK:
            user = event.callback_query.from_user
        else:
            # Kanal postlari, inline so'rovlar va tekshirish tugmasi o'tkaziladi
            return await handler(event, data)

        if not user or user.id in Config.ADMIN_IDS:
            return await handler(event, data)

        bot: Bot = data["bot"]
        if await is_subscribed(bot, user.id):
            return await handler(event, data)

        link = await get_channel_link(bot)
        if event.message:
            await event.message.answer(SUBSCRIBE_TEXT, reply_markup=subscribe_keyboard(link))
        else:
            await event.callback_query.answer("⚠️ Avval kanalga obuna bo'ling!", show_alert=True)
        return None
