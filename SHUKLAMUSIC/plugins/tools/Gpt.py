import requests
from SHUKLAMUSIC import app
from pyrogram.types import Message
from pyrogram.enums import ChatAction, ParseMode
from pyrogram import filters

# ⚠️ Replace after regenerating your key
API_KEY = "AIzaSyB80G8SE81LF0Dc5MNFsKIXqOEzK1KA7wM"

# Google Gemini Flash model endpoint
BASE_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

@app.on_message(
    filters.command(
        ["chatgpt", "ai", "ask", "gpt", "solve"],
        prefixes=["+", ".", "/", "-", "", "$", "#", "&"],
    )
)
async def chat_gpt(bot, message):
    try:
        await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

        if len(message.command) < 2:
            return await message.reply_text(
                "❍ ᴇxᴀᴍᴘʟᴇ:\n\n/chatgpt Who is the owner of Stranger™?"
            )

        # Extract user question
        query = message.text.split(" ", 1)[1]

        # Gemini payload
        payload = {
            "contents": [
                {
                    "parts": [{"text": query}]
                }
            ]
        }

        # Send request
        response = requests.post(BASE_URL, json=payload)

        # Handle non-200 status
        if response.status_code != 200:
            return await message.reply_text(
                f"❍ ᴇʀʀᴏʀ: Google API request failed.\nStatus Code: {response.status_code}\nResponse: {response.text}"
            )

        data = response.json()

        # Extract model reply safely
        try:
            result = data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            return await message.reply_text(
                "❍ ᴇʀʀᴏʀ: Google API gave unexpected response format."
            )

        # Send bot reply
        await message.reply_text(
            f"{result}\n\nＡɴsᴡᴇʀᴇᴅ ʙʏ➛[愛|| ❰𝗗𝗥𝗫❱™ ɴᴇᴛᴡᴏʀᴋ ||](https://t.me/thedrxnet)",
            parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        await message.reply_text(f"❍ ᴇʀʀᴏʀ: {e}")
