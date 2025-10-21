import asyncio
import os
import re
from typing import Union

import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch

from SHUKLAMUSIC.utils.database import is_on_off
from SHUKLAMUSIC.utils.formatters import time_to_seconds

YOUTUBE_API_KEY = "30DxNexGenBotsbfed26"  # <-- Your API key


async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

        # yt-dlp options using API key
        self.YDL_OPTS_AUDIO = {
            "format": "bestaudio[acodec!=iamf.001.001.Opus]/bestaudio/best",
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "geo_bypass": True,
            "nocheckcertificate": True,
            "quiet": True,
            "no_warnings": True,
            "prefer_ffmpeg": True,
            "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
            ],
            "youtube_api_key": YOUTUBE_API_KEY,
        }

        self.YDL_OPTS_VIDEO = {
            "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+bestaudio[acodec!=iamf.001.001.Opus][ext=m4a]",
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "geo_bypass": True,
            "nocheckcertificate": True,
            "quiet": True,
            "no_warnings": True,
            "prefer_ffmpeg": True,
            "merge_output_format": "mp4",
            "youtube_api_key": YOUTUBE_API_KEY,
        }

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        text = ""
        offset = None
        length = None
        for message in messages:
            if offset:
                break
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length
                        break
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        if offset is None:
            return None
        return text[offset: offset + length]

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            duration_sec = 0 if duration_min is None else int(time_to_seconds(duration_min))
        return title, duration_min, duration_sec, thumbnail, vidid

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            vidid = result["id"]
            yturl = result["link"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        return {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }, vidid

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ):
        if videoid:
            link = self.base + link
        loop = asyncio.get_running_loop()

        def audio_dl():
            ydl = yt_dlp.YoutubeDL(self.YDL_OPTS_AUDIO)
            info = ydl.extract_info(link, download=False)
            path = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(path):
                return path
            ydl.download([link])
            return path

        def video_dl():
            ydl = yt_dlp.YoutubeDL(self.YDL_OPTS_VIDEO)
            info = ydl.extract_info(link, download=False)
            path = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(path):
                return path
            ydl.download([link])
            return path

        def song_audio_dl():
            opts = self.YDL_OPTS_AUDIO.copy()
            opts["format"] = format_id
            opts["outtmpl"] = f"downloads/{title}.%(ext)s"
            ydl = yt_dlp.YoutubeDL(opts)
            ydl.download([link])

        def song_video_dl():
            opts = self.YDL_OPTS_VIDEO.copy()
            opts["format"] = f"{format_id}+140"
            opts["outtmpl"] = f"downloads/{title}.mp4"
            ydl = yt_dlp.YoutubeDL(opts)
            ydl.download([link])

        if songvideo:
            await loop.run_in_executor(None, song_video_dl)
            return f"downloads/{title}.mp4"
        elif songaudio:
            await loop.run_in_executor(None, song_audio_dl)
            return f"downloads/{title}.mp3"
        elif video:
            if await is_on_off(1):
                downloaded_file = await loop.run_in_executor(None, video_dl)
                direct = True
            else:
                ydl = yt_dlp.YoutubeDL(self.YDL_OPTS_VIDEO)
                info = ydl.extract_info(link, download=False)
                downloaded_file = info["url"]
                direct = None
        else:
            direct = True
            downloaded_file = await loop.run_in_executor(None, audio_dl)
        return downloaded_file, direct
