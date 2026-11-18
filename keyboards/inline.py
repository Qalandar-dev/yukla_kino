from typing import List, Dict, Optional, Iterable

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils import GENRES

# Callback data formatlari (Telegram cheklovi: 64 bayt):
#   movie:<kod>             — kino kartochkasi
#   fav:<kod> / wl:<kod>    — sevimlilar / keyin ko'raman
#   list:<tur>:<sahifa>     — tur: new | top | fav | wl | srch
#   genre:<kalit>:<sahifa>  — janr bo'yicha ro'yxat
#   gsub:<kalit>            — janrga obuna bo'lish/bekor qilish
#   menu | genres | search | random | noop


def get_movie_keyboard(code: str, is_favorite: bool = False, is_watch_later: bool = False) -> InlineKeyboardMarkup:
    """Kino kartochkasi uchun tugmalar"""
    fav_text = "❤️ Sevimlilardan olib tashlash" if is_favorite else "🤍 Sevimlilarga qo'shish"
    watch_text = "🗑 Keyin ko'ramandan olib tashlash" if is_watch_later else "⏰ Keyin ko'raman"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=fav_text, callback_data=f"fav:{code}")],
        [InlineKeyboardButton(text=watch_text, callback_data=f"wl:{code}")],
        [InlineKeyboardButton(text="📤 Do'stga ulashish", switch_inline_query=str(code))],
    ])


def _nav_row(prefix: str, page: int, pages: int) -> List[InlineKeyboardButton]:
    row = []
    if page > 0:
        row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"{prefix}:{page - 1}"))
    row.append(InlineKeyboardButton(text=f"{page + 1}/{pages}", callback_data="noop"))
    if page < pages - 1:
        row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"{prefix}:{page + 1}"))
    return row


def get_movie_list_keyboard(
    movies: List[Dict],
    prefix: str,
    page: int = 0,
    pages: int = 1,
    extra_rows: Optional[Iterable[List[InlineKeyboardButton]]] = None,
    back: str = "menu",
) -> InlineKeyboardMarkup:
    """Kinolar ro'yxati: har bir kino tugma, sahifalash va orqaga"""
    buttons = []
    for movie in movies:
        title = movie["title"]
        if len(title) > 30:
            title = title[:30] + "…"
        buttons.append([InlineKeyboardButton(text=f"{movie['code']}. {title}", callback_data=f"movie:{movie['code']}")])

    if pages > 1:
        buttons.append(_nav_row(prefix, page, pages))
    if extra_rows:
        buttons.extend(extra_rows)
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data=back)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍 Qidirish", callback_data="search"),
            InlineKeyboardButton(text="🎲 Tasodifiy", callback_data="random"),
        ],
        [
            InlineKeyboardButton(text="🆕 Yangilar", callback_data="list:new:0"),
            InlineKeyboardButton(text="🏆 Top", callback_data="list:top:0"),
        ],
        [InlineKeyboardButton(text="🎭 Janrlar", callback_data="genres")],
        [
            InlineKeyboardButton(text="❤️ Sevimlilar", callback_data="list:fav:0"),
            InlineKeyboardButton(text="⏰ Keyin ko'raman", callback_data="list:wl:0"),
        ],
    ])


def get_category_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for i in range(0, len(GENRES), 2):
        buttons.append([
            InlineKeyboardButton(text=label, callback_data=f"genre:{key}:0")
            for key, label, _ in GENRES[i:i + 2]
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def genre_subscribe_row(key: str, subscribed: bool) -> List[InlineKeyboardButton]:
    text = "🔕 Obunani bekor qilish" if subscribed else "🔔 Yangi kinolardan xabardor bo'lish"
    return [InlineKeyboardButton(text=text, callback_data=f"gsub:{key}")]


def get_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📋 Barcha kinolar", callback_data="admin_list")],
        [InlineKeyboardButton(text="➕ Kino qo'shish", callback_data="admin_add")],
        [InlineKeyboardButton(text="📢 Ommaviy xabar", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="admin_settings")],
    ])


def get_admin_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_back")],
    ])


def get_settings_keyboard(force_subscription: bool = False) -> InlineKeyboardMarkup:
    sub_text = "✅ Majburiy obuna: YOQILGAN" if force_subscription else "❌ Majburiy obuna: O'CHIRILGAN"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=sub_text, callback_data="toggle_subscription")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back")],
    ])


def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Yuborish", callback_data="bc_send"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="bc_cancel"),
    ]])
