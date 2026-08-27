# 🎬 Telegram Kino Bot

Maxfiy Telegram kanaldagi kinolarni kod orqali tarqatuvchi Telegram bot.

## ✨ Xususiyatlar

- **Kodga asoslangan tarqatish**: Har bir kinoga unikal kod biriktiriladi (masalan: 123)
- **Avtomatik yuborish**: Foydalanuvchi kod yuborsa, bot kinoni avtomatik topib yuboradi
- **Admin paneli**: Kinolarni qo'shish, o'chirish va boshqarish imkoniyati
- **SQLite ma'lumotlar bazasi**: Kod → kino bog'lanishi saqlanadi
- **Xavfsiz**: Faqat adminlar kino qo'shishi mumkin

## 📋 Talablar

- Python 3.8+
- Telegram bot tokeni (@BotFather dan oling)
- Maxfiy Telegram kanal ID

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
- `BOT_TOKEN`: @BotFather dan olingan token
- `ADMIN_IDS`: Admin Telegram IDlari (vergul bilan ajratilgan)
- `PRIVATE_CHANNEL_ID`: Maxfiy kanal ID (ixtiyoriy)

## 🎮 Foydalanish

### Foydalanuvchilar uchun

1. Botni boshlash: `/start`
2. Kodni yuborish (masalan: `123`)
3. Bot kinoni avtomatik yuboradi

### Adminlar uchun

#### Kino qo'shish
```
/add <kod> <file_id> [<nomi>]
```
Masalan:
```
/add 123 BAADqwADKwADBQACZQAA  Avatar
```

**File ID ni qanday olish:**
1. Kinoni maxfiy kanalga yuboring
2. Kinoni forward qilib botga yuboring
3. Bot file_id ni qaytaradi (yoki @GetMyIdBot orqali olish)

#### Kino o'chirish
```
/delete <kod>
```
Masalan:
```
/delete 123
```

#### Barcha kinolarni ko'rish
```
/list
```

#### Statistika
```
/stats
```

## 📁 Fayl tuzilishi

```
yukla_kino/
├── main.py           # Asosiy bot fayli
├── database.py       # SQLite ma'lumotlar bazasi
├── config.py         # Konfiguratsiya
├── requirements.txt  # Python qaramliklari
├── .env.example      # Konfiguratsiya namunasi
├── .env              # Konfiguratsiya (yaratilishi kerak)
└── movies.db         # Ma'lumotlar bazasi (avtomatik yaratiladi)
```

## 🔒 Xavfsizlik

- `.env` faylini hech kimga bermang
- Admin IDlarni to'g'ri kiriting
- Bot tokenni maxfiy saqlang

## 🐛 Muammolar

**Bot ishlamayapti:**
- `.env` fayl to'g'ri yaratilganligini tekshiring
- Bot token to'g'ri ekanligini tasdiqlang
- Admin IDlari to'g'ri ekanligini tekshiring

**Kino yuborilmayapti:**
- File ID to'g'ri ekanligini tekshiring
- Kino kanalda mavjudligini tasdiqlang

## 📞 Yordam

Qo'shimcha ma'lumot uchun:
- `/help` - Yordam
- `/start` - Boshlash

## 📄 Litsenziya

Bu loyiha ochiq kodli va erkin foydalanish mumkin.
