#!/usr/bin/env python3
"""
🎭 Mafia Game Bot
Group & Solo mode | UZ/RU/EN | Admin panel
"""

import os
import random
import asyncio
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
from flask import Flask
import threading

# ─────────────────────────────────────────────
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8967307684:AAF48NYpJZf9pmtsbbqrDLoCoPaFhMuM8kI")
ADMIN_IDS = [8397484222]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# FLASK KEEP-ALIVE
# ─────────────────────────────────────────────
app = Flask(__name__)

@app.route("/")
def home():
    return "Mafia Bot is running!"

@app.route("/health")
def health():
    return {"status": "running", "game": "mafia"}

def run_flask():
    app.run(host="0.0.0.0", port=5000)

# ─────────────────────────────────────────────
# TRANSLATIONS
# ─────────────────────────────────────────────
TX = {
    "uz": {
        "welcome": "🎭 <b>Mafia O'yiniga Xush Kelibsiz!</b>\n\nGuruhda o'ynash uchun /newgame\nYakka o'ynash uchun /solo",
        "new_game": "🎭 <b>Yangi Mafia o'yini boshlandi!</b>\n\n/join - O'yinga qo'shiling\n/startgame - O'yinni boshlash (min 4 o'yinchi)",
        "joined": "✅ {name} o'yinga qo'shildi! ({count}/10)",
        "already_joined": "⚠️ Siz allaqachon o'yinda!", 
        "game_started": "🎮 O'yin boshlandi! Rollar taqsimlanmoqda...",
        "not_enough": "⚠️ Kamida 4 o'yinchi kerak! Hozir: {count}",
        "your_role": "🎭 Sizning rolingiz: {role}",
        "day_phase": "☀️ <b>Kun - {day}-kun</b>\n\nO'yinchilar ovoz berishsin!\nKimni yo'q qilmoqchisiz?\n\n🧑‍🤝‍🧑 Tirik o'yinchilar:\n{players}",
        "night_phase": "🌙 <b>Kecha keldi</b>\n\nBarcha ko'zlarini yumsing...",
        "mafia_wins": "🔴 <b>Mafia g'alaba qildi!</b>\n\nMafiachilar: {mafia}",
        "civilians_win": "🔵 <b>Tinch aholisi g'alaba qildi!</b>\n\nBarcha mafiachilar yo'q qilindi!",
        "eliminated": "☠️ {name} o'yindan chiqarildi! U {role} edi.",
        "vote": "🗳 Ovoz bering:",
        "no_game": "⚠️ Hozir o'yin yo'q! /newgame yozing.",
        "rules": (
            "📖 <b>Mafia O'yini Qoidalari</b>\n\n"
            "🔴 <b>Mafia</b> — har kecha bir o'yinchini o'ldiradi\n"
            "🔵 <b>Tinch aholi</b> — mafiani topib ovoz bilan chiqaradi\n"
            "💚 <b>Doktor</b> — har kecha bir o'yinchini himoya qiladi\n"
            "🔍 <b>Detektiv</b> — har kecha bir o'yinchining rolini biladi\n\n"
            "🏆 <b>G'alaba:</b>\n"
            "• Mafia: tinch aholi soni ≤ mafia soni\n"
            "• Tinch aholi: barcha mafiachilar chiqarilsa"
        ),
        "stats": "📊 <b>Sizning statistikangiz:</b>\n🎮 O'yinlar: {games}\n🏆 G'alabalar: {wins}\n💀 Mag'lubiyatlar: {losses}",
        "lang_set": "✅ Til O'zbek tiliga o'rnatildi!",
        "choose_lang": "🌐 Tilni tanlang:",
        "solo_start": "🎮 <b>Solo o'yin boshlandi!</b>\nSiz tinch aholisiz. AI botilar bilan o'ynaysiz!",
        "admin_panel": "🛡 <b>Admin Panel</b>",
        "not_admin": "❌ Siz admin emassiz!",
    },
    "ru": {
        "welcome": "🎭 <b>Добро пожаловать в Мафию!</b>\n\nДля игры в группе: /newgame\nДля соло игры: /solo",
        "new_game": "🎭 <b>Новая игра в Мафию началась!</b>\n\n/join - Присоединиться\n/startgame - Начать игру (мин 4 игрока)",
        "joined": "✅ {name} присоединился! ({count}/10)",
        "already_joined": "⚠️ Вы уже в игре!",
        "game_started": "🎮 Игра началась! Раздаём роли...",
        "not_enough": "⚠️ Нужно минимум 4 игрока! Сейчас: {count}",
        "your_role": "🎭 Ваша роль: {role}",
        "day_phase": "☀️ <b>День - {day}-й день</b>\n\nГолосуйте за подозреваемого!\n\n🧑‍🤝‍🧑 Живые игроки:\n{players}",
        "night_phase": "🌙 <b>Наступила ночь</b>\n\nВсе закрывают глаза...",
        "mafia_wins": "🔴 <b>Мафия победила!</b>\n\nМафиози: {mafia}",
        "civilians_win": "🔵 <b>Мирные жители победили!</b>\n\nВся мафия устранена!",
        "eliminated": "☠️ {name} выбыл! Он был {role}.",
        "vote": "🗳 Голосуйте:",
        "no_game": "⚠️ Сейчас нет игры! Напишите /newgame.",
        "rules": (
            "📖 <b>Правила Мафии</b>\n\n"
            "🔴 <b>Мафия</b> — каждую ночь убивает игрока\n"
            "🔵 <b>Мирные</b> — голосуют за мафию\n"
            "💚 <b>Доктор</b> — каждую ночь спасает игрока\n"
            "🔍 <b>Детектив</b> — узнаёт роль игрока\n\n"
            "🏆 <b>Победа:</b>\n"
            "• Мафия: мирных ≤ мафии\n"
            "• Мирные: вся мафия устранена"
        ),
        "stats": "📊 <b>Ваша статистика:</b>\n🎮 Игр: {games}\n🏆 Побед: {wins}\n💀 Поражений: {losses}",
        "lang_set": "✅ Язык установлен: Русский!",
        "choose_lang": "🌐 Выберите язык:",
        "solo_start": "🎮 <b>Соло игра началась!</b>\nВы мирный житель. Играете с AI ботами!",
        "admin_panel": "🛡 <b>Панель администратора</b>",
        "not_admin": "❌ Вы не администратор!",
    },
    "en": {
        "welcome": "🎭 <b>Welcome to Mafia Game!</b>\n\nFor group play: /newgame\nFor solo play: /solo",
        "new_game": "🎭 <b>New Mafia game started!</b>\n\n/join - Join the game\n/startgame - Start (min 4 players)",
        "joined": "✅ {name} joined! ({count}/10)",
        "already_joined": "⚠️ You already joined!",
        "game_started": "🎮 Game started! Assigning roles...",
        "not_enough": "⚠️ Need at least 4 players! Now: {count}",
        "your_role": "🎭 Your role: {role}",
        "day_phase": "☀️ <b>Day - Day {day}</b>\n\nVote to eliminate!\n\n🧑‍🤝‍🧑 Alive players:\n{players}",
        "night_phase": "🌙 <b>Night has fallen</b>\n\nEveryone close your eyes...",
        "mafia_wins": "🔴 <b>Mafia wins!</b>\n\nMafia members: {mafia}",
        "civilians_win": "🔵 <b>Civilians win!</b>\n\nAll mafia eliminated!",
        "eliminated": "☠️ {name} was eliminated! They were {role}.",
        "vote": "🗳 Vote:",
        "no_game": "⚠️ No game running! Type /newgame.",
        "rules": (
            "📖 <b>Mafia Game Rules</b>\n\n"
            "🔴 <b>Mafia</b> — kills one player each night\n"
            "🔵 <b>Civilians</b> — vote to eliminate mafia\n"
            "💚 <b>Doctor</b> — saves one player each night\n"
            "🔍 <b>Detective</b> — investigates one player each night\n\n"
            "🏆 <b>Win condition:</b>\n"
            "• Mafia: civilians ≤ mafia count\n"
            "• Civilians: all mafia eliminated"
        ),
        "stats": "📊 <b>Your stats:</b>\n🎮 Games: {games}\n🏆 Wins: {wins}\n💀 Losses: {losses}",
        "lang_set": "✅ Language set to English!",
        "choose_lang": "🌐 Choose language:",
        "solo_start": "🎮 <b>Solo game started!</b>\nYou are a civilian. Playing against AI bots!",
        "admin_panel": "🛡 <b>Admin Panel</b>",
        "not_admin": "❌ You are not an admin!",
    }
}

ROLES = {
    "uz": {"mafia": "🔴 Mafiachi", "civilian": "🔵 Tinch aholi", "doctor": "💚 Doktor", "detective": "🔍 Detektiv"},
    "ru": {"mafia": "🔴 Мафия", "civilian": "🔵 Мирный", "doctor": "💚 Доктор", "detective": "🔍 Детектив"},
    "en": {"mafia": "🔴 Mafia", "civilian": "🔵 Civilian", "doctor": "💚 Doctor", "detective": "🔍 Detective"},
}

# ─────────────────────────────────────────────
# STORAGE
# ─────────────────────────────────────────────
users_db = {}
games = {}  # chat_id -> game_state
stats_db = {}  # user_id -> {games, wins, losses}

def get_lang(uid):
    return users_db.get(uid, {}).get("lang", "uz")

def tx(uid, key, **kw):
    text = TX.get(get_lang(uid), TX["uz"]).get(key, key)
    return text.format(**kw) if kw else text

def ensure_user(uid, name=""):
    if uid not in users_db:
        users_db[uid] = {"lang": "uz", "name": name}
    if uid not in stats_db:
        stats_db[uid] = {"games": 0, "wins": 0, "losses": 0}

def lang_kb():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang_uz"),
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
    ]])

def assign_roles(player_count):
    roles = []
    mafia_count = max(1, player_count // 4)
    roles.extend(["mafia"] * mafia_count)
    if player_count >= 5:
        roles.append("doctor")
    if player_count >= 7:
        roles.append("detective")
    while len(roles) < player_count:
        roles.append("civilian")
    random.shuffle(roles)
    return roles

# ─────────────────────────────────────────────
# COMMANDS
# ─────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ensure_user(uid, update.effective_user.first_name)
    await update.message.reply_text(tx(uid, "welcome"), parse_mode="HTML")

async def cmd_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ensure_user(uid)
    await update.message.reply_text(tx(uid, "choose_lang"), reply_markup=lang_kb())

async def cmd_rules(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ensure_user(uid)
    await update.message.reply_text(tx(uid, "rules"), parse_mode="HTML")

async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ensure_user(uid)
    s = stats_db[uid]
    await update.message.reply_text(
        tx(uid, "stats", games=s["games"], wins=s["wins"], losses=s["losses"]),
        parse_mode="HTML"
    )

async def cmd_newgame(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    ensure_user(uid, update.effective_user.first_name)
    
    games[chat_id] = {
        "players": {},
        "roles": {},
        "alive": [],
        "day": 0,
        "phase": "lobby",
        "votes": {},
        "creator": uid
    }
    
    await update.message.reply_text(tx(uid, "new_game"), parse_mode="HTML")

async def cmd_join(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    name = update.effective_user.first_name
    ensure_user(uid, name)
    
    if chat_id not in games:
        await update.message.reply_text(tx(uid, "no_game"))
        return
    
    game = games[chat_id]
    if uid in game["players"]:
        await update.message.reply_text(tx(uid, "already_joined"))
        return
    
    game["players"][uid] = name
    count = len(game["players"])
    await update.message.reply_text(tx(uid, "joined", name=name, count=count))

async def cmd_startgame(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    ensure_user(uid)
    
    if chat_id not in games:
        await update.message.reply_text(tx(uid, "no_game"))
        return
    
    game = games[chat_id]
    count = len(game["players"])
    
    if count < 4:
        await update.message.reply_text(tx(uid, "not_enough", count=count))
        return
    
    await update.message.reply_text(tx(uid, "game_started"), parse_mode="HTML")
    
    # Assign roles
    player_ids = list(game["players"].keys())
    role_list = assign_roles(count)
    
    for i, pid in enumerate(player_ids):
        role = role_list[i]
        game["roles"][pid] = role
        game["alive"].append(pid)
        
        role_name = ROLES[get_lang(pid)][role]
        try:
            await ctx.bot.send_message(
                pid,
                tx(pid, "your_role", role=role_name),
                parse_mode="HTML"
            )
        except:
            pass
    
    game["phase"] = "day"
    game["day"] = 1
    
    await asyncio.sleep(3)
    await start_day_phase(update, ctx, chat_id)

async def start_day_phase(update, ctx, chat_id):
    game = games[chat_id]
    uid = list(game["players"].keys())[0]
    
    alive_names = [game["players"][pid] for pid in game["alive"]]
    players_text = "\n".join([f"• {name}" for name in alive_names])
    
    # Vote buttons
    buttons = []
    for pid in game["alive"]:
        buttons.append([InlineKeyboardButton(
            f"☠️ {game['players'][pid]}",
            callback_data=f"vote_{pid}"
        )])
    
    kb = InlineKeyboardMarkup(buttons)
    
    await ctx.bot.send_message(
        chat_id,
        tx(uid, "day_phase", day=game["day"], players=players_text),
        parse_mode="HTML",
        reply_markup=kb
    )

async def cmd_top(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ensure_user(uid)
    
    sorted_players = sorted(stats_db.items(), key=lambda x: x[1]["wins"], reverse=True)[:10]
    
    text = "🏆 <b>Top O'yinchilar:</b>\n\n"
    for i, (pid, s) in enumerate(sorted_players, 1):
        name = users_db.get(pid, {}).get("name", "Noma'lum")
        text += f"{i}. {name} — {s['wins']} g'alaba\n"
    
    await update.message.reply_text(text, parse_mode="HTML")

async def cmd_solo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ensure_user(uid, update.effective_user.first_name)
    
    # Create AI players
    ai_players = ["🤖 Bot-1", "🤖 Bot-2", "🤖 Bot-3", "🤖 Bot-4", "🤖 Bot-5"]
    
    game = {
        "players": {uid: update.effective_user.first_name},
        "roles": {},
        "alive": [uid],
        "day": 1,
        "phase": "day",
        "votes": {},
        "ai_players": ai_players,
        "solo": True
    }
    
    for i, bot_name in enumerate(ai_players):
        fake_id = -(i + 1)
        game["players"][fake_id] = bot_name
        game["alive"].append(fake_id)
    
    # Assign roles
    all_players = list(game["players"].keys())
    roles = assign_roles(len(all_players))
    for i, pid in enumerate(all_players):
        game["roles"][pid] = roles[i]
    
    games[uid] = game
    
    role_name = ROLES[get_lang(uid)][game["roles"][uid]]
    
    await update.message.reply_text(
        tx(uid, "solo_start") + f"\n\n{tx(uid, 'your_role', role=role_name)}",
        parse_mode="HTML"
    )

async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        await update.message.reply_text(tx(uid, "not_admin"))
        return
    
    total_users = len(users_db)
    total_games = sum(s["games"] for s in stats_db.values())
    active_games = len(games)
    
    text = (
        f"🛡 <b>Admin Panel</b>\n\n"
        f"👤 Foydalanuvchilar: {total_users}\n"
        f"🎮 Jami o'yinlar: {total_games}\n"
        f"🟢 Faol o'yinlar: {active_games}"
    )
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="admin_users")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")],
    ])
    
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb)

async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    data = query.data
    await query.answer()
    
    if data.startswith("lang_"):
        lang = data.split("_")[1]
        users_db.setdefault(uid, {})["lang"] = lang
        await query.edit_message_text(tx(uid, "lang_set"))
    
    elif data.startswith("vote_"):
        target_id = int(data.split("_")[1])
        chat_id = update.effective_chat.id
        
        if chat_id not in games:
            return
        
        game = games[chat_id]
        game["votes"][uid] = target_id
        
        # Check if all voted
        alive_real = [p for p in game["alive"] if p > 0]
        if len(game["votes"]) >= len(alive_real):
            # Count votes
            vote_count = {}
            for v in game["votes"].values():
                vote_count[v] = vote_count.get(v, 0) + 1
            
            eliminated = max(vote_count, key=vote_count.get)
            eliminated_name = game["players"][eliminated]
            eliminated_role = ROLES[get_lang(uid)][game["roles"][eliminated]]
            
            game["alive"].remove(eliminated)
            game["votes"] = {}
            
            await ctx.bot.send_message(
                chat_id,
                tx(uid, "eliminated", name=eliminated_name, role=eliminated_role),
                parse_mode="HTML"
            )
            
            # Check win condition
            mafia_alive = [p for p in game["alive"] if game["roles"][p] == "mafia"]
            civilian_alive = [p for p in game["alive"] if game["roles"][p] != "mafia"]
            
            if len(mafia_alive) == 0:
                await ctx.bot.send_message(chat_id, tx(uid, "civilians_win"), parse_mode="HTML")
                del games[chat_id]
            elif len(mafia_alive) >= len(civilian_alive):
                mafia_names = ", ".join([game["players"][p] for p in mafia_alive])
                await ctx.bot.send_message(
                    chat_id,
                    tx(uid, "mafia_wins", mafia=mafia_names),
                    parse_mode="HTML"
                )
                del games[chat_id]
            else:
                game["day"] += 1
                await start_day_phase(update, ctx, chat_id)
    
    elif data == "admin_users":
        if uid not in ADMIN_IDS:
            return
        text = f"👥 <b>Foydalanuvchilar: {len(users_db)}</b>\n\n"
        for pid, info in list(users_db.items())[:20]:
            text += f"• {info.get('name', 'N/A')} (ID: {pid})\n"
        await query.edit_message_text(text, parse_mode="HTML")
    
    elif data == "admin_stats":
        if uid not in ADMIN_IDS:
            return
        total_games = sum(s["games"] for s in stats_db.values())
        text = f"📊 <b>Statistika</b>\n\n👤 Users: {len(users_db)}\n🎮 Games: {total_games}"
        await query.edit_message_text(text, parse_mode="HTML")

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("lang", cmd_lang))
    application.add_handler(CommandHandler("rules", cmd_rules))
    application.add_handler(CommandHandler("stats", cmd_stats))
    application.add_handler(CommandHandler("newgame", cmd_newgame))
    application.add_handler(CommandHandler("join", cmd_join))
    application.add_handler(CommandHandler("startgame", cmd_startgame))
    application.add_handler(CommandHandler("top", cmd_top))
    application.add_handler(CommandHandler("solo", cmd_solo))
    application.add_handler(CommandHandler("admin", cmd_admin))
    application.add_handler(CallbackQueryHandler(on_callback))
    
    logger.info("🎭 Mafia Bot ishga tushdi!")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
