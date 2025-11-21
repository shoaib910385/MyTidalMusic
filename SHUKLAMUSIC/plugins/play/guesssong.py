import random
import asyncio
from pyrogram import filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

from SHUKLAMUSIC import app
from SHUKLAMUSIC.core.call import SHUKLA
from SHUKLAMUSIC.utils.stream.stream import stream
from SHUKLAMUSIC.utils.decorators.language import LanguageStart

from pymongo import MongoClient
from rapidfuzz import fuzz

# ------------------ MONGO ------------------
MONGO_DB = "mongodb+srv://arrush:Arrush123@arrush0.w4uwjly.mongodb.net/?retryWrites=true&w=majority&appName=arrush0"
mongo = MongoClient(MONGO_DB)

db = mongo["GuessSong"]
global_users = db["GlobalUsers"]      # lifetime total points
chat_users = db["ChatUsers"]          # lifetime per-group points

# ------------------ GAME STORAGE ------------------
game_sessions = {}   # chat_id: {rounds, current, session_scores}
active_round = {}    # chat_id: {"answer": title, "guessed": False}

# ------------------ SONGS (.ogg) ------------------
GUESS_SONGS = [
    {"title": "Attention", "audio": "https://files.catbox.moe/s60zrl.ogg"},
    {"title": "saiyara", "audio": "https://files.catbox.moe/xg44ng.ogg"},
    {"title": "levitating", "audio": "https://files.catbox.moe/xb2npe.ogg"},
]

# ---------------------------------------------------------
# START GAME
# ---------------------------------------------------------
@app.on_message(filters.command("guesssong") & filters.group)
@LanguageStart
async def start_game(client, message: Message, _):

    chat_id = message.chat.id

    if chat_id in game_sessions:
        return await message.reply_text("⚠️ A game is already running here!")

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("3 Songs", callback_data="gs_rounds_3"),
                InlineKeyboardButton("5 Songs", callback_data="gs_rounds_5"),
            ]
        ]
    )

    await message.reply_text(
        "🎮 **Choose number of rounds:**",
        reply_markup=keyboard
    )

# ---------------------------------------------------------
# HANDLE ROUNDS CHOICE
# ---------------------------------------------------------
@app.on_callback_query(filters.regex("gs_rounds_"))
async def round_choice(client, query: CallbackQuery):

    chat_id = query.message.chat.id
    rounds = int(query.data.split("_")[2])

    game_sessions[chat_id] = {
        "rounds": rounds,
        "current": 0,
        "session_scores": {}   # per game score (temporary)
    }

    await query.message.edit_text(f"🎧 Guess Song Game Started!\nRounds: {rounds}")

    await start_round(chat_id)


# ---------------------------------------------------------
# START ONE ROUND
# ---------------------------------------------------------
async def start_round(chat_id):

    session = game_sessions.get(chat_id)
    if not session:
        return

    # FINISHED?
    if session["current"] >= session["rounds"]:
        return await end_game(chat_id)

    session["current"] += 1

    song = random.choice(GUESS_SONGS)
    title = song["title"].lower()

    active_round[chat_id] = {
        "answer": title,
        "guessed": False
    }

    await app.send_message(
        chat_id,
        f"🎵 **Round {session['current']} of {session['rounds']}**\n"
        f"Guess the song!\nYou have **60 seconds**.\n"
        f"Use: `/guess your answer`"
    )

    # PLAY AUDIO
    try:
        await stream(
            song["audio"],
            None,
            None,
            None,
            chat_id,
            "GuessGame",
            chat_id,
            streamtype="local",
        )
    except:
        return await app.send_message(chat_id, "❌ Error playing audio.")

    # 60 sec timeout
    await asyncio.sleep(60)

    if chat_id in active_round and not active_round[chat_id]["guessed"]:
        # Stop audio
        try:
            await SHUKLA.leave_group_call(chat_id)
        except:
            pass

        await app.send_message(chat_id, "⏱ No guesses! Moving to next round...")
        del active_round[chat_id]

    await start_round(chat_id)


# ---------------------------------------------------------
# GUESS COMMAND
# ---------------------------------------------------------
@app.on_message(filters.command("guess") & filters.group)
async def guess_handler(client, message: Message):

    chat_id = message.chat.id

    if chat_id not in active_round:
        return await message.reply_text("❌ No active round!")

    guess_text = message.text.split(" ", 1)
    if len(guess_text) < 2:
        return await message.reply_text("❗Usage: `/guess your answer`")

    guess = guess_text[1].strip().lower()
    answer = active_round[chat_id]["answer"]

    # FUZZY MATCH
    if fuzz.ratio(guess, answer) >= 70:

        if active_round[chat_id]["guessed"]:
            return

        active_round[chat_id]["guessed"] = True
        user_id = message.from_user.id

        # Update per-game score
        game_sessions[chat_id]["session_scores"][user_id] = (
            game_sessions[chat_id]["session_scores"].get(user_id, 0) + 1
        )

        # 20 points to GLOBAL ranking
        global_users.update_one(
            {"user_id": user_id},
            {"$inc": {"points": 20}},
            upsert=True,
        )

        # 20 points to CHAT ranking
        chat_users.update_one(
            {"chat_id": chat_id, "user_id": user_id},
            {"$inc": {"points": 20}},
            upsert=True
        )

        # fetch total global points
        total_points = global_users.find_one({"user_id": user_id})["points"]

        # stop audio
        try:
            await SHUKLA.leave_group_call(chat_id)
        except:
            pass

        await message.reply_text(
            f"🎉 **Congratulations!**\n"
            f"Correct song: **{answer.title()}**\n\n"
            f"🎁 You earned **+20 points**\n"
            f"🏆 Total Points: **{total_points}**"
        )

        del active_round[chat_id]

        await start_round(chat_id)

    else:
        await message.reply_text("❌ Wrong guess! Try again.")


# ---------------------------------------------------------
# END GAME
# ---------------------------------------------------------
async def end_game(chat_id):

    session = game_sessions.get(chat_id)
    if not session:
        return

    results = sorted(
        session["session_scores"].items(),
        key=lambda x: x[1],
        reverse=True
    )

    text = "🏁 **GAME OVER**\n\n**Top Players This Game:**\n\n"

    rank = 1
    for user_id, score in results:
        u = await app.get_users(user_id)
        text += f"{rank}. {u.mention} — {score} correct 🎯\n"
        rank += 1

    await app.send_message(chat_id, text)

    del game_sessions[chat_id]
    if chat_id in active_round:
        del active_round[chat_id]


# ---------------------------------------------------------
# STOP GAME
# ---------------------------------------------------------
@app.on_message(filters.command("stopgame") & filters.group)
async def stopgame(client, message: Message):

    chat_id = message.chat.id

    if chat_id not in game_sessions:
        return await message.reply_text("❌ No active game to stop.")

    try:
        await SHUKLA.leave_group_call(chat_id)
    except:
        pass

    del game_sessions[chat_id]
    if chat_id in active_round:
        del active_round[chat_id]

    await message.reply_text("🛑 Guess Song Game has been stopped.")


# ---------------------------------------------------------
# RANKING SYSTEM
# ---------------------------------------------------------
@app.on_message(filters.command("guessranking") & filters.group)
async def ranking_menu(client, message: Message):

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🌍 Global Ranking", callback_data="gs_rank_global"),
                InlineKeyboardButton("👥 Chat Ranking", callback_data=f"gs_rank_chat_{message.chat.id}")
            ]
        ]
    )

    await message.reply_text(
        "📊 Choose ranking type:",
        reply_markup=keyboard
    )


@app.on_callback_query(filters.regex("gs_rank_"))
async def ranking_show(client, query: CallbackQuery):

    data = query.data

    # -------- GLOBAL RANKING --------
    if "global" in data:

        top_users = list(global_users.find().sort("points", -1).limit(10))

        text = "🌍 **Global Ranking — Top 10 Players**\n\n"
        rank = 1
        for user in top_users:
            try:
                u = await app.get_users(user["user_id"])
                text += f"{rank}. {u.mention} — {user['points']} pts 🏆\n"
                rank += 1
            except:
                pass

        return await query.message.edit_text(text)


    # -------- CHAT RANKING --------
    if "chat" in data:

        chat_id = int(data.split("_")[3])

        top_chat = list(
            chat_users.find({"chat_id": chat_id}).sort("points", -1).limit(10)
        )

        if not top_chat:
            return await query.message.edit_text("❌ No ranking data for this chat!")

        text = "👥 **Lifetime Chat Ranking**\n\n"
        rank = 1
        for doc in top_chat:
            u = await app.get_users(doc["user_id"])
            text += f"{rank}. {u.mention} — {doc['points']} pts 🎯\n"
            rank += 1

        return await query.message.edit_text(text)
