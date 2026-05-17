import os
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# ===================== O'YIN HOLATI =====================
games = {}  # chat_id -> GameState

ROLES = {
    "mafia": "🔫 Mafiya",
    "detective": "🕵️ Dedektiv",
    "doctor": "👨‍⚕️ Shifokor",
    "citizen": "👤 Fuqaro",
}

ROLE_DESCRIPTIONS = {
    "mafia": "Har kecha bir fuqaroni o'ldirish. Mafiyachilar bir-birini bilishadi.",
    "detective": "Har kecha bir odamni tekshirish. Mafiyami yoki yo'qligini bilasiz.",
    "doctor": "Har kecha bir odamni davolash. O'zingizni ham davolashingiz mumkin.",
    "citizen": "Ovoz berish orqali mafiyachilarni topib, shahardan chiqarib yuboring.",
}

PHASES = ["lobby", "night", "day", "vote", "ended"]


class Player:
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name
        self.role = None
        self.alive = True
        self.voted_for = None
        self.night_action = None

    def mention(self):
        return f"[{self.name}](tg://user?id={self.user_id})"


class GameState:
    def __init__(self, chat_id, host_id):
        self.chat_id = chat_id
        self.host_id = host_id
        self.players = {}  # user_id -> Player
        self.phase = "lobby"
        self.day_number = 0
        self.votes = {}
        self.night_actions = {}
        self.eliminated_today = None
        self.messages_to_delete = []

    def alive_players(self):
        return [p for p in self.players.values() if p.alive]

    def mafia_players(self):
        return [p for p in self.alive_players() if p.role == "mafia"]

    def citizen_players(self):
        return [p for p in self.alive_players() if p.role != "mafia"]

    def assign_roles(self):
        player_list = list(self.players.values())
        random.shuffle(player_list)
        n = len(player_list)

        # Rol taqsimoti
        mafia_count = max(1, n // 4)
        has_detective = n >= 5
        has_doctor = n >= 6

        roles = ["mafia"] * mafia_count
        if has_detective:
            roles.append("detective")
        if has_doctor:
            roles.append("doctor")
        while len(roles) < n:
            roles.append("citizen")

        random.shuffle(roles)
        for player, role in zip(player_list, roles):
            player.role = role

    def check_win(self):
        alive = self.alive_players()
        mafia = self.mafia_players()
        citizens = self.citizen_players()

        if len(mafia) == 0:
            return "citizens"
        if len(mafia) >= len(citizens):
            return "mafia"
        return None


# ===================== YORDAMCHI FUNKSIYALAR =====================

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 O'yin boshlash", callback_data="start_game")],
        [InlineKeyboardButton("📖 Qoidalar", callback_data="rules")],
    ])


def join_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✋ Qo'shilish", callback_data="join")],
        [InlineKeyboardButton("🚀 O'yinni boshlash", callback_data="begin")],
    ])


async def send_role_privately(app, player, game):
    role_name = ROLES[player.role]
    description = ROLE_DESCRIPTIONS[player.role]

    if player.role == "mafia":
        teammates = [p.name for p in game.mafia_players() if p.user_id != player.user_id]
        team_info = f"\n\n🤝 *Hamkasblaringiz:* {', '.join(teammates) if teammates else 'Siz yolg\\'izsiz'}"
    else:
        team_info = ""

    text = (
        f"🎭 *Sizning rolingiz:* {role_name}\n\n"
        f"📋 *Vazifangiz:* {description}"
        f"{team_info}"
    )
    try:
        await app.bot.send_message(player.user_id, text, parse_mode="Markdown")
    except Exception:
        pass


# ===================== KOMANDALAR =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🌙 *Mafiya O'yiniga Xush Kelibsiz!*\n\n"
        "Bu klassik Mafiya o'yini — strategiya, aldash va mantiq o'yini.\n\n"
        "Guruhda `/newgame` yozing va o'yin boshlang!"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_keyboard())


async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    if update.effective_chat.type == "private":
        await update.message.reply_text("❌ Bu komanda faqat guruhlarda ishlaydi!")
        return

    if chat_id in games and games[chat_id].phase != "ended":
        await update.message.reply_text("⚠️ Allaqachon o'yin davom etmoqda!")
        return

    game = GameState(chat_id, user.id)
    games[chat_id] = game

    player = Player(user.id, user.first_name)
    game.players[user.id] = player

    text = (
        f"🎮 *Yangi Mafiya O'yini!*\n\n"
        f"👑 Boshlovchi: {user.first_name}\n"
        f"👥 O'yinchilar (1): {user.first_name}\n\n"
        f"✋ Qo'shilish uchun tugmani bosing!\n"
        f"_(Kamida 4 ta o'yinchi kerak)_"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=join_keyboard())


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    user = query.from_user
    data = query.data

    if data == "rules":
        rules_text = (
            "📖 *MAFIYA QOIDALARI*\n\n"
            "🎭 *Rollar:*\n"
            "🔫 Mafiya — kecha o'ldiradi\n"
            "🕵️ Dedektiv — kecha tekshiradi\n"
            "👨‍⚕️ Shifokor — kecha davolaydi\n"
            "👤 Fuqaro — ovoz beradi\n\n"
            "🌙 *Kecha:* Mafiya qurbonini tanlaydi\n"
            "☀️ *Kunduz:* Minnat qilish va ovoz berish\n"
            "🗳️ *Ovoz:* Ko'p ovoz olgan chiqarib yuboriladi\n\n"
            "🏆 *G'alaba:*\n"
            "Fuqarolar — barcha mafiyachilarni toping\n"
            "Mafiya — fuqarolar bilan teng keling"
        )
        await query.message.reply_text(rules_text, parse_mode="Markdown")
        return

    if data == "start_game":
        await query.message.reply_text(
            "Guruhda `/newgame` yozing!", parse_mode="Markdown"
        )
        return

    if chat_id not in games:
        await query.message.reply_text("❌ Faol o'yin yo'q!")
        return

    game = games[chat_id]

    if data == "join":
        if game.phase != "lobby":
            await query.answer("O'yin allaqachon boshlangan!", show_alert=True)
            return
        if user.id in game.players:
            await query.answer("Siz allaqachon ro'yxatdasiz!", show_alert=True)
            return

        game.players[user.id] = Player(user.id, user.first_name)
        names = [p.name for p in game.players.values()]
        text = (
            f"🎮 *Mafiya O'yini — Kutish Xonasi*\n\n"
            f"👥 O'yinchilar ({len(names)}):\n" +
            "\n".join(f"  • {n}" for n in names) +
            "\n\n✋ Ko'proq qo'shilishi mumkin!"
        )
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=join_keyboard())

    elif data == "begin":
        if user.id != game.host_id:
            await query.answer("Faqat boshlovchi o'yinni boshlay oladi!", show_alert=True)
            return
        if len(game.players) < 4:
            await query.answer("Kamida 4 ta o'yinchi kerak!", show_alert=True)
            return

        await start_game(query.message, game, context.application)

    elif data.startswith("vote_"):
        await handle_vote(query, game, context)

    elif data.startswith("night_"):
        await handle_night_action(query, game, context)


async def start_game(message, game, app):
    game.phase = "night"
    game.day_number = 1
    game.assign_roles()

    # Rollari xususiy yuborish
    for player in game.players.values():
        await send_role_privately(app, player, game)

    text = (
        "🎮 *O'YIN BOSHLANDI!*\n\n"
        "🎭 Barcha o'yinchilarga rollar yuborildi.\n"
        "_(Agar xabar kelmagan bo'lsa, botga /start yuboring)_\n\n"
        "🌙 *1-Kecha boshlanmoqda...*\n"
        "Shahar uxlayapti. Mafiya ish boshlamoqda..."
    )
    await message.edit_text(text, parse_mode="Markdown")

    await asyncio.sleep(3)
    await send_night_actions(message.chat_id, game, app)


async def send_night_actions(chat_id, game, app):
    game.night_actions = {}

    for player in game.alive_players():
        if player.role == "mafia":
            targets = [p for p in game.alive_players() if p.role != "mafia"]
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"💀 {p.name}", callback_data=f"night_kill_{p.user_id}")]
                for p in targets
            ])
            try:
                await app.bot.send_message(
                    player.user_id,
                    f"🌙 *{game.day_number}-Kecha*\n\n🔫 Kim o'ldirilsin?",
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
            except Exception:
                pass

        elif player.role == "detective":
            targets = [p for p in game.alive_players() if p.user_id != player.user_id]
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"🔍 {p.name}", callback_data=f"night_check_{p.user_id}")]
                for p in targets
            ])
            try:
                await app.bot.send_message(
                    player.user_id,
                    f"🌙 *{game.day_number}-Kecha*\n\n🕵️ Kimni tekshirasiz?",
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
            except Exception:
                pass

        elif player.role == "doctor":
            targets = game.alive_players()
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"💊 {p.name}", callback_data=f"night_heal_{p.user_id}")]
                for p in targets
            ])
            try:
                await app.bot.send_message(
                    player.user_id,
                    f"🌙 *{game.day_number}-Kecha*\n\n👨‍⚕️ Kimni davolaysiz?",
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
            except Exception:
                pass

    # Guruhga kecha xabarini yuborish
    await app.bot.send_message(
        chat_id,
        f"🌙 *{game.day_number}-Kecha*\n\nShahar uxlayapti...\nO'yinchilar xususiy xabarlarga o'z harakatlarini tanlashsin.",
        parse_mode="Markdown"
    )


async def handle_night_action(query, game, context):
    user = query.from_user
    data = query.data
    app = context.application

    if user.id not in game.players:
        return

    player = game.players[user.id]

    if not player.alive:
        await query.answer("Siz o'lgansiz!", show_alert=True)
        return

    if data.startswith("night_kill_"):
        if player.role != "mafia":
            return
        target_id = int(data.split("_")[2])
        # Barcha mafiyalar ovozi
        game.night_actions[f"kill_{user.id}"] = target_id
        await query.edit_message_text("✅ Tanlov qilindi. Boshqa mafiyachilarni kuting...")

        # Barcha mafiyalar tanlov qildimi?
        mafia = game.mafia_players()
        kill_votes = {v for k, v in game.night_actions.items() if k.startswith("kill_")}
        if len([k for k in game.night_actions if k.startswith("kill_")]) >= len(mafia):
            # Ko'p ovoz olgan qurbon
            from collections import Counter
            count = Counter(v for k, v in game.night_actions.items() if k.startswith("kill_"))
            game.night_actions["kill_target"] = count.most_common(1)[0][0]

    elif data.startswith("night_check_"):
        if player.role != "detective":
            return
        target_id = int(data.split("_")[2])
        game.night_actions["check"] = target_id
        target = game.players.get(target_id)
        if target:
            result = "🔴 MAFIYA!" if target.role == "mafia" else "🟢 Begunoh"
            await query.edit_message_text(
                f"🕵️ *Tekshiruv natijasi:*\n\n{target.name} → {result}",
                parse_mode="Markdown"
            )

    elif data.startswith("night_heal_"):
        if player.role != "doctor":
            return
        target_id = int(data.split("_")[2])
        game.night_actions["heal"] = target_id
        target = game.players.get(target_id)
        await query.edit_message_text(f"💊 {target.name} davolandi!")

    # Kecha tugadimi?
    await check_night_complete(game, app)


async def check_night_complete(game, app):
    mafia = game.mafia_players()
    mafia_voted = len([k for k in game.night_actions if k.startswith("kill_")]) >= len(mafia)

    detective = next((p for p in game.alive_players() if p.role == "detective"), None)
    doctor = next((p for p in game.alive_players() if p.role == "doctor"), None)

    detective_done = "check" in game.night_actions or detective is None
    doctor_done = "heal" in game.night_actions or doctor is None

    if not (mafia_voted and detective_done and doctor_done):
        return  # Hamma tugamadi

    # Kechani hisoblaymiz
    await process_night_results(game, app)


async def process_night_results(game, app):
    kill_target_id = game.night_actions.get("kill_target")
    heal_target_id = game.night_actions.get("heal")

    killed_player = None

    if kill_target_id:
        if kill_target_id == heal_target_id:
            # Davolandi, tirik qoldi
            victim = game.players.get(kill_target_id)
            result_text = (
                f"☀️ *{game.day_number}-Kunduz*\n\n"
                f"🌙 Kecha mafiya hujum qildi, lekin shifokor uni qutqardi!\n"
                f"😮 Hech kim o'lmadi!"
            )
        else:
            victim = game.players.get(kill_target_id)
            if victim:
                victim.alive = False
                killed_player = victim
                result_text = (
                    f"☀️ *{game.day_number}-Kunduz*\n\n"
                    f"💀 Kecha *{victim.name}* o'ldirildi!\n"
                    f"Roli: {ROLES[victim.role]}\n\n"
                    f"🗳️ Endi mafiyachini topib, ovoz bering!"
                )
            else:
                result_text = f"☀️ *{game.day_number}-Kunduz*\n\nHech kim o'lmadi!"
    else:
        result_text = (
            f"☀️ *{game.day_number}-Kunduz*\n\n"
            f"Mafiya kecha harakat qilmadi!\n\n"
            f"🗳️ Ovoz berish boshlanmoqda..."
        )

    # G'alabani tekshirish
    winner = game.check_win()
    if winner:
        await end_game(game, app, winner)
        return

    game.phase = "vote"
    game.votes = {}

    alive_names = [f"• {p.name}" for p in game.alive_players()]
    vote_text = result_text + f"\n\n👥 *Tirik o'yinchilar ({len(game.alive_players())}):*\n" + "\n".join(alive_names)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🗳️ {p.name}", callback_data=f"vote_{p.user_id}")]
        for p in game.alive_players()
    ] + [[InlineKeyboardButton("⏭️ O'tkazib yuborish", callback_data="vote_skip")]])

    await app.bot.send_message(
        game.chat_id,
        vote_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


async def handle_vote(query, game, context):
    user = query.from_user
    data = query.data
    app = context.application

    if user.id not in game.players:
        await query.answer("Siz o'yinda yo'qsiz!", show_alert=True)
        return

    voter = game.players[user.id]
    if not voter.alive:
        await query.answer("O'lganlar ovoz bera olmaydi!", show_alert=True)
        return

    if user.id in game.votes:
        await query.answer("Siz allaqachon ovoz berdingiz!", show_alert=True)
        return

    if data == "vote_skip":
        game.votes[user.id] = "skip"
        await query.answer("O'tkazib yubordingiz!")
    else:
        target_id = int(data.split("_")[1])
        target = game.players.get(target_id)
        if not target or not target.alive:
            await query.answer("Bu o'yinchi mavjud emas!", show_alert=True)
            return
        game.votes[user.id] = target_id
        await query.answer(f"{target.name}ga ovoz berdingiz!")

    # Barcha tirik o'yinchilar ovoz berdimi?
    alive = game.alive_players()
    voted = len(game.votes)

    if voted >= len(alive):
        await process_votes(game, app)


async def process_votes(game, app):
    from collections import Counter

    vote_counts = Counter(v for v in game.votes.values() if v != "skip")

    if not vote_counts:
        result = "🤷 Hech kim ovoz bermadi, hech kim chiqarilmadi!"
        eliminated = None
    else:
        max_votes = max(vote_counts.values())
        top = [uid for uid, cnt in vote_counts.items() if cnt == max_votes]

        if len(top) > 1:
            result = f"🤝 Ovozlar teng bo'lindi! Hech kim chiqarilmadi!"
            eliminated = None
        else:
            eliminated_id = top[0]
            eliminated = game.players[eliminated_id]
            eliminated.alive = False
            result = (
                f"⚖️ *{eliminated.name}* shahardan chiqarib yuborildi!\n"
                f"Roli: {ROLES[eliminated.role]}"
            )

    # G'alabani tekshirish
    winner = game.check_win()
    if winner:
        await end_game(game, app, winner)
        return

    # Keyingi kechaga o'tish
    game.day_number += 1
    game.phase = "night"

    alive_names = [f"• {p.name}" for p in game.alive_players()]
    text = (
        f"🗳️ *Ovoz berish natijasi:*\n\n"
        f"{result}\n\n"
        f"👥 *Qolganlar ({len(game.alive_players())}):*\n" +
        "\n".join(alive_names) +
        f"\n\n🌙 *{game.day_number}-Kecha boshlanmoqda...*"
    )

    await app.bot.send_message(game.chat_id, text, parse_mode="Markdown")
    await asyncio.sleep(3)
    await send_night_actions(game.chat_id, game, app)


async def end_game(game, app, winner):
    game.phase = "ended"

    if winner == "citizens":
        title = "🎉 FUQAROLAR G'ALABA QILDI!"
        emoji = "🏆"
    else:
        title = "😈 MAFIYA G'ALABA QILDI!"
        emoji = "💀"

    roles_text = "\n".join(
        f"{'✅' if p.alive else '❌'} {p.name} — {ROLES[p.role]}"
        for p in game.players.values()
    )

    text = (
        f"{emoji} *{title}*\n\n"
        f"📋 *Barcha rollar:*\n{roles_text}\n\n"
        f"Yangi o'yin uchun /newgame yozing!"
    )

    await app.bot.send_message(game.chat_id, text, parse_mode="Markdown")

    if game.chat_id in games:
        del games[game.chat_id]


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in games:
        await update.message.reply_text("❌ Hozir faol o'yin yo'q!")
        return

    game = games[chat_id]
    alive = game.alive_players()

    text = (
        f"📊 *O'yin Holati*\n\n"
        f"📅 Kun: {game.day_number}\n"
        f"🔄 Bosqich: {'🌙 Kecha' if game.phase == 'night' else '☀️ Kunduz'}\n"
        f"👥 Tirik o'yinchilar ({len(alive)}):\n" +
        "\n".join(f"  • {p.name}" for p in alive)
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def end_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    if chat_id not in games:
        await update.message.reply_text("❌ Faol o'yin yo'q!")
        return

    game = games[chat_id]
    if user.id != game.host_id:
        await update.message.reply_text("❌ Faqat boshlovchi o'yinni tugatishi mumkin!")
        return

    await end_game(game, context.application, "cancelled")
    await update.message.reply_text("🛑 O'yin tugatildi!")


# ===================== ASOSIY =====================

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newgame", new_game))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("endgame", end_command))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🎮 Mafiya bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
