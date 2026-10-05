from aiogram import Router, types, F
from aiogram.types import Message
from database import Database
from services.tmdb import tmdb_service
import re
import logging

logger = logging.getLogger(__name__)
router = Router()


@router.channel_post()
@router.edited_channel_post()
async def handle_channel_post(message: Message, db: Database):
    """Kanaldan kinolarni avtomatik o'qish"""
    print("\n" + "=" * 50)
    print(f"📩 KANAL POSTI KELDI! Chat ID: {message.chat.id}")
    print(f"📌 Content Type: {message.content_type}")

    # Video bor-yo'qligini tekshirish
    video = message.video or message.animation or message.document
    if not video:
        print("❌ XATOLIK: Xabarda video yoki media fayl topilmadi!")
        print("=" * 50 + "\n")
        return

    # Caption bor-yo'qligini tekshirish
    caption = message.caption.strip() if message.caption else ""
    print(f"📝 Post Izohi (Caption):\n{caption}")

    if not caption:
        print("❌ XATOLIK: Videoga izoh (caption) yozilmagan!")
        print("=" * 50 + "\n")
        return

    lines = [line.strip() for line in caption.split("\n") if line.strip()]

    # Koddagi raqamni izlash
    code_match = re.search(r'\d+', lines[0])
    if not code_match:
        print(f"❌ XATOLIK: Birinchi qatordan '{lines[0]}' raqamli kod topilmadi!")
        print("=" * 50 + "\n")
        return

    code = code_match.group()
    title = lines[1] if len(lines) > 1 else "Noma'lum kino"
    file_id = video.file_id

    # Bazaga saqlash
    if await db.code_exists(code):
        await db.delete_movie(code)

    # TMDB dan ma'lumot olish
    tmdb_info = await tmdb_service.get_movie_info_by_name(title)
    
    if tmdb_info:
        print(f"🎬 TMDB dan ma'lumot olindi: {title}")
        await db.add_movie(
            code=code,
            file_id=file_id,
            title=title,
            poster_url=tmdb_info.get("poster_url"),
            year=tmdb_info.get("year"),
            genre=tmdb_info.get("genre"),
            duration=tmdb_info.get("duration"),
            description=tmdb_info.get("description"),
            country=tmdb_info.get("country"),
            language=tmdb_info.get("language")
        )
    else:
        print(f"⚠️ TMDB dan ma'lumot topilmadi, asosiy ma'lumotlar saqlanmoqda")
        await db.add_movie(code, file_id, title)

    print(f"✅ MUVAFFAQIYATLI SAQLANDI! -> Kod: {code} | Nomi: {title}")
    print("=" * 50 + "\n")
