import os
import json
from random import randint
from typing import Union

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, Message

import config
from SHUKLAMUSIC import Carbon, YouTube, app
from SHUKLAMUSIC.core.call import SHUKLA
from SHUKLAMUSIC.misc import db
from SHUKLAMUSIC.utils.database import add_active_video_chat, is_active_chat
from SHUKLAMUSIC.utils.exceptions import AssistantErr
from SHUKLAMUSIC.utils.inline import aq_markup, close_markup, stream_markup
from SHUKLAMUSIC.utils.pastebin import SHUKLABin
from SHUKLAMUSIC.utils.stream.queue import put_queue, put_queue_index
from SHUKLAMUSIC.utils.thumbnails import get_thumb

# --- Custom Caption Logic Start ---
CAPTION_DB_FILE = "stream_caption_config.json"
ADMIN_ID = 7659846392

def get_custom_caption_text():
    if os.path.exists(CAPTION_DB_FILE):
        try:
            with open(CAPTION_DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("text")
        except:
            return None
    return None

def save_custom_caption_text(text):
    with open(CAPTION_DB_FILE, "w", encoding="utf-8") as f:
        json.dump({"text": text}, f, ensure_ascii=False, indent=4)

async def gen_caption(_, link, title, duration, user):
    """
    Generates the caption. 
    Prioritizes custom text set by admin. 
    Falls back to default _["stream_1"] if custom text fails or doesn't exist.
    """
    custom_text = get_custom_caption_text()
    
    if custom_text:
        try:
            # We strictly use the formatting placeholders provided
            # {0} = Link, {1} = Title, {2} = Duration, {3} = User
            return custom_text.format(link, title, duration, user)
        except Exception:
            # If the admin messed up the brackets/formatting, fallback to default
            pass
            
    return _["stream_1"].format(link, title, duration, user)

# --- Command Handler ---
# Note: If this file is loaded as a utility, this handler might not register depending on your bot's structure.
# If /setstream doesn't work, move this function to a file in your 'plugins' folder.
@app.on_message(filters.command("setstream") & filters.user(ADMIN_ID))
async def set_stream_message_handler(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>Usage:</b>\n/setstream [Your Text]\n\n"
            "<b>Variables:</b>\n"
            "{0} - Link\n"
            "{1} - Title\n"
            "{2} - Duration\n"
            "{3} - Requested By\n\n"
            "<b>Example:</b>\n"
            "/setstream <b>Playing:</b> <a href={0}>{1}</a>\nDuration: {2}\nUser: {3}"
        )
    
    # We split by space once to get everything after /setstream
    text_to_save = message.text.split(None, 1)[1]
    
    # Strip leading/trailing whitespace but keep internal formatting
    text_to_save = text_to_save.strip()
    
    save_custom_caption_text(text_to_save)
    await message.reply_text("<b>Successfully saved new stream caption!</b>\n\nNext song will use this format.")
# --- Custom Caption Logic End ---


async def stream(
    _,
    mystic,
    user_id,
    result,
    chat_id,
    user_name,
    original_chat_id,
    video: Union[bool, str] = None,
    streamtype: Union[bool, str] = None,
    spotify: Union[bool, str] = None,
    forceplay: Union[bool, str] = None,
):
    if not result:
        return
    if forceplay:
        await SHUKLA.force_stop_stream(chat_id)
    if streamtype == "playlist":
        msg = f"{_['play_19']}\n\n"
        count = 0
        for search in result:
            if int(count) == config.PLAYLIST_FETCH_LIMIT:
                continue
            try:
                (
                    title,
                    duration_min,
                    duration_sec,
                    thumbnail,
                    vidid,
                ) = await YouTube.details(search, False if spotify else True)
            except:
                continue
            if str(duration_min) == "None":
                continue
            if duration_sec > config.DURATION_LIMIT:
                continue
            if await is_active_chat(chat_id):
                await put_queue(
                    chat_id,
                    original_chat_id,
                    f"vid_{vidid}",
                    title,
                    duration_min,
                    user_name,
                    vidid,
                    user_id,
                    "video" if video else "audio",
                )
                position = len(db.get(chat_id)) - 1
                count += 1
                msg += f"{count}. {title[:70]}\n"
                msg += f"{_['play_20']} {position}\n\n"
            else:
                if not forceplay:
                    db[chat_id] = []
                status = True if video else None
                try:
                    file_path, direct = await YouTube.download(
                        vidid, mystic, video=status, videoid=True
                    )
                except:
                    raise AssistantErr(_["play_14"])
                await SHUKLA.join_call(
                    chat_id,
                    original_chat_id,
                    file_path,
                    video=status,
                    image=thumbnail,
                )
                await put_queue(
                    chat_id,
                    original_chat_id,
                    file_path if direct else f"vid_{vidid}",
                    title,
                    duration_min,
                    user_name,
                    vidid,
                    user_id,
                    "video" if video else "audio",
                    forceplay=forceplay,
                )
                img = await get_thumb(vidid)
                button = stream_markup(_, chat_id)
                
                # Generated Caption
                caption_text = await gen_caption(
                    _,
                    f"https://t.me/{app.username}?start=info_{vidid}",
                    title[:23],
                    duration_min,
                    user_name
                )

                run = await app.send_photo(
                    original_chat_id,
                    photo=img,
                    has_spoiler=True,
                    caption=caption_text,
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"
        if count == 0:
            return
        else:
            link = await SHUKLABin(msg)
            lines = msg.count("\n")
            if lines >= 17:
                car = os.linesep.join(msg.split(os.linesep)[:17])
            else:
                car = msg
            carbon = await Carbon.generate(car, randint(100, 10000000))
            upl = close_markup(_)
            return await app.send_photo(
                original_chat_id,
                photo=carbon,
                caption=_["play_21"].format(position, link),
                reply_markup=upl,
            )
    elif streamtype == "youtube":
        link = result["link"]
        vidid = result["vidid"]
        title = (result["title"]).title()
        duration_min = result["duration_min"]
        thumbnail = result["thumb"]
        status = True if video else None
        try:
            file_path, direct = await YouTube.download(
                vidid, mystic, videoid=True, video=status
            )
        except:
            raise AssistantErr(_["play_14"])
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path if direct else f"vid_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(
                chat_id=original_chat_id,
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await SHUKLA.join_call(
                chat_id,
                original_chat_id,
                file_path,
                video=status,
                image=thumbnail,
            )
            await put_queue(
                chat_id,
                original_chat_id,
                file_path if direct else f"vid_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
                forceplay=forceplay,
            )
            img = await get_thumb(vidid)
            button = stream_markup(_, chat_id)
            
            # Generated Caption
            caption_text = await gen_caption(
                _,
                f"https://t.me/{app.username}?start=info_{vidid}",
                title[:23],
                duration_min,
                user_name
            )

            run = await app.send_photo(
                original_chat_id,
                photo=img,
                has_spoiler=True,
                caption=caption_text,
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"
    elif streamtype == "soundcloud":
        file_path = result["filepath"]
        title = result["title"]
        duration_min = result["duration_min"]
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "audio",
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(
                chat_id=original_chat_id,
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await SHUKLA.join_call(chat_id, original_chat_id, file_path, video=None)
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "audio",
                forceplay=forceplay,
            )
            button = stream_markup(_, chat_id)
            
            # Generated Caption
            caption_text = await gen_caption(
                _,
                config.SUPPORT_CHAT,
                title[:23],
                duration_min,
                user_name
            )

            run = await app.send_photo(
                original_chat_id,
                photo=config.SOUNCLOUD_IMG_URL,
                caption=caption_text,
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
    elif streamtype == "telegram":
        file_path = result["path"]
        link = result["link"]
        title = (result["title"]).title()
        duration_min = result["dur"]
        status = True if video else None
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(
                chat_id=original_chat_id,
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await SHUKLA.join_call(chat_id, original_chat_id, file_path, video=status)
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "video" if video else "audio",
                forceplay=forceplay,
            )
            if video:
                await add_active_video_chat(chat_id)
            button = stream_markup(_, chat_id)

            # Generated Caption
            caption_text = await gen_caption(
                _,
                link,
                title[:23],
                duration_min,
                user_name
            )

            run = await app.send_photo(
                original_chat_id,
                photo=config.TELEGRAM_VIDEO_URL if video else config.TELEGRAM_AUDIO_URL,
                caption=caption_text,
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
    elif streamtype == "live":
        link = result["link"]
        vidid = result["vidid"]
        title = (result["title"]).title()
        thumbnail = result["thumb"]
        duration_min = "Live Track"
        status = True if video else None
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                f"live_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(
                chat_id=original_chat_id,
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            n, file_path = await YouTube.video(link)
            if n == 0:
                raise AssistantErr(_["str_3"])
            await SHUKLA.join_call(
                chat_id,
                original_chat_id,
                file_path,
                video=status,
                image=thumbnail if thumbnail else None,
            )
            await put_queue(
                chat_id,
                original_chat_id,
                f"live_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
                forceplay=forceplay,
            )
            img = await get_thumb(vidid)
            button = stream_markup(_, chat_id)

            # Generated Caption
            caption_text = await gen_caption(
                _,
                f"https://t.me/{app.username}?start=info_{vidid}",
                title[:23],
                duration_min,
                user_name
            )

            run = await app.send_photo(
                original_chat_id,
                photo=img,
                has_spoiler=True,
                caption=caption_text,
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
    elif streamtype == "index":
        link = result
        title = "ɪɴᴅᴇx ᴏʀ ᴍ3ᴜ8 ʟɪɴᴋ"
        duration_min = "00:00"
        if await is_active_chat(chat_id):
            await put_queue_index(
                chat_id,
                original_chat_id,
                "index_url",
                title,
                duration_min,
                user_name,
                link,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await mystic.edit_text(
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await SHUKLA.join_call(
                chat_id,
                original_chat_id,
                link,
                video=True if video else None,
            )
            await put_queue_index(
                chat_id,
                original_chat_id,
                "index_url",
                title,
                duration_min,
                user_name,
                link,
                "video" if video else "audio",
                forceplay=forceplay,
            )
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=config.STREAM_IMG_URL,
                has_spoiler=True,
                caption=_["stream_2"].format(user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            await mystic.delete()
