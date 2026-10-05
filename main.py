import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from database import Database
from config import Config
from handlers import user, admin, channel, inline
from middlewares.db import DbMiddleware
from middlewares.channel_check import ChannelCheckMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    try:
        Config.validate()
        
        # Database initialization
        db = Database()
        await db.init_db()
        
        # Bot va Dispatcher
        bot = Bot(token=Config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
        dp = Dispatcher(storage=MemoryStorage())
        
        # Middleware
        dp.update.middleware(DbMiddleware(db))
        dp.update.middleware(ChannelCheckMiddleware())
        
        # Handlers ro'yxatga qo'shish
        dp.include_router(user.router)
        dp.include_router(admin.router)
        dp.include_router(channel.router)
        dp.include_router(inline.router)
        
        logger.info("Bot ishga tushmoqda...")
        await dp.start_polling(
            bot,
            allowed_updates=["message", "channel_post", "edited_channel_post", "callback_query", "inline_query"]
        )
    except Exception as e:
        logger.error(f"Xatolik: {e}")


if __name__ == "__main__":
    asyncio.run(main())