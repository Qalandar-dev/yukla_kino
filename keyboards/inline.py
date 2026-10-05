from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Optional


def get_movie_keyboard(
    code: str,
    user_id: int,
    is_favorite: bool = False,
    is_watch_later: bool = False
) -> InlineKeyboardMarkup:
    """Kino kartochkasi uchun inline tugmalar"""
    buttons = []
    
    # Sevimlilar tugmasi
    fav_text = "❤️ Sevimlilardan olib tashlash" if is_favorite else "🤍 Sevimlilarga qo'shish"
    buttons.append([InlineKeyboardButton(text=fav_text, callback_data=f"fav_{code}")])
    
    # Keyin ko'raman tugmasi
    watch_text = "🗑 Keyin ko'ramandan olib tashlash" if is_watch_later else "⏰ Keyin ko'raman"
    buttons.append([InlineKeyboardButton(text=watch_text, callback_data=f"watch_{code}")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_search_results_keyboard(
    movies: List[Dict],
    page: int = 0,
    total_pages: int = 0,
    query: str = "",
    filter_type: str = "search"
) -> InlineKeyboardMarkup:
    """Qidiruv natijalari uchun inline tugmalar (sahifalash bilan)"""
    buttons = []
    
    for movie in movies:
        movie_title = movie['title'][:30] + "..." if len(movie['title']) > 30 else movie['title']
        buttons.append([
            InlineKeyboardButton(
                text=f"{movie['code']}. {movie_title}",
                callback_data=f"movie_{movie['code']}"
            )
        ])
    
    # Sahifalash tugmalari
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"{filter_type}_{query}_{page-1}")
        )
    
    nav_buttons.append(
        InlineKeyboardButton(text=f"{page + 1}/{total_pages + 1}", callback_data="page")
    )
    
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"{filter_type}_{query}_{page+1}")
        )
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Asosiy menyu"""
    buttons = [
        [InlineKeyboardButton(text="🔍 Qidirish", callback_data="search")],
        [InlineKeyboardButton(text="🆕 Yangilar", callback_data="new")],
        [InlineKeyboardButton(text="🏆 Top 10", callback_data="top")],
        [InlineKeyboardButton(text="❤️ Sevimlilar", callback_data="favorites")],
        [InlineKeyboardButton(text="⏰ Keyin ko'raman", callback_data="watch_later")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_category_keyboard() -> InlineKeyboardMarkup:
    """Kategoriya filtr tugmalari"""
    buttons = [
        [
            InlineKeyboardButton(text="🎭 Drama", callback_data="genre_Drama"),
            InlineKeyboardButton(text="💥 Action", callback_data="genre_Action")
        ],
        [
            InlineKeyboardButton(text="😂 Comedy", callback_data="genre_Comedy"),
            InlineKeyboardButton(text="😱 Horror", callback_data="genre_Horror")
        ],
        [
            InlineKeyboardButton(text="🔮 Fantasy", callback_data="genre_Fantasy"),
            InlineKeyboardButton(text="💕 Romance", callback_data="genre_Romance")
        ],
        [
            InlineKeyboardButton(text="🔍 Science Fiction", callback_data="genre_Sci-Fi"),
            InlineKeyboardButton(text="🎬 Thriller", callback_data="genre_Thriller")
        ],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Admin paneli uchun tugmalar"""
    buttons = [
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📋 Barcha kinolar", callback_data="admin_list")],
        [InlineKeyboardButton(text="➕ Kino qo'shish", callback_data="admin_add")],
        [InlineKeyboardButton(text="📢 Ommaviy xabar", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="admin_settings")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_settings_keyboard(force_subscription: bool = False) -> InlineKeyboardMarkup:
    """Sozlamalar tugmalari"""
    sub_text = "✅ Majburiy obuna: YOQILGAN" if force_subscription else "❌ Majburiy obuna: O'CHIRILGAN"
    buttons = [
        [InlineKeyboardButton(text=sub_text, callback_data="toggle_subscription")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
