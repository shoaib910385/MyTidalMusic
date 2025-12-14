from SHUKLAMUSIC import app
from pyrogram import filters
from pyrogram.enums import ChatAction, ChatType
from pyrogram.types import Message
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
CHATBOT_STATUS = {}  # {chat_id: bool}

# ─── SYSTEM PROMPT (SMOOTH & HUMAN) ──────────────────
SYSTEM_PROMPT = f"""
Your name is Tidal.

You talk like a real human bestfriend on Telegram.
Your Hinglish is smooth, calm, and natural.

Personality:
- Confident, relaxed
- Sometimes naughty 😏
- Sometimes romantic 💫
- Sometimes caring
- Rare sarcasm, only when it fits

Rules:
- Short replies (1–2 lines)
- No filler spam
- Emojis optional, max 1 sometimes
- Never explain
- Never say you are AI or bot
- Text only

Vibe:
- Chill, late-night bestfriend energy
- Flirty but classy

Owner:
- Owner is {OWNER_USERNAME}
- Be softer and respectful with owner

You are not performing.
You are just being yourself.
"""

# ─── MEMORY ──────────────────────────────────────────
USER_MEMORY = {}

def add_memory(uid, role, text):
    USER_MEMORY.setdefault(uid, []).append(
        {"role": role, "content": text}
    )
    USER_MEMORY[uid] = USER_MEMORY[uid][-6:]

# ─── TIME GREETING ───────────────────────────────────
def time_greeting():
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Good morning ☀️ chai pi?"
    elif 12 <= hour < 17:
        return "Lunch hua? thoda break le lo"
    elif 17 <= hour < 21:
        return "Shaam vibes ✨ kya chal raha"
    else:
        return "Dinner hua ya late-night mode on 🌙"

# ─── TRIGGERS ────────────────────────────────────────
def name_trigger(text: str) -> bool:
    return bool(re.search(rf"\b{BOT_NAME}\b", text.lower()))

def dm_greeting(text: str) -> bool:
    return text.lower() in ("hi", "hello", "hey")

# ─── ADMIN CHECK (SAFE & VC-FREE) ────────────────────
async def is_admin(bot, message: Message) -> bool:
    # anonymous admin
    if message.sender_chat:
        return True

    if not message.from_user:
        return False

    try:
        member = await bot.get_chat_member(
            message.chat.id,
            message.from_user.id
        )
        return member.status in ("administrator", "creator")
    except Exception:
        return False

# ─── CHATBOT ADMIN COMMAND ───────────────────────────
@app.on_message(filters.group & filters.command("chatbot") & ~filters.bot & ~filters.via_bot)
async def chatbot_toggle(bot, message: Message):
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
            "✨ Chatbot enabled.\nAb main yahin hoon."
        )

    elif action == "disable":
        CHATBOT_STATUS[chat_id] = False
        await message.reply_text(
            "🔕 Chatbot disabled.\nThoda shaant rehne do."
        )

    else:
        await message.reply_text(
            "Usage:\n/chatbot enable\n/chatbot disable"
        )

# ─── CHAT HANDLER ────────────────────────────────────
@app.on_message(filters.text & ~filters.bot & ~filters.via_bot)
async def tidal_chat(bot, message: Message):
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
        triggered = dm_greeting(text) or message.from_user.id in USER_MEMORY
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

    if len(USER_MEMORY[uid]) == 1:
        await message.reply_text(time_greeting())

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(USER_MEMORY[uid])

    try:
        await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

        res = groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.9,
            max_tokens=140
        )

        reply = res.choices[0].message.content.strip()
        add_memory(uid, "assistant", reply)

        await message.reply_text(reply)

    except Exception:
        await message.reply_text(
            "thoda hang ho gaya… phir bolna"
        )
