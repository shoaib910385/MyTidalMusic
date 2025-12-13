import os
from pyrogram import Client, filters
from groq import Groq

# ───── ENV ─────
BOT_USERNAME = os.environ.get("BOT_USERNAME").lower()

# ───── GROQ ─────
groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ───── BLOCKED COMMANDS ─────
BLOCKED_COMMANDS = (
    "/play", "/vplay", "/cplay", "/seek", "/seekback",
    "/pause", "/resume", "/skip", "/end", "/stop",
    "/afk", "/ping", "/start", "/help"
)

# ───── SYSTEM PROMPT (PERSONALITY) ─────
SYSTEM_PROMPT = """
Your name is Shivani.
You are a funny, caring, friendly bestfriend.
You talk like a real human, not an AI.
You use emojis naturally 😄✨
Sometimes playful, sometimes supportive.
Replies should be short, emotional and natural.
No images, only text.
"""

# ───── MEMORY ─────
USER_MEMORY = {}

def add_memory(uid, role, content):
    USER_MEMORY.setdefault(uid, []).append(
        {"role": role, "content": content}
    )
    USER_MEMORY[uid] = USER_MEMORY[uid][-5:]

# ───── HANDLER ─────
@Client.on_message(filters.text & ~filters.command)
async def shivani_chat(client, message):
    text = message.text.strip()

    # Ignore blocked commands
    if text.startswith(BLOCKED_COMMANDS):
        return

    # PRIVATE CHAT → always reply
    if message.chat.type == "private":
        triggered = True
    else:
        # GROUP → mention OR reply to bot
        mentioned = message.entities and any(
            e.type == "mention" and BOT_USERNAME in text.lower()
            for e in message.entities
        )

        replied = (
            message.reply_to_message
            and message.reply_to_message.from_user
            and message.reply_to_message.from_user.is_bot
        )

        triggered = mentioned or replied

    if not triggered:
        return

    user_id = message.from_user.id

    # Clean mention
    clean_text = text.replace(f"@{BOT_USERNAME}", "").strip()

    add_memory(user_id, "user", clean_text)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(USER_MEMORY[user_id])

    try:
        response = groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.9,
            max_tokens=180
        )

        reply = response.choices[0].message.content.strip()
        add_memory(user_id, "assistant", reply)

        await message.reply_text(reply)

    except Exception:
        await message.reply_text("😅 Arre ruk… thoda load aa gaya!")
