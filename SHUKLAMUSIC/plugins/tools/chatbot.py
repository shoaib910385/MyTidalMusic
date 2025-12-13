from SHUKLAMUSIC import app
from pyrogram import filters
from pyrogram.enums import ChatAction
from groq import Groq
from os import getenv
import re

# ─── CONFIG ──────────────────────────────────────────
BOT_USERNAME = getenv("BOT_USERNAME", "").lower()
BOT_NAME = "Tidal"  # name trigger (lowercase)

groq = Groq(api_key=getenv("GROQ_API_KEY"))

BLOCKED_COMMANDS = (
    "/play", "/vplay", "/cplay", "/seek", "/seekback",
    "/pause", "/resume", "/skip", "/end", "/stop",
    "/afk", "/ping", "/start", "/help"
)

# ─── PERSONALITY (HINGLISH) ──────────────────────────
SYSTEM_PROMPT = """
Your name is Tidal.
You talk in Hinglish (Hindi + English mix).
You are a caring, funny, human-like bestfriend.
Use emojis naturally 😄✨
Sometimes tease, sometimes support.
Talk casually like real Indian friends.
Never say you are an AI or bot.
Replies should feel real, short, and friendly.
No images, text only.
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
    """
    Triggers if message starts with or contains bot name
    Examples:
    'sivix hi'
    'hey sivix'
    """
    text = text.lower()
    return bool(re.search(rf"\b{BOT_NAME}\b", text))

# ─── CHAT HANDLER ────────────────────────────────────
@app.on_message(filters.text)
async def sivix_chat(bot, message):
    if not message.from_user:
        return

    text = message.text.strip()

    # Ignore commands
    if text.startswith(BLOCKED_COMMANDS):
        return

    # ─── TRIGGER LOGIC ───
    if message.chat.type == "private":
        triggered = True

    else:
        mentioned = f"@{BOT_USERNAME}" in text.lower()

        replied = (
            message.reply_to_message
            and message.reply_to_message.from_user
            and message.reply_to_message.from_user.is_bot
        )

        name_called = name_trigger(text)

        triggered = mentioned or replied or name_called

    if not triggered:
        return

    # Clean message text
    clean_text = (
        text.replace(f"@{BOT_USERNAME}", "")
            .replace(BOT_NAME, "")
            .strip()
    )

    user_id = message.from_user.id

    add_memory(user_id, "user", clean_text or "Hi")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(USER_MEMORY[user_id])

    try:
        await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

        response = groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.9,
            max_tokens=220
        )

        reply = response.choices[0].message.content.strip()
        add_memory(user_id, "assistant", reply)

        await message.reply_text(reply)

    except Exception:
        await message.reply_text(
            "😅 Arre wait yaar… thoda busy ho gayi thi, phir bolo na!"
      )
