import asyncio
import logging
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
from database import Database
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()
bot = Bot(token=Config.BOT_TOKEN)
dp = Dispatcher()


def is_admin(user_id: int) -> bool:
    return user_id in Config.ADMIN_IDS


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("🎬 **Kino Botga xush kelibsiz!**\n\nKino kodini yuboring:", parse_mode="Markdown")


@dp.message(Command("list"))
async def cmd_list_movies(message: Message):
    if not is_admin(message.from_user.id):
        return
    movies = db.list_all_movies()
    if not movies:
        await message.answer("📭 Bazada kinolar yo'q.")
        return
    response = "📋 **Barcha kinolar:**\n\n"
    for idx, (code, title, added_at) in enumerate(movies, 1):
        response += f"{idx}. Kod: `{code}` | Nomi: {title}\n"
    await message.answer(response, parse_mode="Markdown")


# ==========================================
# DIAGNOSTIKA: KANAL POSTLARINI TESHIRISH
# ==========================================
@dp.channel_post()
@dp.edited_channel_post()
async def handle_channel_post_debug(message: Message):
    print("\n" + "=" * 50)
    print(f"📩 KANAL POSTI KELDI! Chat ID: {message.chat.id}")
    print(f"📌 Content Type: {message.content_type}")

    # 1. Video bor-yo'qligini tekshirish
    video = message.video or message.animation or message.document
    if not video:
        print("❌ XATOLIK: Xabarda video yoki media fayl topilmadi!")
        print("=" * 50 + "\n")
        return

    # 2. Caption bor-yo'qligini tekshirish
    caption = message.caption.strip() if message.caption else ""
    print(f"📝 Post Izohi (Caption):\n{caption}")

    if not caption:
        print("❌ XATOLIK: Videoga izoh (caption) yozilmagan!")
        print("=" * 50 + "\n")
        return

    lines = [line.strip() for line in caption.split("\n") if line.strip()]

    # 3. Koddagi raqamni izlash
    code_match = re.search(r'\d+', lines[0])
    if not code_match:
        print(f"❌ XATOLIK: Birinchi qatordan '{lines[0]}' raqamli kod topilmadi!")
        print("=" * 50 + "\n")
        return

    code = code_match.group()
    title = lines[1] if len(lines) > 1 else "Noma'lum kino"
    file_id = video.file_id

    # Bazaga saqlash
    if db.code_exists(code):
        db.delete_movie(code)

    if db.add_movie(code, file_id, title):
        print(f"✅ MUVAFFAQIYATLI SAQLANDI! -> Kod: {code} | Nomi: {title}")
    else:
        print(f"❌ XATOLIK: Bazaga saqlashda DB xatoligi yuz berdi!")
    print("=" * 50 + "\n")


@dp.message(F.text)
async def handle_code(message: Message):
    code = message.text.strip()
    if code.startswith("/"):
        return

    movie = db.get_movie_by_code(code)
    if movie:
        file_id, title = movie
        try:
            await message.answer_video(
                file_id,
                caption=f"🎬 **{title}**\n\n🔑 Kod: `{code}`",
                parse_mode="Markdown"
            )
        except Exception as e:
            await message.answer(f"❌ Video yuborishda xatolik: {e}")
    else:
        await message.answer("❌ Kino topilmadi!")


async def main():
    try:
        Config.validate()
        logger.info("Bot ishga tushmoqda...")
        await dp.start_polling(
            bot,
            allowed_updates=["message", "channel_post", "edited_channel_post"]
        )
    except Exception as e:
        logger.error(f"Xatolik: {e}")


if __name__ == "__main__":
    asyncio.run(main())