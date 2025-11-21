import requests
from SHUKLAMUSIC import app
from pyrogram.types import Message
from pyrogram.enums import ChatAction
from pyrogram import filters
import base64

API_KEY = "AIzaSyB80G8SE81LF0Dc5MNFsKIXqOEzK1KA7wM"

# TEXT MODEL
TEXT_MODEL_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-001:generateContent?key={API_KEY}"

# IMAGE MODEL
IMAGE_MODEL_URL = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-1:generateImage?key={API_KEY}"

# Keywords that trigger image generation
IMAGE_KEYWORDS = [
    "image", "photo", "picture", "draw", "generate an image",
    "create an image", "make an image", "ai image", "create photo",
    "generate photo", "draw me", "make a picture"
]

@app.on_message(
    filters.command(
        ["ai", "ask", "chatgpt", "gpt", "solve"],
        prefixes=["+", ".", "/", "-", "", "$", "#", "&"],
    )
)
async def ai_handler(bot, message):
    try:
        await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

        if len(message.command) < 2:
            return await message.reply_text("❍ Example:\n\n/ai create an image of a cute robot")

        query = message.text.split(" ", 1)[1].lower()

        # Detect if the user wants to generate an image
        is_image_prompt = any(kw in query for kw in IMAGE_KEYWORDS)

        # -------------------------
        # 1) IMAGE GENERATION
        # -------------------------
        if is_image_prompt:
            await message.reply_text("🖼 Generating image... Please wait 4–6 seconds.")

            payload = {
                "prompt": query,
                "numImages": 1,
                "width": 1024,
                "height": 1024
            }

            response = requests.post(IMAGE_MODEL_URL, json=payload)

            if response.status_code != 200:
                return await message.reply_text(
                    f"❍ ERROR generating image\nStatus Code: {response.status_code}\nResponse: {response.text}"
                )

            data = response.json()

            try:
                img_base64 = data["images"][0]["imageBytes"]
                img_bytes = base64.b64decode(img_base64)
            except:
                return await message.reply_text("❍ ERROR: Invalid image response from Google API.")

            # Upload the generated image
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=img_bytes,
                caption="✨ **AI Generated Image**"
            )
            return

        # -------------------------
        # 2) TEXT GENERATION
        # -------------------------
        payload = {
            "contents": [
                {"parts": [{"text": query}]}
            ]
        }

        response = requests.post(TEXT_MODEL_URL, json=payload)

        if response.status_code != 200:
            return await message.reply_text(
                f"❍ ERROR: Google API failed.\nStatus Code: {response.status_code}\nResponse: {response.text}"
            )

        data = response.json()

        try:
            result = data["candidates"][0]["content"]["parts"][0]["text"]
        except:
            return await message.reply_text("❍ ERROR: Invalid text response format.")

        await message.reply_text(result)

    except Exception as e:
        await message.reply_text(f"❍ ERROR: {e}")
