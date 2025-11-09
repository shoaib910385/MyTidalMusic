import asyncio, os, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from SHUKLAMUSIC import app
from pyrogram import filters, enums
from pyrogram.types import *
from typing import Union, Optional


# -----------------------------------------
#  CONFIG
# -----------------------------------------

bg_path = "SHUKLAMUSIC/assets/userinfo.png"
font_path = "SHUKLAMUSIC/assets/hiroko.ttf"

random_photo = [
    "https://telegra.ph/file/1949480f01355b4e87d26.jpg",
    "https://telegra.ph/file/3ef2cc0ad2bc548bafb30.jpg",
    "https://telegra.ph/file/a7d663cd2de689b811729.jpg",
    "https://telegra.ph/file/6f19dc23847f5b005e922.jpg",
    "https://telegra.ph/file/2973150dd62fd27a3a6ba.jpg",
]

get_font = lambda size: ImageFont.truetype(font_path, size)


# -----------------------------------------
#  USER LAST SEEN
# -----------------------------------------

async def userstatus(user_id: int):
    try:
        user = await app.get_users(user_id)
        x = user.status

        if x == enums.UserStatus.RECENTLY:
            return "Recently"
        elif x == enums.UserStatus.LAST_WEEK:
            return "Last week"
        elif x == enums.UserStatus.LONG_AGO:
            return "Long time ago"
        elif x == enums.UserStatus.OFFLINE:
            return "Offline"
        elif x == enums.UserStatus.ONLINE:
            return "Online"
    except:
        return "Unknown"


# -----------------------------------------
#  GENERATE IMAGE WITH TEXT ONLY
# -----------------------------------------

async def generate_userinfo_image(
    user_id, first_name, last_name, username, mention, status, dc_id, bio
):
    bg = Image.open(bg_path).convert("RGBA")
    draw = ImageDraw.Draw(bg)

    # Text positions (you can adjust these)
    draw.text((120, 160), str(user_id), fill="white", font=get_font(48))
    draw.text((120, 260), first_name, fill="white", font=get_font(48))
    draw.text((120, 360), last_name, fill="white", font=get_font(48))
    draw.text((120, 460), username, fill="white", font=get_font(48))
    draw.text((120, 560), mention, fill="white", font=get_font(48))
    draw.text((120, 660), status, fill="white", font=get_font(48))
    draw.text((120, 760), str(dc_id), fill="white", font=get_font(48))
    draw.text((120, 860), bio, fill="white", font=get_font(48))

    path = f"./userinfo_{user_id}.png"
    bg.save(path)
    return path


# -----------------------------------------
#  COMMAND HANDLER
# -----------------------------------------

@app.on_message(filters.command(["userinfo", "info"], prefixes=["/", ".", "!", ",", "#"]))
async def userinfo_cmd(_, message):
    chat_id = message.chat.id

    # Case 1: /userinfo <id or username>
    if not message.reply_to_message and len(message.command) >= 2:
        try:
            user_query = message.text.split(None, 1)[1]
            target = await app.get_users(user_query)

        except Exception as e:
            return await message.reply_text(str(e))

    # Case 2: /userinfo without reply
    elif not message.reply_to_message:
        target = message.from_user

    # Case 3: /userinfo replying to someone
    else:
        target = message.reply_to_message.from_user

    # Extract data
    user = await app.get_users(target.id)
    chat = await app.get_chat(target.id)

    id = user.id
    first_name = chat.first_name or "No first name"
    last_name = chat.last_name or "No last name"
    username = chat.username or "No username"
    mention = user.mention
    status = await userstatus(user.id)
    dc_id = user.dc_id
    bio = chat.bio or "No bio set"

    # Generate PNG
    img = await generate_userinfo_image(
        id, first_name, last_name, username, mention, status, dc_id, bio
    )

    await message.reply_photo(
        photo=img,
        caption="✅ **USER INFORMATION GENERATED**"
    )
