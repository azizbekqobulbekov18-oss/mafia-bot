# 🎮 Mafiya Telegram Bot

Mukammal Mafiya o'yin boti — strategiya, aldash va mantiq!

## 🎭 Rollar
| Rol | Vazifa |
|-----|--------|
| 🔫 Mafiya | Har kecha bir odamni o'ldiradi |
| 🕵️ Dedektiv | Har kecha kimdir mafiyami tekshiradi |
| 👨‍⚕️ Shifokor | Har kecha kimnidir davolaydi |
| 👤 Fuqaro | Ovoz berish orqali mafiyani topadi |

## 🚀 Render.com'ga Deploy

### 1. BotFather'dan token oling
- Telegram'da @BotFather ga yozing
- `/newbot` buyrug'ini yuboring
- Token nusxalab oling

### 2. GitHub'ga yuklang
```bash
git init
git add .
git commit -m "Mafiya bot"
git push origin main
```

### 3. Render.com sozlamalari
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python bot.py`
- **Environment Variable:** `BOT_TOKEN` = sizning tokeningiz

## 🎮 Bot Buyruqlari
| Buyruq | Vazifa |
|--------|--------|
| `/newgame` | Yangi o'yin boshlash (guruhda) |
| `/status` | O'yin holati |
| `/endgame` | O'yinni tugatish (boshlovchi) |
| `/start` | Bot bilan tanishish |

## 📋 O'yin Tartibi
1. Guruhda `/newgame` yozing
2. O'yinchilar "Qo'shilish" tugmasini bosadi (min 4 kishi)
3. Boshlovchi "O'yinni boshlash" tugmasini bosadi
4. Botdan xususiy xabarda rolni qabul qiling
5. **Kecha:** Mafiya, Dedektiv, Shifokor harakatlanadi
6. **Kunduz:** Minnat qilish va ovoz berish
7. G'alaba shartlari bajarilgunicha davom etadi

## 🏆 G'alaba Shartlari
- **Fuqarolar:** Barcha mafiyachilarni chiqarib yuborsa
- **Mafiya:** Fuqarolar bilan teng yoki ko'p bo'lib qolsa
