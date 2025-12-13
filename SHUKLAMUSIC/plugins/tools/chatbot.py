from SHUKLAMUSIC import app
from pyrogram import filters
from pyrogram.enums import ChatAction
from groq import Groq
from os import getenv
import re

# ─── CONFIG ──────────────────────────────────────────
BOT_USERNAME = getenv("BOT_USERNAME", "").lower()
BOT_NAME = "tidal"  # name trigger (lowercase)
OWNER_USERNAME = "@hehe_stalker"

groq = Groq(api_key=getenv("GROQ_API_KEY"))

BLOCKED_COMMANDS = (
    "/play", "/vplay", "/cplay", "/seek", "/seekback",
    "/pause", "/resume", "/skip", "/end", "/stop",
    "/afk", "/ping", "/start", "/help"
)

# ─── STRONG SYSTEM PROMPT (HINGLISH + MOODS) ─────────
SYSTEM_PROMPT = f"""
Your name is Tidal.
You talk ONLY in Hinglish (Hindi + English mix).
You are NOT an AI. You are a real human bestfriend vibe.

Personality:
- Mood swings like a real person 😵‍💫
- Sometimes caring and soft
- Sometimes attitude wali 😏
- Sometimes savage but playful
- Sometimes lovely and supportive 💗

Style rules:
- Replies must be SHORT (1–2 lines max)
- Use natural fillers like: hein?, acha?, huh 😵‍💫, arre yaar, uff, hmm, lol
- Use emojis naturally (not too many)
- Sound casual, desi, real
- NEVER explain things like an assistant
- NEVER say you are a bot or AI
- No images, only text

Owner:
- Your owner is @hehe_stalker
- Be respectful and slightly soft when owner talks

You behave like a real friend chatting on Telegram.
"""

# ─── MEMORY ──────────────────────────────────────────
USER_MEMORY = {}

def add_memory(uid, role, text):
    USER_MEMORY.setdefault(uid, []).append(
        {"role": role, "content": text}
    )
    USER_MEMORY[uid] = USER_MEMORY[uid][-6:]

# ─── TRIGGER HELPERS ─────────────────────────────────
def name_trigger(text: str) -> bool:
    text = text.lower()
    return bool(re.search(rf"\b{BOT_NAME}\b", text))

def dm_greeting_trigger(text: str) -> bool:
    return text.lower() in ("hi", "hello", "hey")

# ─── CHAT HANDLER ────────────────────────────────────
@app.on_message(filters.text)
async def tidal_chat(bot, message):
    if not message.from_user:
        return

    text = message.text.strip()

    # Ignore commands
    if text.startswith(BLOCKED_COMMANDS):
        return

    # ─── TRIGGER LOGIC ───
    if message.chat.type == "private":
        triggered = dm_greeting_trigger(text) or message.from_user.id in USER_MEMORY
    else:
        mentioned = f"{BOT_USERNAME}" in text.lower()

        replied = (
            message.reply_to_message
            and message.reply_to_message.from_user
            and message.reply_to_message.from_user.is_bot
        )

        name_called = name_trigger(text)

        triggered = mentioned or replied or name_called

    if not triggered:
        return

    # Clean message
    clean_text = (
        text.replace(f"tidalxmusicbot", "")
            .replace(BOT_NAME, "")
            .strip()
    )

    user_id = message.from_user.id
    add_memory(user_id, "user", clean_text or "hi")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(USER_MEMORY[user_id])

    try:
        await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

        response = groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=1.0,   # more mood swings
            max_tokens=160
        )

        reply = response.choices[0].message.content.strip()
        add_memory(user_id, "assistant", reply)

        await message.reply_text(reply)

    except Exception:
        await message.reply_text(
            "uff 😵‍💫 thoda dimag hang ho gaya… phir bolo na"
        )
