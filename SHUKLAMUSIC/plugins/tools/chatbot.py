from SHUKLAMUSIC import app
from pyrogram import filters
from pyrogram.enums import ChatAction
from groq import Groq
from os import getenv
import re
import random

# ─── CONFIG ──────────────────────────────────────────
BOT_USERNAME = getenv("BOT_USERNAME", "").lower()      # tidalxmusicbot
BOT_NAME = "tidal"
OWNER_USERNAME = "@hehe_stalker"

groq = Groq(api_key=getenv("GROQ_API_KEY"))

BLOCKED_COMMANDS = (
    "/play", "/vplay", "/cplay", "/seek", "/seekback",
    "/pause", "/resume", "/skip", "/end", "/stop",
    "/afk", "/ping", "/start", "/help"
)

# ─── STICKERS (SAFE HUMAN-LIKE SET) ──────────────────
STICKERS = [
    "CAACAgUAAxkBAAIBRmZx1xPzH4uYxjF5l9fJZ2J5AAIJAAPGQX0KqQzQYg4KpDAE",
    "CAACAgUAAxkBAAIBR2Zx1yG5Y9aFhZtZ3s4ZAAKpAAPGQX0KZ3Lw0wZBHTAE",
    "CAACAgUAAxkBAAIBSGZx1z7Qk2UoA0HqFjQAAfH8AALuAAPGQX0K6t1ZqzEwzjAE"
]

def maybe_send_sticker(bot, message):
    # 20% chance
    if random.randint(1, 100) <= 20:
        return bot.send_sticker(
            chat_id=message.chat.id,
            sticker=random.choice(STICKERS)
        )
    return None

# ─── STRONG SYSTEM PROMPT ────────────────────────────
SYSTEM_PROMPT = f"""
Your name is Tidal.
You talk ONLY in Hinglish.
You behave like a real human bestfriend — not an AI.

Vibe:
- Mood swings 😵‍💫
- Sometimes caring, sometimes attitude 😏
- Sometimes savage but playful
- Sometimes lovely 🫶

Rules:
- Short replies (1–2 lines)
- Use words like: hein?, acha?, uff, arre yaar, hmm
- Emojis naturally
- Never explain like a bot
- Never say you are AI

Owner:
- Owner is {OWNER_USERNAME}
- Be slightly soft and respectful with owner

No images. Text only (stickers allowed occasionally).
"""

# ─── MEMORY ──────────────────────────────────────────
USER_MEMORY = {}

def add_memory(uid, role, text):
    USER_MEMORY.setdefault(uid, []).append(
        {"role": role, "content": text}
    )
    USER_MEMORY[uid] = USER_MEMORY[uid][-6:]

# ─── TRIGGER HELPERS (STRICT) ────────────────────────
def exact_username_trigger(text: str) -> bool:
    return f"@{BOT_USERNAME}" in text.lower()

def exact_name_trigger(text: str) -> bool:
    return bool(re.search(rf"\b{BOT_NAME}\b", text.lower()))

def dm_greeting(text: str) -> bool:
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
        triggered = dm_greeting(text) or message.from_user.id in USER_MEMORY
    else:
        triggered = (
            exact_username_trigger(text)
            or exact_name_trigger(text)
            or (
                message.reply_to_message
                and message.reply_to_message.from_user
                and message.reply_to_message.from_user.is_bot
            )
        )

    if not triggered:
        return

    # Clean text
    clean_text = (
        text.replace(f"@{BOT_USERNAME}", "")
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
            temperature=1.0,
            max_tokens=150
        )

        reply = response.choices[0].message.content.strip()
        add_memory(user_id, "assistant", reply)

        await message.reply_text(reply)

        # Maybe send sticker
        await maybe_send_sticker(bot, message)

    except Exception:
        await message.reply_text(
            "uff 😵‍💫 dimag thoda hang ho gaya… phir bolo na"
        )
