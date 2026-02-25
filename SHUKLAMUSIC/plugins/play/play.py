import random
import string
import aiohttp
import asyncio
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InputMediaPhoto, Message
from pytgcalls.exceptions import NoActiveGroupCall

import config
from SHUKLAMUSIC import Apple, Resso, SoundCloud, Spotify, Telegram, YouTube, app
from SHUKLAMUSIC.core.call import SHUKLA
from SHUKLAMUSIC.utils import seconds_to_min, time_to_seconds
from SHUKLAMUSIC.utils.channelplay import get_channeplayCB
from SHUKLAMUSIC.utils.decorators.language import languageCB
from SHUKLAMUSIC.utils.decorators.play import PlayWrapper
from SHUKLAMUSIC.utils.formatters import formats
from SHUKLAMUSIC.utils.inline import (
    botplaylist_markup,
    livestream_markup,
    playlist_markup,
    slider_markup,
    track_markup,
)
from SHUKLAMUSIC.utils.logger import play_logs
from SHUKLAMUSIC.utils.stream.stream import stream
from config import BANNED_USERS, lyrical

# JioSaavn API Base URL
JIOSAAVN_API = "https://jiosavan-lilac.vercel.app"


async def search_jiosaavn_song(query: str):
    """
    Search for a song on JioSaavn API
    Returns: dict with song details or None if failed
    """
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{JIOSAAVN_API}/api/search/songs?query={query}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                
                if not data.get("success") or not data.get("data", {}).get("results"):
                    return None
                
                song = data["data"]["results"][0]
                
                # Extract song details
                song_id = song.get("id", "")
                title = song.get("name", "Unknown Title")
                duration = song.get("duration", 0)
                
                # Get primary artist
                artists = song.get("artists", {})
                primary_artists = artists.get("primary", [])
                artist_name = primary_artists[0].get("name", "Unknown Artist") if primary_artists else "Unknown Artist"
                
                # Get song image (highest quality)
                images = song.get("image", [])
                image_url = None
                for img in images:
                    if img.get("quality") == "500x500":
                        image_url = img.get("url")
                        break
                if not image_url and images:
                    image_url = images[-1].get("url")
                
                # Get download URL (160kbps or 320kbps)
                download_urls = song.get("downloadUrl", [])
                audio_url = None
                
                # Priority: 160kbps > 320kbps > 96kbps > 48kbps > 12kbps
                quality_priority = ["160kbps", "320kbps", "96kbps", "48kbps", "12kbps"]
                for quality in quality_priority:
                    for dl in download_urls:
                        if dl.get("quality") == quality:
                            audio_url = dl.get("url")
                            break
                    if audio_url:
                        break
                
                if not audio_url and download_urls:
                    audio_url = download_urls[-1].get("url")
                
                if not audio_url:
                    return None
                
                # Format duration
                duration_min = "00:00"
                if duration:
                    minutes = int(duration) // 60
                    seconds = int(duration) % 60
                    duration_min = f"{minutes}:{seconds:02d}"
                
                return {
                    "id": song_id,
                    "title": title,
                    "artist": artist_name,
                    "duration": duration,
                    "duration_min": duration_min,
                    "image": image_url,
                    "audio_url": audio_url,
                    "url": song.get("url", ""),
                }
    except Exception as e:
        print(f"JioSaavn API Error: {e}")
        return None


async def get_jiosaavn_thumbnail(song_data: dict, output_path: str):
    """
    Generate custom thumbnail using template
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        import aiofiles
        import os
        
        # Template path (user will place this in assets folder)
        template_path = "SHUKLAMUSIC/assets/template.png"
        
        # Download song image
        async with aiohttp.ClientSession() as session:
            async with session.get(song_data["image"]) as resp:
                if resp.status == 200:
                    song_img_data = await resp.read()
                    song_img_path = f"cache/temp_song_img_{song_data['id']}.jpg"
                    async with aiofiles.open(song_img_path, mode="wb") as f:
                        await f.write(song_img_data)
                else:
                    return None
        
        # Open template and song image
        template = Image.open(template_path)
        song_img = Image.open(song_img_path)
        
        # Resize song image to fit in template (left side area ~400x400)
        song_img = song_img.resize((380, 380), Image.Resampling.LANCZOS)
        
        # Create rounded corners for song image
        mask = Image.new("L", (380, 380), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.rounded_rectangle([0, 0, 380, 380], radius=30, fill=255)
        
        # Paste song image onto template (position based on template design)
        # Left side position (adjust as needed)
        img_position = (60, 60)
        template.paste(song_img, img_position, mask)
        
        # Prepare text
        draw = ImageDraw.Draw(template)
        
        # Try to load Google Sans font, fallback to default
        try:
            title_font = ImageFont.truetype("SHUKLAMUSIC/assets/GoogleSans-Bold.ttf", 42)
            artist_font = ImageFont.truetype("SHUKLAMUSIC/assets/GoogleSans-Regular.ttf", 32)
            duration_font = ImageFont.truetype("SHUKLAMUSIC/assets/GoogleSans-Medium.ttf", 28)
        except:
            try:
                title_font = ImageFont.truetype("SHUKLAMUSIC/assets/font.ttf", 42)
                artist_font = ImageFont.truetype("SHUKLAMUSIC/assets/font2.ttf", 32)
                duration_font = ImageFont.truetype("SHUKLAMUSIC/assets/font2.ttf", 28)
            except:
                title_font = ImageFont.load_default()
                artist_font = ImageFont.load_default()
                duration_font = ImageFont.load_default()
        
        # Truncate title to 4 words max
        title_words = song_data["title"].split()[:4]
        display_title = " ".join(title_words)
        if len(song_data["title"].split()) > 4:
            display_title += "..."
        
        # Text positions (right side of template)
        # Green area - Title
        title_position = (480, 120)
        draw.text(title_position, display_title, font=title_font, fill=(255, 255, 255))
        
        # Blue area - Artist
        artist_position = (480, 190)
        draw.text(artist_position, song_data["artist"], font=artist_font, fill=(200, 200, 200))
        
        # Purple area - Duration (bottom right)
        duration_position = (1050, 350)
        draw.text(duration_position, song_data["duration_min"], font=duration_font, fill=(180, 180, 180))
        
        # Save thumbnail
        template.save(output_path, "PNG")
        
        # Cleanup temp file
        if os.path.exists(song_img_path):
            os.remove(song_img_path)
        
        return output_path
        
    except Exception as e:
        print(f"Thumbnail generation error: {e}")
        return None


# Audio commands that use JioSaavn API
AUDIO_COMMANDS = ["play", "cplay", "cvplay", "playforce", "cplayforce"]
# Video commands that use YouTube
VIDEO_COMMANDS = ["vplay", "vplayforce", "cvplayforce"]


@app.on_message(
    filters.command(AUDIO_COMMANDS + VIDEO_COMMANDS, prefixes=["/", "!", "%", ",", "", ".", "@", "#"])
    & filters.group
    & ~BANNED_USERS
)
@PlayWrapper
async def play_command(
    client,
    message: Message,
    _,
    chat_id,
    video,
    channel,
    playmode,
    url,
    fplay,
):
    mystic = await message.reply_text(
        _["play_2"].format(channel) if channel else _["play_1"]
    )
    
    # Determine if this is a video command
    command = message.command[0].lower()
    is_video_command = command in ["vplay", "vplayforce"] or (command == "cvplayforce" and video)
    
    plist_id = None
    slider = None
    plist_type = None
    spotify = None
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    audio_telegram = (
        (message.reply_to_message.audio or message.reply_to_message.voice)
        if message.reply_to_message
        else None
    )
    video_telegram = (
        (message.reply_to_message.video or message.reply_to_message.document)
        if message.reply_to_message
        else None
    )
    
    # Handle Telegram audio reply
    if audio_telegram:
        if audio_telegram.file_size > 104857600:
            return await mystic.edit_text(_["play_5"])
        duration_min = seconds_to_min(audio_telegram.duration)
        if (audio_telegram.duration) > config.DURATION_LIMIT:
            return await mystic.edit_text(
                _["play_6"].format(config.DURATION_LIMIT_MIN, app.mention)
            )
        file_path = await Telegram.get_filepath(audio=audio_telegram)
        if await Telegram.download(_, message, mystic, file_path):
            message_link = await Telegram.get_link(message)
            file_name = await Telegram.get_filename(audio_telegram, audio=True)
            dur = await Telegram.get_duration(audio_telegram, file_path)
            details = {
                "title": file_name,
                "link": message_link,
                "path": file_path,
                "dur": dur,
            }
            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    message.chat.id,
                    streamtype="telegram",
                    forceplay=fplay,
                )
            except Exception as e:
                ex_type = type(e).__name__
                err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
                return await mystic.edit_text(err)
            return await mystic.delete()
        return
    
    # Handle Telegram video reply
    elif video_telegram:
        if message.reply_to_message.document:
            try:
                ext = video_telegram.file_name.split(".")[-1]
                if ext.lower() not in formats:
                    return await mystic.edit_text(
                        _["play_7"].format(f"{' | '.join(formats)}")
                    )
            except:
                return await mystic.edit_text(
                    _["play_7"].format(f"{' | '.join(formats)}")
                )
        if video_telegram.file_size > config.TG_VIDEO_FILESIZE_LIMIT:
            return await mystic.edit_text(_["play_8"])
        file_path = await Telegram.get_filepath(video=video_telegram)
        if await Telegram.download(_, message, mystic, file_path):
            message_link = await Telegram.get_link(message)
            file_name = await Telegram.get_filename(video_telegram)
            dur = await Telegram.get_duration(video_telegram, file_path)
            details = {
                "title": file_name,
                "link": message_link,
                "path": file_path,
                "dur": dur,
            }
            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    message.chat.id,
                    video=True,
                    streamtype="telegram",
                    forceplay=fplay,
                )
            except Exception as e:
                ex_type = type(e).__name__
                err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
                return await mystic.edit_text(err)
            return await mystic.delete()
        return
    
    # Handle URL input
    elif url:
        # Existing URL handling logic (YouTube, Spotify, Apple, etc.)
        if await YouTube.exists(url):
            if "playlist" in url:
                try:
                    details = await YouTube.playlist(
                        url,
                        config.PLAYLIST_FETCH_LIMIT,
                        message.from_user.id,
                    )
                except Exception as e:
                    print(e)
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "yt"
                if "&" in url:
                    plist_id = (url.split("=")[1]).split("&")[0]
                else:
                    plist_id = url.split("=")[1]
                img = config.PLAYLIST_IMG_URL
                has_spoiler = True
                cap = _["play_10"]
            elif "https://youtu.be" in url:
                videoid = url.split("/")[-1].split("?")[0]
                details, track_id = await YouTube.track(f"https://www.youtube.com/watch?v={videoid}")
                streamtype = "youtube"
                img = details["thumb"]
                cap = _["play_11"].format(
                    details["title"],
                    details["duration_min"],
                )
            else:
                try:
                    details, track_id = await YouTube.track(url)
                except Exception as e:
                    print(e)
                    return await mystic.edit_text(_["play_3"])
                streamtype = "youtube"
                img = details["thumb"]
                has_spoiler = True
                cap = _["play_11"].format(
                    details["title"],
                    details["duration_min"],
                )
        elif await Spotify.valid(url):
            spotify = True
            if not config.SPOTIFY_CLIENT_ID and not config.SPOTIFY_CLIENT_SECRET:
                return await mystic.edit_text(
                    "» sᴘᴏᴛɪғʏ ɪs ɴᴏᴛ sᴜᴘᴘᴏʀᴛᴇᴅ ʏᴇᴛ.\n\nᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ."
                )
            if "track" in url:
                try:
                    details, track_id = await Spotify.track(url)
                except:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "youtube"
                img = details["thumb"]
                has_spoiler = True
                cap = _["play_10"].format(details["title"], details["duration_min"])
            elif "playlist" in url:
                try:
                    details, plist_id = await Spotify.playlist(url)
                except Exception:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "spplay"
                img = config.SPOTIFY_PLAYLIST_IMG_URL
                cap = _["play_11"].format(app.mention, message.from_user.mention)
            elif "album" in url:
                try:
                    details, plist_id = await Spotify.album(url)
                except:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "spalbum"
                img = config.SPOTIFY_ALBUM_IMG_URL
                cap = _["play_11"].format(app.mention, message.from_user.mention)
            elif "artist" in url:
                try:
                    details, plist_id = await Spotify.artist(url)
                except:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "spartist"
                img = config.SPOTIFY_ARTIST_IMG_URL
                cap = _["play_11"].format(message.from_user.first_name)
            else:
                return await mystic.edit_text(_["play_15"])
        elif await Apple.valid(url):
            if "album" in url:
                try:
                    details, track_id = await Apple.track(url)
                except:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "youtube"
                img = details["thumb"]
                has_spoiler = True
                cap = _["play_10"].format(details["title"], details["duration_min"])
            elif "playlist" in url:
                spotify = True
                try:
                    details, plist_id = await Apple.playlist(url)
                except:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "apple"
                cap = _["play_12"].format(app.mention, message.from_user.mention)
                img = url
            else:
                return await mystic.edit_text(_["play_3"])
        elif await Resso.valid(url):
            try:
                details, track_id = await Resso.track(url)
            except:
                return await mystic.edit_text(_["play_3"])
            streamtype = "youtube"
            img = details["thumb"]
            has_spoiler = True
            cap = _["play_10"].format(details["title"], details["duration_min"])
        elif await SoundCloud.valid(url):
            try:
                details, track_path = await SoundCloud.download(url)
            except:
                return await mystic.edit_text(_["play_3"])
            duration_sec = details["duration_sec"]
            if duration_sec > config.DURATION_LIMIT:
                return await mystic.edit_text(
                    _["play_6"].format(
                        config.DURATION_LIMIT_MIN,
                        app.mention,
                    )
                )
            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    message.chat.id,
                    streamtype="soundcloud",
                    forceplay=fplay,
                )
            except Exception as e:
                ex_type = type(e).__name__
                err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
                return await mystic.edit_text(err)
            return await mystic.delete()
        else:
            try:
                await SHUKLA.stream_call(url)
            except NoActiveGroupCall:
                await mystic.edit_text(_["black_9"])
                return await app.send_message(
                    chat_id=config.LOGGER_ID,
                    text=_["play_17"],
                )
            except Exception as e:
                return await mystic.edit_text(_["general_2"].format(type(e).__name__))
            await mystic.edit_text(_["str_2"])
            try:
                await stream(
                    _,
                    mystic,
                    message.from_user.id,
                    url,
                    chat_id,
                    message.from_user.first_name,
                    message.chat.id,
                    video=video,
                    streamtype="index",
                    forceplay=fplay,
                )
            except Exception as e:
                ex_type = type(e).__name__
                err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
                return await mystic.edit_text(err)
            return await play_logs(message, streamtype="M3u8 or Index Link")
    
    # Handle search query (text input)
    else:
        if len(message.command) < 2:
            buttons = botplaylist_markup(_)
            return await mystic.edit_text(
                _["play_18"],
                reply_markup=InlineKeyboardMarkup(buttons),
            )
        
        slider = True
        query = message.text.split(None, 1)[1]
        
        # For video commands, use YouTube directly
        if is_video_command or "-v" in query:
            query = query.replace("-v", "").strip()
            try:
                details, track_id = await YouTube.track(query)
            except:
                return await mystic.edit_text(_["play_3"])
            streamtype = "youtube"
            img = details["thumb"]
            has_spoiler = True
            cap = _["play_11"].format(
                details["title"],
                details["duration_min"],
            )
        else:
            # For audio commands, try JioSaavn API first
            jiosaavn_data = await search_jiosaavn_song(query)
            
            if jiosaavn_data:
                # Use JioSaavn data
                track_id = jiosaavn_data["id"]
                streamtype = "jiosaavn"
                
                # Generate custom thumbnail
                thumb_path = f"cache/jiosaavn_{track_id}_thumb.png"
                img = await get_jiosaavn_thumbnail(jiosaavn_data, thumb_path)
                
                if not img:
                    # Fallback to song image if thumbnail generation fails
                    img = jiosaavn_data["image"]
                
                has_spoiler = True
                cap = _["play_11"].format(
                    jiosaavn_data["title"],
                    jiosaavn_data["duration_min"],
                )
                
                # Create details dict for streaming
                details = {
                    "title": jiosaavn_data["title"],
                    "duration_min": jiosaavn_data["duration_min"],
                    "thumb": img,
                    "link": jiosaavn_data["audio_url"],
                    "duration_sec": jiosaavn_data["duration"] if jiosaavn_data["duration"] else 0,
                    "jiosaavn_data": jiosaavn_data,
                }
            else:
                # Fallback to YouTube if JioSaavn fails
                try:
                    details, track_id = await YouTube.track(query)
                except:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "youtube"
                img = details["thumb"]
                has_spoiler = True
                cap = _["play_11"].format(
                    details["title"],
                    details["duration_min"],
                )
    
    # Direct play mode
    if str(playmode) == "Direct":
        if not plist_type:
            if details.get("duration_min"):
                duration_sec = time_to_seconds(details["duration_min"])
                if duration_sec > config.DURATION_LIMIT:
                    return await mystic.edit_text(
                        _["play_6"].format(config.DURATION_LIMIT_MIN, app.mention)
                    )
            else:
                buttons = livestream_markup(
                    _,
                    track_id,
                    user_id,
                    "v" if video else "a",
                    "c" if channel else "g",
                    "f" if fplay else "d",
                )
                return await mystic.edit_text(
                    _["play_13"],
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
        
        try:
            await stream(
                _,
                mystic,
                user_id,
                details,
                chat_id,
                user_name,
                message.chat.id,
                video=video,
                streamtype=streamtype,
                spotify=spotify,
                forceplay=fplay,
            )
        except Exception as e:
            ex_type = type(e).__name__
            err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
            return await mystic.edit_text(err)
        await mystic.delete()
        return await play_logs(message, streamtype=streamtype)
    
    # Playlist or slider mode
    else:
        if plist_type:
            ran_hash = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=10)
            )
            lyrical[ran_hash] = plist_id
            buttons = playlist_markup(
                _,
                ran_hash,
                message.from_user.id,
                plist_type,
                "c" if channel else "g",
                "f" if fplay else "d",
            )
            await mystic.delete()
            await message.reply_photo(
                photo=img,
                caption=cap,
                reply_markup=InlineKeyboardMarkup(buttons),
            )
            return await play_logs(message, streamtype=f"Playlist : {plist_type}")
        else:
            if slider:
                buttons = slider_markup(
                    _,
                    track_id,
                    message.from_user.id,
                    query,
                    0,
                    "c" if channel else "g",
                    "f" if fplay else "d",
                )
                await mystic.delete()
                await message.reply_photo(
                    photo=img,
                    has_spoiler=has_spoiler,
                    caption=cap,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
                return await play_logs(message, streamtype=f"Searched on {'JioSaavn' if streamtype == 'jiosaavn' else 'Youtube'}")
            else:
                buttons = track_markup(
                    _,
                    track_id,
                    message.from_user.id,
                    "c" if channel else "g",
                    "f" if fplay else "d",
                )
                await mystic.delete()
                await message.reply_photo(
                    photo=img,
                    caption=cap,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
                return await play_logs(message, streamtype=f"URL Searched Inline")


@app.on_callback_query(filters.regex("MusicStream") & ~BANNED_USERS)
@languageCB
async def play_music(client, CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    vidid, user_id, mode, cplay, fplay = callback_request.split("|")
    if CallbackQuery.from_user.id != int(user_id):
        try:
            return await CallbackQuery.answer(_["playcb_1"], show_alert=True)
        except:
            return
    try:
        chat_id, channel = await get_channeplayCB(_, cplay, CallbackQuery)
    except:
        return
    user_name = CallbackQuery.from_user.first_name
    try:
        await CallbackQuery.message.delete()
        await CallbackQuery.answer()
    except:
        pass
    mystic = await CallbackQuery.message.reply_text(
        _["play_2"].format(channel) if channel else _["play_1"]
    )
    try:
        details, track_id = await YouTube.track(vidid, True)
    except:
        return await mystic.edit_text(_["play_3"])
    if details["duration_min"]:
        duration_sec = time_to_seconds(details["duration_min"])
        if duration_sec > config.DURATION_LIMIT:
            return await mystic.edit_text(
                _["play_6"].format(config.DURATION_LIMIT_MIN, app.mention)
            )
    else:
        buttons = livestream_markup(
            _,
            track_id,
            CallbackQuery.from_user.id,
            mode,
            "c" if cplay == "c" else "g",
            "f" if fplay else "d",
        )
        return await mystic.edit_text(
            _["play_13"],
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    video = True if mode == "v" else None
    ffplay = True if fplay == "f" else None
    try:
        await stream(
            _,
            mystic,
            CallbackQuery.from_user.id,
            details,
            chat_id,
            user_name,
            CallbackQuery.message.chat.id,
            video,
            streamtype="youtube",
            forceplay=ffplay,
        )
    except Exception as e:
        ex_type = type(e).__name__
        err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
        return await mystic.edit_text(err)
    return await mystic.delete()


@app.on_callback_query(filters.regex("SHUKLAmousAdmin") & ~BANNED_USERS)
async def SHUKLAmous_check(client, CallbackQuery):
    try:
        await CallbackQuery.answer(
            "» ʀᴇᴠᴇʀᴛ ʙᴀᴄᴋ ᴛᴏ ᴜsᴇʀ ᴀᴄᴄᴏᴜɴᴛ :\n\nᴏᴘᴇɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ sᴇᴛᴛɪɴɢs.\n-> ᴀᴅᴍɪɴɪsᴛʀᴀᴛᴏʀs\n-> ᴄʟɪᴄᴋ ᴏɴ ʏᴏᴜʀ ɴᴀᴍᴇ\n-> ᴜɴᴄʜᴇᴄᴋ ᴀɴᴏɴʏᴍᴏᴜs ᴀᴅᴍɪɴ ᴘᴇʀᴍɪssɪᴏɴs.",
            show_alert=True,
        )
    except:
        pass


@app.on_callback_query(filters.regex("SHUKLAPlaylists") & ~BANNED_USERS)
@languageCB
async def play_playlists_command(client, CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    (
        videoid,
        user_id,
        ptype,
        mode,
        cplay,
        fplay,
    ) = callback_request.split("|")
    if CallbackQuery.from_user.id != int(user_id):
        try:
            return await CallbackQuery.answer(_["playcb_1"], show_alert=True)
        except:
            return
    try:
        chat_id, channel = await get_channeplayCB(_, cplay, CallbackQuery)
    except:
        return
    user_name = CallbackQuery.from_user.first_name
    await CallbackQuery.message.delete()
    try:
        await CallbackQuery.answer()
    except:
        pass
    mystic = await CallbackQuery.message.reply_text(
        _["play_2"].format(channel) if channel else _["play_1"]
    )
    videoid = lyrical.get(videoid)
    video = True if mode == "v" else None
    ffplay = True if fplay == "f" else None
    spotify = True
    if ptype == "yt":
        spotify = False
        try:
            result = await YouTube.playlist(
                videoid,
                config.PLAYLIST_FETCH_LIMIT,
                CallbackQuery.from_user.id,
                True,
            )
        except:
            return await mystic.edit_text(_["play_3"])
    if ptype == "spplay":
        try:
            result, spotify_id = await Spotify.playlist(videoid)
        except:
            return await mystic.edit_text(_["play_3"])
    if ptype == "spalbum":
        try:
            result, spotify_id = await Spotify.album(videoid)
        except:
            return await mystic.edit_text(_["play_3"])
    if ptype == "spartist":
        try:
            result, spotify_id = await Spotify.artist(videoid)
        except:
            return await mystic.edit_text(_["play_3"])
    if ptype == "apple":
        try:
            result, apple_id = await Apple.playlist(videoid, True)
        except:
            return await mystic.edit_text(_["play_3"])
    try:
        await stream(
            _,
            mystic,
            user_id,
            result,
            chat_id,
            user_name,
            CallbackQuery.message.chat.id,
            video,
            streamtype="playlist",
            spotify=spotify,
            forceplay=ffplay,
        )
    except Exception as e:
        ex_type = type(e).__name__
        err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
        return await mystic.edit_text(err)
    return await mystic.delete()


@app.on_callback_query(filters.regex("slider") & ~BANNED_USERS)
@languageCB
async def slider_queries(client, CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    (
        what,
        rtype,
        query,
        user_id,
        cplay,
        fplay,
    ) = callback_request.split("|")
    if CallbackQuery.from_user.id != int(user_id):
        try:
            return await CallbackQuery.answer(_["playcb_1"], show_alert=True)
        except:
            return
    what = str(what)
    rtype = int(rtype)
    if what == "F":
        if rtype == 9:
            query_type = 0
        else:
            query_type = int(rtype + 1)
        try:
            await CallbackQuery.answer(_["playcb_2"])
        except:
            pass
        title, duration_min, thumbnail, vidid = await YouTube.slider(query, query_type)
        buttons = slider_markup(_, vidid, user_id, query, query_type, cplay, fplay)
        med = InputMediaPhoto(
            media=thumbnail,
            caption=_["play_10"].format(
                title.title(),
                duration_min,
            ),
        )
        return await CallbackQuery.edit_message_media(
            media=med, reply_markup=InlineKeyboardMarkup(buttons)
        )
    if what == "B":
        if rtype == 0:
            query_type = 9
        else:
            query_type = int(rtype - 1)
        try:
            await CallbackQuery.answer(_["playcb_2"])
        except:
            pass
        title, duration_min, thumbnail, vidid = await YouTube.slider(query, query_type)
        buttons = slider_markup(_, vidid, user_id, query, query_type, cplay, fplay)
        med = InputMediaPhoto(
            media=thumbnail,
            has_spoiler=True,
            caption=_["play_10"].format(
                title.title(),
                duration_min,
            ),
        )
        return await CallbackQuery.edit_message_media(
            media=med, reply_markup=InlineKeyboardMarkup(buttons)
        )
