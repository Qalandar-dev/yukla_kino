import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from database import Database
from config import Config
from handlers import user, admin, channel, inline
from middlewares.db import DbMiddleware
from middlewares.channel_check import ChannelCheckMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def main():
    Config.validate()

    db = Database(Config.DB_FILE)
    await db.init_db()

    # Majburiy obuna holati bazada saqlanadi (admin paneldan o'zgartiriladi).
    # Birinchi ishga tushishda .env dagi qiymat olinadi.
    saved = await db.get_setting("force_channel_check")
    if saved is not None:
        Config.FORCE_CHANNEL_CHECK = saved == "1"

    bot = Bot(token=Config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.update.outer_middleware(DbMiddleware(db))
    dp.update.outer_middleware(ChannelCheckMiddleware())

    # Tartib muhim: admin va kanal routerlari user routeridagi umumiy
    # matn handleridan OLDIN ulanishi kerak.
    dp.include_router(admin.router)
    dp.include_router(channel.router)
    dp.include_router(inline.router)
    dp.include_router(user.router)

    await bot.set_my_commands([
        BotCommand(command="start", description="Botni boshlash"),
        BotCommand(command="help", description="Yordam"),
        BotCommand(command="random", description="Tasodifiy kino"),
    ])

    logger.info("Bot ishga tushmoqda...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi")
