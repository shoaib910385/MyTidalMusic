import os
import asyncio
from os import path
import yt_dlp

COOKIES_FILE = "SHUKLAMUSIC/assets/cookies.txt"
DOWNLOAD_DIR = "downloads"

# Ensure download directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Standard yt-dlp options for audio
YDL_AUDIO_OPTS = {
    "format": "bestaudio[ext=m4a][acodec!=iamf.001.001.Opus]",
    "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),
    "geo_bypass": True,
    "nocheckcertificate": True,
    "quiet": True,
    "no_warnings": True,
    "cookiefile": COOKIES_FILE,
    "prefer_ffmpeg": True,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
}

# Standard yt-dlp options for video
YDL_VIDEO_OPTS = {
    "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+bestaudio[acodec!=iamf.001.001.Opus][ext=m4a]",
    "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),
    "geo_bypass": True,
    "nocheckcertificate": True,
    "quiet": True,
    "no_warnings": True,
    "cookiefile": COOKIES_FILE,
    "prefer_ffmpeg": True,
    "merge_output_format": "mp4",
}


async def async_download(url: str, is_video=False, title: str = None, progress_hook=None) -> str:
    """
    Downloads audio or video from a YouTube URL asynchronously.
    Returns the local file path or None if failed.
    """
    loop = asyncio.get_running_loop()

    def download_sync():
        try:
            opts = YDL_VIDEO_OPTS.copy() if is_video else YDL_AUDIO_OPTS.copy()
            if title:
                ext = "mp4" if is_video else "mp3"
                opts["outtmpl"] = os.path.join(DOWNLOAD_DIR, f"{title}.{ext}")
            if progress_hook:
                opts["progress_hooks"] = [progress_hook]

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                if is_video and title:
                    filename = os.path.join(DOWNLOAD_DIR, f"{title}.mp4")
                elif not is_video and title:
                    filename = os.path.join(DOWNLOAD_DIR, f"{title}.mp3")
                return filename
        except Exception as e:
            print(f"[Downloader Error] {e}")
            return None

    return await loop.run_in_executor(None, download_sync)
