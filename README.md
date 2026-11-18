# 🎬 Telegram Kino Bot

Kod va nom bo'yicha qidiruv, janrlar, sevimlilar, inline rejim va admin paneliga ega Telegram kino boti (aiogram 3).

## ✨ Imkoniyatlar

### Foydalanuvchilar uchun
- **Kod bo'yicha qidirish** — kodni yuboring, kino fayli kartochkasi bilan keladi
- **Nom bo'yicha qidirish** — nomning bir qismini yozish kifoya (`spider` → *Spider-Man*), FTS5 + prefiks qidiruv
- **Sahifalash** — barcha ro'yxatlarda 5 tadan, «Oldingi / Keyingi» tugmalari bilan
- **🆕 Yangilar** va **🏆 Top** — eng so'nggi va eng ko'p ko'rilgan kinolar
- **🎭 Janrlar** — 12 ta janr bo'yicha ko'rish
- **🔔 Janrga obuna** — tanlangan janrda yangi kino qo'shilganda bot xabar beradi
- **🎲 Tasodifiy kino** — menyudan yoki `/random`
- **❤️ Sevimlilar** va **⏰ Keyin ko'raman**
- **📤 Ulashish** — kartochkadagi tugma orqali do'stga yuborish; xabarda botga to'g'ridan-to'g'ri havola bo'ladi (`t.me/bot?start=<kod>`)
- **Inline rejim** — istalgan chatda `@botnomi kino nomi`

### Adminlar uchun
- **Avtomatik qo'shish** — maxfiy kanalga video/hujjat yuboring, bot o'zi saqlaydi
- **TMDB integratsiya** — yil, janr, davomiylik, davlat va mazmun avtomatik to'ldiriladi
- **Tahrirlash** — `/edit <kod> <maydon> <qiymat>`
- **O'chirish** — `/delete <kod>`
- **TMDB dan yangilash** — `/tmdb <kod>`
- **Statistika** — foydalanuvchilar, bloklaganlar, ko'rishlar, top kinolar
- **Ommaviy xabar** — matn, rasm, video va h.k.; yuborishdan oldin tasdiqlash; botni bloklaganlar avtomatik belgilanadi
- **Majburiy obuna** — admin paneldan yoqish/o'chirish (holat bazada saqlanadi), foydalanuvchiga «Kanalga o'tish» va «✅ Obuna bo'ldim» tugmalari chiqadi

## 📋 Talablar

- Python 3.9+
- Telegram bot tokeni ([@BotFather](https://t.me/BotFather))
- Maxfiy Telegram kanal (bot unda **admin** bo'lishi kerak)
- TMDB API kaliti — ixtiyoriy ([themoviedb.org](https://www.themoviedb.org/settings/api))

## 🚀 O'rnatish

```bash
git clone https://github.com/qalandar-dev/yukla_kino.git
cd yukla_kino

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

pip install -r requirements.txt
cp .env.example .env           # keyin .env ni to'ldiring
python main.py
```

Bot birinchi ishga tushganda bazani o'zi yaratadi. Eski versiyadagi bazangiz bo'lsa, u ham avtomatik yangilanadi (ma'lumotlar o'chmaydi). Xohlasangiz, avval zaxira nusxa olib yangilash uchun:

```bash
python migrate_db.py
```

## ⚙️ `.env` parametrlari

| Parametr | Majburiy | Tavsif |
|---|---|---|
| `BOT_TOKEN` | ✅ | Bot tokeni |
| `ADMIN_IDS` | ✅ | Admin Telegram ID lari, vergul bilan: `111,222` |
| `PRIVATE_CHANNEL_ID` | ✅ | Kinolar yuklanadigan maxfiy kanal ID si (`-100...`). Boshqa kanallardan kelgan postlar e'tiborsiz qoldiriladi |
| `TMDB_API_KEY` | — | TMDB API kaliti |
| `FORCE_CHANNEL_ID` | — | Majburiy obuna kanali ID si |
| `FORCE_CHANNEL_LINK` | — | Shu kanal havolasi. Bo'sh bo'lsa, bot o'zi aniqlaydi |
| `FORCE_CHANNEL_CHECK` | — | `true` / `false` — boshlang'ich holat (keyin admin paneldan o'zgartiriladi) |
| `DB_FILE` | — | Baza fayli (standart: `movies.db`) |

## 🎮 Foydalanish

### Kino qo'shish
Maxfiy kanalga video (yoki hujjat) yuboring, caption:

```
123
Kino nomi
```

1-qatordagi raqam — kod, 2-qator — nom. Shu kod bilan qayta yuborilsa, kino yangilanadi (ko'rishlar soni saqlanadi).

### Komandalar

| Komanda | Kim uchun | Vazifasi |
|---|---|---|
| `/start` | hamma | Bosh menyu |
| `/help` | hamma | Yordam |
| `/random` | hamma | Tasodifiy kino |
| `/admin` | admin | Admin paneli |
| `/list` | admin | Barcha kinolar |
| `/delete <kod>` | admin | Kinoni o'chirish |
| `/edit <kod> <maydon> <qiymat>` | admin | Tahrirlash. Maydonlar: `title`, `year`, `genre`, `duration`, `description`, `country`, `language`, `poster_url`. Qiymatni tozalash: `-` |
| `/tmdb <kod>` | admin | Ma'lumotlarni TMDB dan qayta olish |
| `/cancel` | admin | Joriy amalni bekor qilish |

Misol: `/edit 12 year 2019`, `/edit 12 genre Drama, Romance`

## 📁 Fayl tuzilishi

```
yukla_kino/
├── main.py                 # Ishga tushirish, routerlar
├── config.py               # .env sozlamalari
├── database.py             # Async SQLite (aiosqlite) + FTS5
├── utils.py                # Matn formatlash, kino yuborish, janrlar ro'yxati
├── migrate_db.py           # Zaxira nusxa bilan bazani yangilash
├── handlers/
│   ├── admin.py            # Admin paneli va komandalar
│   ├── channel.py          # Kanaldan kino qabul qilish, obunachilarga xabar
│   ├── inline.py           # Inline qidiruv
│   └── user.py             # Foydalanuvchi menyusi va qidiruv
├── keyboards/inline.py     # Inline tugmalar
├── middlewares/
│   ├── db.py               # Bazani handlerlarga uzatish
│   └── channel_check.py    # Majburiy obuna tekshiruvi
└── services/tmdb.py        # TMDB API
```

## 🐛 Muammolar

**Kanalga yuborilgan kino saqlanmayapti**
- Bot kanalda admin ekanini tekshiring
- `PRIVATE_CHANNEL_ID` aynan shu kanal ID si ekanini tekshiring
- Caption 1-qatorida raqamli kod borligini tekshiring

**Majburiy obuna ishlamayapti**
- Bot `FORCE_CHANNEL_ID` kanalida admin bo'lishi kerak (aks holda tekshiruv o'tkazib yuboriladi va logda xato chiqadi)

**Inline rejim ishlamayapti**
- @BotFather → `/setinline` orqali inline rejimni yoqing

## 🔒 Xavfsizlik

- `.env` faylini hech qachon GitHub'ga yuklamang (`.gitignore` da bor)
- Token oshkor bo'lib qolsa, @BotFather → `/revoke` orqali yangisini oling
