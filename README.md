# 🎬 Telegram Kino Bot

Zamonaviy, qulay va kengaytiriladigan Telegram kino boti. Kod bo'yicha va nom bo'yicha qidirish, kategoriyalar, inline rejim va boshqa ko'plab funksiyalar.

## ✨ Xususiyatlar

### Foydalanuvchilar uchun
- **Kod bo'yicha qidirish**: Kod yuboring, kino yuboriladi
- **Nom bo'yicha qidirish**: Kino nomini yozing, natijalar chiqadi (FTS5 fuzzy search)
- **Sahifalash**: Natijalar inline tugmalar bilan, 5 tadan, "Oldingi/Keyingi" bilan
- **Kategoriyalar**: Janr, yil, davlat bo'yicha filtr
- **Yangilar va Top 10**: Eng so'nggi va eng ko'p ko'rilgan kinolar
- **Inline rejim**: Istalgan chatda @botnomi kino nomi yozing
- **Kino kartochkasi**: Poster, nom, yil, janr, davomiyligi, mazmun
- **Sevimlilar**: Sevimli kinolarni saqlash
- **Keyin ko'raman**: Keyin ko'rishni rejalashtirish
- **Ko'rishlar hisobi**: Har bir kinoni ko'rishlar soni

### Adminlar uchun
- **Kino qo'shish**: Kanalga yuboring, avtomatik saqlanadi
- **TMDB integratsiya**: Kino ma'lumotlari avtomatik to'ldiriladi
- **Kino tahrirlash/o'chirish**: Kod bo'yicha boshqarish
- **Statistika**: Foydalanuvchilar, yangi foydalanuvchilar, eng ko'p ko'rilgan kinolar
- **Ommaviy xabar**: Barcha foydalanuvchilarga xabar yuborish (flood limit bilan)
- **Majburiy kanal**: Kanal obuna tekshiruvi (yoqish/o'chirish mumkin)

### Texnik xususiyatlar
- **aiogram 3**: Zamonaviy async kutubxona
- **aiosqlite**: Async SQLite ma'lumotlar bazasi
- **FTS5**: Full-text search qidiruv
- **Modular strukturasi**: handlers, keyboards, services, middlewares
- **FSM (Finite State Machine)**: Admin panel uchun holatlar
- **TMDB API**: Kino ma'lumotlari uchun
- **.env konfiguratsiya**: Barcha sozlamalar faylda

## 📋 Talablar

- Python 3.8+
- Telegram bot tokeni (@BotFather dan oling)
- Maxfiy Telegram kanal ID (kinolar uchun)
- TMDB API kaliti (ixtiyoriy, kino ma'lumotlari uchun)

## 🚀 O'rnatish

1. **Repozitoriyani kloning**
```bash
git clone <repository-url>
cd yukla_kino
```

2. **Virtual muhit yaratish**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

3. **Qaramliklarni o'rnatish**
```bash
pip install -r requirements.txt
```

4. **Konfiguratsiya**
```bash
cp .env.example .env
```

`.env` faylini oching va quyidagilarni to'ldiring:
```
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=7770204757
PRIVATE_CHANNEL_ID=-1001234567890
TMDB_API_KEY=your_tmdb_api_key_here
FORCE_CHANNEL_ID=-1001234567890
FORCE_CHANNEL_CHECK=false
```

5. **Ma'lumotlar bazasini migratsiya qilish** (agar eski bazangiz bo'lsa)
```bash
python migrate_db.py
```

6. **Botni ishga tushirish**
```bash
python main.py
```

## 🎮 Foydalanish

### Foydalanuvchilar uchun

1. **Botni boshlash**: `/start`
2. **Kod yuborish**: Masalan, `123`
3. **Nom bo'yicha qidirish**: Kino nomini yozing
4. **Inline rejim**: Istalgan chatda `@botnomi kino nomi`
5. **Menyu**: Asosiy menyu orqali qidirish, yangilar, top 10, sevimlilar

### Adminlar uchun

1. **Admin paneli**: `/admin`
2. **Kino qo'shish**: 
   - Kanalga kinoni yuboring (caption: 1-qator - kod, 2-qator - nom)
   - Yoki admin panel orqali kino nomini yozing (TMDB dan ma'lumot olinadi)
3. **Kino o'chirish**: `/delete <kod>`
4. **Barcha kinolar**: `/list`
5. **Ommaviy xabar**: Admin panel orqali
6. **Statistika**: Admin panel orqali

## 📁 Fayl tuzilishi

```
yukla_kino/
├── main.py                 # Asosiy bot fayli
├── config.py               # Konfiguratsiya
├── database.py             # Async SQLite ma'lumotlar bazasi
├── migrate_db.py           # Migratsiya skripti
├── requirements.txt        # Python qaramliklari
├── .env.example            # Konfiguratsiya namunasi
├── .env                    # Konfiguratsiya (yaratilishi kerak)
├── movies.db               # Ma'lumotlar bazasi (avtomatik yaratiladi)
├── handlers/               # Handlerlar
│   ├── __init__.py
│   ├── user.py            # Foydalanuvchi handlerlari
│   ├── admin.py           # Admin handlerlari
│   ├── channel.py         # Kanal handleri
│   └── inline.py          # Inline handler
├── keyboards/             # Tugmalar
│   ├── __init__.py
│   └── inline.py          # Inline tugmalar
├── services/              # Xizmatlar
│   ├── __init__.py
│   └── tmdb.py            # TMDB API service
└── middlewares/           # Middlewarelar
    ├── __init__.py
    ├── db.py              # Database middleware
    └── channel_check.py   # Kanal tekshiruvi middleware
```

## 🔧 Sozlamalar

### .env fayl parametrlari

- `BOT_TOKEN`: Telegram bot tokeni (majburiy)
- `ADMIN_IDS`: Admin Telegram IDlari, vergul bilan ajratilgan (majburiy)
- `PRIVATE_CHANNEL_ID`: Maxfiy kanal ID (kinolar uchun)
- `TMDB_API_KEY`: TMDB API kaliti (ixtiyoriy, kino ma'lumotlari uchun)
- `FORCE_CHANNEL_ID`: Majburiy obuna kanal ID (ixtiyoriy)
- `FORCE_CHANNEL_CHECK`: Majburiy obuna tekshiruvi (true/false, default: false)

## 🔒 Xavfsizlik

- `.env` faylini hech kimga bermang
- Admin IDlarni to'g'ri kiriting
- Bot tokenni maxfiy saqlang
- TMDB API kalitini maxfiy saqlang

## 🐛 Muammolar

**Bot ishlamayapti:**
- `.env` fayl to'g'ri yaratilganligini tekshiring
- Bot token to'g'ri ekanligini tasdiqlang
- Admin IDlari to'g'ri ekanligini tekshiring
- Qaramliklarni o'rnatganingizni tekshiring

**Kino yuborilmayapti:**
- File ID to'g'ri ekanligini tekshiring
- Kino kanalda mavjudligini tasdiqlang
- Bot kanalga admin ekanligini tekshiring

**TMDB ishlamayapti:**
- API kalit to'g'ri ekanligini tekshiring
- API kalit aktiv ekanligini tasdiqlang

## 📞 Yordam

Qo'shimcha ma'lumot uchun:
- `/help` - Yordam
- `/start` - Boshlash

## 📄 Litsenziya

Bu loyiha ochiq kodli va erkin foydalanish mumkin.

## 🤝 Qo'shgan hissa

Agar loyihaga qo'shmoqchi bo'lsangiz, pull request yuboring.
