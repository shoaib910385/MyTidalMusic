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
You talk ONLY in Hinglish.
You are NOT an AI — you behave like a real human friend.

Vibe:
- Mood swings 😵‍💫
- Caring, savage, playful, soft — depending on mood
- Modern, premium, chill energy

Style rules:
- Short replies (1–2 lines)
- Use words like: hein?, acha?, uff, hmm, lol
- Emojis spaced & natural ✨
- Never explain like assistant
- Never say AI/bot
- Text only

Owner:
- Owner is {OWNER_USERNAME}
- Be respectful & slightly soft with owner

Act like Telegram bestfriend, not support agent.
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

# ─── ADMIN COMMANDS ──────────────────────────────────
@app.on_message(filters.command("chatbot") & filters.group)
async def chatbot_toggle(bot, message):
    if not message.from_user:
        return

    member = await bot.get_chat_member(
        message.chat.id, message.from_user.id
    )

    if member.status not in ("administrator", "creator"):
        return await message.reply_text(
            "🚫 Sirf admins hi chatbot control kar sakte hain."
        )

    if len(message.command) < 2:
        return await message.reply_text(
            "Usage:\n/chatbot enable\n/chatbot disable"
        )

    action = message.command[1].lower()

    if action == "enable":
        CHATBOT_STATUS[message.chat.id] = True
        await message.reply_text("✨ Chatbot enabled. Ab main zinda hoon 😄")

    elif action == "disable":
        CHATBOT_STATUS[message.chat.id] = False
        await message.reply_text("🔕 Chatbot disabled. Thoda shaant mode 😌")

# ─── CHAT HANDLER ────────────────────────────────────
@app.on_message(filters.text)
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

    user_id = message.from_user.id
    add_memory(user_id, "user", clean_text or "hi")

    # ─── GREETING INJECTION ───
    if len(USER_MEMORY[user_id]) == 1:
        await message.reply_text(time_greeting())

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(USER_MEMORY[user_id])

    try:
        await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

        res = groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=1.0,
            max_tokens=160
        )

        reply = res.choices[0].message.content.strip()
        add_memory(user_id, "assistant", reply)

        await message.reply_text(reply)

    except Exception:
        await message.reply_text(
            "uff 😵‍💫 thoda hang ho gaya… phir bolo na"
        )
