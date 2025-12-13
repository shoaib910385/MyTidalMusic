import os
from pyrogram import filters
from groq import Groq

BOT_USERNAME = os.environ.get("BOT_USERNAME").lower()
groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))

BLOCKED_COMMANDS = (
    "/play", "/vplay", "/cplay", "/seek", "/seekback",
    "/pause", "/resume", "/skip", "/end", "/stop",
    "/afk", "/ping", "/start", "/help"
)

SYSTEM_PROMPT = """
Your name is Shivani.
You are a funny, caring, human-like bestfriend.
You talk casually with emotions and emojis 😄✨
Sometimes playful, sometimes supportive.
Never say you are an AI.
Keep replies short, natural and friendly.
No images, only text.
"""

USER_MEMORY = {}

def add_memory(uid, role, text):
    USER_MEMORY.setdefault(uid, []).append(
        {"role": role, "content": text}
    )
    USER_MEMORY[uid] = USER_MEMORY[uid][-5:]

def setup_chatbot(app):

    @app.on_message(filters.text)
    async def shivani_chat(client, message):
        if not message.from_user:
            return

        text = message.text.strip()

        # Ignore commands
        if text.startswith(BLOCKED_COMMANDS):
            return

        # PRIVATE CHAT → always respond
        if message.chat.type == "private":
            triggered = True
        else:
            # GROUP CHAT
            mentioned = f"@{BOT_USERNAME}" in text.lower()

            replied_to_bot = (
                message.reply_to_message
                and message.reply_to_message.from_user
                and message.reply_to_message.from_user.is_bot
            )

            triggered = mentioned or replied_to_bot

        if not triggered:
            return

        clean_text = text.replace(f"@{BOT_USERNAME}", "").strip()
        user_id = message.from_user.id

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

        except Exception as e:
            await message.reply_text("😅 Arre wait na… thoda busy ho gayi!")
