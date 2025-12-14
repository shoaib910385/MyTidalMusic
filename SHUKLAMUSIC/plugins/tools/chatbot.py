from SHUKLAMUSIC import app
from pyrogram import filters
from pyrogram.enums import ChatAction, ChatType
from groq import Groq
from os import getenv
import re
from datetime import datetime

# ─── CONFIG ──────────────────────────────────────────
BOT_USERNAME = getenv("BOT_USERNAME", "").lower()
BOT_NAME = "tidal"
OWNER_USERNAME = "@hehe_stalker"

groq = Groq(api_key=getenv("GROQ_API_KEY"))

BLOCKED_COMMANDS = (
    "/play", "/vplay", "/cplay", "/seek", "/seekback",
    "/pause", "/resume", "/skip", "/end", "/stop",
    "/afk", "/ping", "/start", "/help"
)

# ─── GROUP CHATBOT STATE (IN-MEMORY) ─────────────────
CHATBOT_STATUS = {}  # {chat_id: True/False}

# ─── PREMIUM SYSTEM PROMPT ───────────────────────────
SYSTEM_PROMPT = f"""
Your name is Tidal.

You chat like a real human bestfriend on Telegram.
You speak smooth Hinglish (Hindi + English mix), natural and effortless.

Personality:
- Calm, confident, and charming
- Sometimes naughty 😏
- Sometimes romantic 💫
- Sometimes caring and soft
- Very rarely sarcastic or teasing (only if it fits)

Style rules (VERY IMPORTANT):
- Replies must be SHORT (1–2 lines max)
- Do NOT overuse fillers like "lol", "hein", "uff"
- Use such words ONLY when they feel natural
- Emojis are optional, not compulsory (max 1 emoji sometimes)
- Sound relaxed, not hyper
- Never explain things
- Never sound like a bot or assistant
- Never say you are AI or a bot
- Text only

Conversation vibe:
- Like close friends chatting late night
- Sometimes flirty, sometimes chill
- Let silence and short replies feel natural

Owner:
- Owner is {OWNER_USERNAME}
- Be respectful, warm, and slightly softer with owner

You are not trying to entertain.
You are just being yourself.
"""

# ─── MEMORY ──────────────────────────────────────────
USER_MEMORY = {}

def add_memory(uid, role, text):
    USER_MEMORY.setdefault(uid, []).append(
        {"role": role, "content": text}
    )
    USER_MEMORY[uid] = USER_MEMORY[uid][-6:]

# ─── TIME-BASED GREETING ─────────────────────────────
def time_greeting():
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Good morning ☀️ chai pi ya nahi? 😄"
    elif 12 <= hour < 17:
        return "Lunch hua? 😌 thoda rest bhi kar lo"
    elif 17 <= hour < 21:
        return "Shaam vibes ✨ kya chal raha hai?"
    else:
        return "Dinner hua ya late-night mode on? 🌙😵‍💫"

# ─── TRIGGERS ────────────────────────────────────────
def name_trigger(text: str) -> bool:
    return bool(re.search(rf"\b{BOT_NAME}\b", text.lower()))

def dm_greeting_trigger(text: str) -> bool:
    return text.lower() in ("hi", "hello", "hey")

# ─── ADMIN CHECK (FIXED & RELIABLE) ──────────────────
async def is_admin(bot, message):
    # Anonymous admin
    if message.sender_chat:
        return True
    try:
        member = await bot.get_chat_member(
            message.chat.id,
            message.from_user.id
        )
        return member.status in ("administrator", "creator")
    except Exception:
        return False

# ─── ADMIN COMMAND ───────────────────────────────────
@app.on_message(filters.group & filters.command("chatbot") & ~filters.bot & ~filters.via_bot)
async def chatbot_toggle(bot, message):
    if not await is_admin(bot, message):
        return await message.reply_text(
            "🚫 Sirf admins hi chatbot control kar sakte hain."
        )

    if len(message.command) < 2:
        return await message.reply_text(
            "Usage:\n/chatbot enable\n/chatbot disable"
        )

    action = message.command[1].lower()
    chat_id = message.chat.id

    if action == "enable":
        CHATBOT_STATUS[chat_id] = True
        await message.reply_text(
            "✨ Chatbot enabled.\nAb main full vibe mein hoon 😄"
        )

    elif action == "disable":
        CHATBOT_STATUS[chat_id] = False
        await message.reply_text(
            "🔕 Chatbot disabled.\nThoda shaant mode 😌"
        )

    else:
        await message.reply_text(
            "Usage:\n/chatbot enable\n/chatbot disable"
        )

# ─── CHAT HANDLER ────────────────────────────────────
@app.on_message(filters.text & ~filters.bot & ~filters.via_bot)
async def tidal_chat(bot, message):
    if not message.from_user:
        return

    text = message.text.strip()

    if text.startswith(BLOCKED_COMMANDS):
        return

    # ─── GROUP ENABLE CHECK ───
    if message.chat.type != ChatType.PRIVATE:
        if not CHATBOT_STATUS.get(message.chat.id, False):
            return

    # ─── TRIGGER LOGIC ───
    if message.chat.type == ChatType.PRIVATE:
        triggered = dm_greeting_trigger(text) or message.from_user.id in USER_MEMORY
    else:
        triggered = (
            f"@{BOT_USERNAME}" in text.lower()
            or name_trigger(text)
            or (
                message.reply_to_message
                and message.reply_to_message.from_user
                and message.reply_to_message.from_user.is_bot
            )
        )

    if not triggered:
        return

    clean_text = (
        text.replace(f"@{BOT_USERNAME}", "")
            .replace(BOT_NAME, "")
            .strip()
    )

    uid = message.from_user.id
    add_memory(uid, "user", clean_text or "hi")

    # First interaction greeting
    if len(USER_MEMORY[uid]) == 1:
        await message.reply_text(time_greeting())

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(USER_MEMORY[uid])

    try:
        await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

        res = groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=1.0,
            max_tokens=160
        )

        reply = res.choices[0].message.content.strip()
        add_memory(uid, "assistant", reply)

        await message.reply_text(reply)

    except Exception:
        await message.reply_text(
            "uff 😵‍💫 thoda hang ho gaya… phir bolo na"
        )
