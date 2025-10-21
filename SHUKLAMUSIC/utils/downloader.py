import os
import asyncio
from os import path
import yt_dlp

COOKIES_FILE = "SHUKLAMUSIC/assets/cookies.txt"
DOWNLOAD_DIR = "downloads"
YOUTUBE_API_KEY = "30DxNexGenBotsbfed26"  # <-- Your API key

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
    "prefer_ffmpeg": True,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
    "youtube_api_key": YOUTUBE_API_KEY,
}

# Standard yt-dlp options for video
YDL_VIDEO_OPTS = {
    "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+bestaudio[acodec!=iamf.001.001.Opus][ext=m4a]",
    "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),
    "geo_bypass": True,
    "nocheckcertificate": True,
    "quiet": True,
    "no_warnings": True,
    "prefer_ffmpeg": True,
    "merge_output_format": "mp4",
    "youtube_api_key": YOUTUBE_API_KEY,
}


async def async_download(url: str, is_video=False, title: str = None, progress_hook=None) -> str:
    """
    Downloads audio or video from a YouTube URL asynchronously.
    Returns the local file path or None if failed.
    Uses API key first; falls back to cookies if YouTube blocks download.
    """
    loop = asyncio.get_running_loop()

    def download_sync(opts):
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                ext = "mp4" if is_video else "mp3"
                if title:
                    filename = os.path.join(DOWNLOAD_DIR, f"{title}.{ext}")
                return filename
        except Exception as e:
            return str(e)

    # Prepare options
    opts = YDL_VIDEO_OPTS.copy() if is_video else YDL_AUDIO_OPTS.copy()
    if title:
        ext = "mp4" if is_video else "mp3"
        opts["outtmpl"] = os.path.join(DOWNLOAD_DIR, f"{title}.{ext}")
    if progress_hook:
        opts["progress_hooks"] = [progress_hook]

    # Try API key first
    result = await loop.run_in_executor(None, download_sync, opts)

    # If blocked by YouTube bot check, fallback to cookies
    if isinstance(result, str) and "Sign in to confirm" in result:
        opts["cookiefile"] = COOKIES_FILE
        result = await loop.run_in_executor(None, download_sync, opts)

    # Return downloaded file path or None if failed
    return result if os.path.exists(result) else None
