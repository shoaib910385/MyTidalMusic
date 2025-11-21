import random
import asyncio
from urllib.parse import urlparse, parse_qs

from pyrogram import filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

from config import BANNED_USERS
from SHUKLAMUSIC import app, YouTube
from SHUKLAMUSIC.core.call import SHUKLA
from SHUKLAMUSIC.utils.stream.stream import stream
from SHUKLAMUSIC.utils.decorators.language import LanguageStart

from pymongo import MongoClient
from rapidfuzz import fuzz

MONGO_DB_URL=["mongodb+srv://arrush:Arrush123@arrush0.w4uwjly.mongodb.net/?retryWrites=true&w=majority&appName=arrush0"]
# MongoDB Setup
mongo = MongoClient(MONGO_DB_URL)
db = mongo["GuessSong"]
users_col = db["Users"]

# Store Games
game_sessions = {}         # chat_id: {rounds, current_round, scores, players}
active_round = {}          # chat_id: {"answer": "", "winner": None, "guessed": False}

# Songs List
GUESS_SONGS = [
    {"title": "Offo", "url": "https://www.youtube.com/watch?v=ghzMGkZC4nY"},
    {"title": "Attention", "url": "https://www.youtube.com/watch?v=nfs8NYg7yQM"},
    {"title": "Zaroorat", "url": "https://www.youtube.com/watch?v=GzU8KqOY8YA"},
]


# Extract Video ID
def extract_video_id(url):
    query = urlparse(url)
    if query.hostname == "youtu.be":
        return query.path[1:]
    if query.hostname in ("www.youtube.com", "youtube.com"):
        if query.path == "/watch":
            return parse_qs(query.query).get("v", [None])[0]
        if query.path.startswith("/embed/") or query.path.startswith("/v/"):
            return query.path.split("/")[2]
    return None


# ----------------------- ADMIN CHECK -----------------------
async def is_admin(client, message: Message):
    try:
        member = await client.get_chat_member(message.chat.id, message.from_user.id)
        return member.status in ("administrator", "creator")
    except:
        return False

# ----------------------- START COMMAND -----------------------
@app.on_message(filters.command(["guesssong"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def guess_song_cmd(client, message: Message, _):

    chat_id = message.chat.id

    if chat_id in game_sessions:
        return await message.reply_text("⚠️ A game is already running here!")

    # Ask number of rounds
    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("3 Songs", callback_data=f"gs_rounds_3"),
                InlineKeyboardButton("5 Songs", callback_data=f"gs_rounds_5"),
            ]
        ]
    )

    await message.reply_text("🎮 Select number of rounds:", reply_markup=buttons)


# -------------------------- CALLBACK FOR ROUNDS --------------------------
@app.on_callback_query(filters.regex("gs_rounds_"))
async def gs_rounds_callback(client, query: CallbackQuery):
    chat_id = query.message.chat.id
    rounds = int(query.data.split("_")[2])

    game_sessions[chat_id] = {
        "rounds": rounds,
        "current": 0,
        "scores": {},  # user_id: correct_count
    }

    await query.message.edit_text(f"🎧 Guess Song Game Started!\nRounds: {rounds}")

    await start_next_round(chat_id, query.message)


# -------------------------- SINGLE ROUND FUNCTION --------------------------
async def start_next_round(chat_id, msg_obj):
    session = game_sessions.get(chat_id)
    if not session:
        return

    if session["current"] >= session["rounds"]:
        return await end_game(chat_id)

    session["current"] += 1

    song = random.choice(GUESS_SONGS)
    answer = song["title"].strip().lower()

    video_id = extract_video_id(song["url"])
    if not video_id:
        return await app.send_message(chat_id, "❌ Invalid YouTube Link.")

    try:
        details, _id = await YouTube.track(video_id)
    except:
        return await app.send_message(chat_id, "❌ Failed to get song details.")

    # Save round info
    active_round[chat_id] = {
        "answer": answer,
        "guessed": False,
        "winner": None,
    }

    await app.send_message(
        chat_id,
        f"🎵 **Round {session['current']} of {session['rounds']}**\nGuess the song! You have **60 seconds**.\nUse `/guess your answer`"
    )

    try:
        await stream(
            _id,
            None,
            None,
            details,
            chat_id,
            "GuessGame",
            chat_id,
            streamtype="youtube",
        )
    except:
        return await app.send_message(chat_id, "❌ Failed to play song in VC.")

    await asyncio.sleep(10)
    try:
        await SHUKLA.leave_group_call(chat_id)
    except:
        pass

    # Wait 60 seconds for guesses
    await asyncio.sleep(50)

    session = game_sessions.get(chat_id)
    round_data = active_round.get(chat_id)

    if session and round_data and not round_data["guessed"]:
        await app.send_message(chat_id, "⏱ No correct guess! Moving to next round...")
        del active_round[chat_id]

    await start_next_round(chat_id, msg_obj)


# -------------------------- GUESS COMMAND --------------------------
@app.on_message(filters.command(["guess"]) & filters.group & ~BANNED_USERS)
async def guess_handler(client, message: Message):

    chat_id = message.chat.id
    if chat_id not in active_round:
        return await message.reply_text("❌ No active round right now.")

    round_data = active_round[chat_id]

    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        return await message.reply_text("❗Usage: `/guess your answer`", quote=True)

    guess = parts[1].strip().lower()
    answer = round_data["answer"]

    # Fuzzy match
    score = fuzz.ratio(guess, answer)

    if score >= 70:  # match success
        if round_data["guessed"]:
            return

        round_data["guessed"] = True
        round_data["winner"] = message.from_user.id

        # Update game session scores
        game_sessions[chat_id]["scores"][message.from_user.id] = \
            game_sessions[chat_id]["scores"].get(message.from_user.id, 0) + 1

        # Mongo points (20 per correct)
        users_col.update_one(
            {"user_id": message.from_user.id},
            {"$inc": {"points": 20}},
            upsert=True,
        )

        mention = message.from_user.mention
        await message.reply_text(f"🎉 {mention} guessed it right!\nCorrect answer: **{answer.title()}**")

        del active_round[chat_id]
        return

    else:
        return await message.reply_text("❌ Wrong guess, try harder!")


# -------------------------- END GAME --------------------------
async def end_game(chat_id):
    session = game_sessions.get(chat_id)
    if not session:
        return

    result = sorted(session["scores"].items(), key=lambda x: x[1], reverse=True)

    text = "🏁 **Game Ended!**\n\n**Top Players:**\n"
    rank = 1
    for user_id, score in result:
        user = await app.get_users(user_id)
        text += f"**{rank}. {user.mention} — {score} correct**\n"
        rank += 1

    await app.send_message(chat_id, text)

    del game_sessions[chat_id]
    if chat_id in active_round:
        del active_round[chat_id]


# -------------------------- GLOBAL RANKING --------------------------
@app.on_message(filters.command(["guessranking"]) & ~BANNED_USERS)
async def ranking_cmd(client, message: Message):

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🌍 Global", callback_data="gs_rank_global"),
                InlineKeyboardButton("👥 This Chat", callback_data=f"gs_rank_chat_{message.chat.id}"),
            ]
        ]
    )

    await message.reply_text("📊 Choose Ranking Type:", reply_markup=buttons)


@app.on_callback_query(filters.regex("gs_rank_"))
async def ranking_callback(client, query: CallbackQuery):

    data = query.data

    # Global Ranking
    if "global" in data:
        all_users = list(users_col.find().sort("points", -1).limit(10))
        text = "🌍 **Global Top 10 Guessers**\n\n"
        rank = 1
        for u in all_users:
            try:
                user = await app.get_users(u["user_id"])
                text += f"{rank}. {user.mention} — {u['points']} pts\n"
            except:
                pass
            rank += 1

        return await query.message.edit_text(text)

    # Chat Ranking
    if "chat" in data:
        chat_id = int(data.split("_")[3])
        session = game_sessions.get(chat_id)

        if not session or not session["scores"]:
            return await query.message.edit_text("❌ No players in this chat ranking!")

        sorted_players = sorted(session["scores"].items(), key=lambda x: x[1], reverse=True)

        text = "👥 **Chat Ranking**\n\n"
        rank = 1
        for user_id, score in sorted_players:
            user = await app.get_users(user_id)
            text += f"{rank}. {user.mention} — {score} correct\n"
            rank += 1

        await query.message.edit_text(text)
