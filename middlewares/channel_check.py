from aiogram import BaseMiddleware
from aiogram.types import Update, Message
from typing import Callable, Dict, Any, Awaitable, Optional
from config import Config
import logging

logger = logging.getLogger(__name__)


class ChannelCheckMiddleware(BaseMiddleware):
    """Majburiy kanal obuna tekshiruvi"""
    
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        
        # Agar majburiy kanal tekshiruvi o'chirilgan bo'lsa
        if not Config.FORCE_CHANNEL_CHECK or not Config.FORCE_CHANNEL_ID:
            return await handler(event, data)
        
        # Faqat message uchun tekshirish (callback_query va inline_query uchun emas)
        if not event.message:
            return await handler(event, data)
        
        # Adminlar uchun tekshirish shart emas
        user_id = event.message.from_user.id
        if user_id in Config.ADMIN_IDS:
            return await handler(event, data)
        
        # Kanal obunasini tekshirish
        try:
            bot = data["bot"]
            member = await bot.get_chat_member(Config.FORCE_CHANNEL_ID, user_id)
            
            if member.status in ["left", "kicked"]:
                # Foydalanuvchi obuna bo'lmagan
                await event.message.answer(
                    "⚠️ **Diqqat!**\n\n"
                    f"Botdan foydalanish uchun quyidagi kanalga obuna bo'lishingiz shart:\n\n"
                    f"👉 [Kanalga o'tish](https://t.me/{Config.FORCE_CHANNEL_ID.replace('-100', '')})\n\n"
                    "Obuna bo'lgach, /start ni bosing.",
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )
                return  # Handlerni ishga tushirmaslik
        except Exception as e:
            logger.error(f"Channel check error: {e}")
            # Xatolik bo'lsa, handlerni ishga tushirish (bloklamaslik)
        
        return await handler(event, data)
