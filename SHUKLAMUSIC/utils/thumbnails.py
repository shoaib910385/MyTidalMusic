"""
SHUKLAMUSIC - Advanced Thumbnail Generator
Credits: @hehe_staller | Enhanced Template System

Features:
- Template-based thumbnail generation for professional look
- JioSaavn API integration with fallback to YouTube
- Google Sans font support with fallbacks
- Fast async operations with caching
- 1280x720 output optimized for Telegram
"""

import os
import re
import aiohttp
import aiofiles
import logging
from typing import Optional, Dict, Any
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from py_yt import VideosSearch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
TEMPLATE_PATH = "SHUKLAMUSIC/assets/template.png"
CACHE_DIR = "cache"
JIOSAAVN_API = "https://jiosavan-lilac.vercel.app"

# Font paths (in order of preference)
FONT_PATHS = {
    "title": [
        ("SHUKLAMUSIC/assets/GoogleSans-Bold.ttf", 34),
        ("SHUKLAMUSIC/assets/font.ttf", 38),
        ("SHUKLAMUSIC/assets/font3.ttf", 42),
    ],
    "artist": [
        ("SHUKLAMUSIC/assets/GoogleSans-Medium.ttf", 26),
        ("SHUKLAMUSIC/assets/GoogleSans-Regular.ttf", 26),
        ("SHUKLAMUSIC/assets/font2.ttf", 28),
    ],
    "duration": [
        ("SHUKLAMUSIC/assets/GoogleSans-Regular.ttf", 22),
        ("SHUKLAMUSIC/assets/font2.ttf", 24),
    ]
}

# Template positions (for 1280x720 template)
POSITIONS = {
    "image": {"x": 75, "y": 110, "width": 500, "height": 500, "radius": 40},
    "title": {"x": 620, "y": 135, "max_width": 420},  # Keep away from star/menu icons
    "artist": {"x": 620, "y": 195},
    "duration": {"x": 1080, "y": 315},  # Right side, aligned with progress bar area
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_font(font_type: str) -> ImageFont.FreeTypeFont:
    """Load font with fallback chain"""
    for path, size in FONT_PATHS.get(font_type, []):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def truncate_to_width(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> str:
    """Truncate text to fit within max_width pixels"""
    words = text.split()
    result = ""
    
    for word in words:
        test = result + " " + word if result else word
        try:
            bbox = font.getbbox(test)
            if bbox and bbox[2] <= max_width:
                result = test
            else:
                if not result:
                    # Even first word is too long, truncate it
                    for i in range(len(word), 0, -1):
                        test = word[:i] + "..."
                        bbox = font.getbbox(test)
                        if bbox and bbox[2] <= max_width:
                            return test
                return result + "..." if result else word[:10] + "..."
        except:
            # Fallback: truncate by character count
            if len(test) > 25:
                return result + "..." if result else word[:15] + "..."
            result = test
    
    return result


def truncate_words(text: str, max_words: int = 4) -> str:
    """Truncate text to max words, adding ellipsis if truncated"""
    words = text.split()
    if len(words) > max_words:
        return " ".join(words[:max_words]) + "..."
    return text


def format_duration(seconds: int) -> str:
    """Format duration seconds to MM:SS"""
    if not seconds:
        return "0:00"
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{mins}:{secs:02d}"


def create_rounded_mask(size: tuple, radius: int) -> Image.Image:
    """Create a rounded rectangle mask"""
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, size[0], size[1]], radius=radius, fill=255)
    return mask


# ============================================================================
# JIOSAAVN API FUNCTIONS
# ============================================================================

async def search_jiosaavn(query: str) -> Optional[Dict[str, Any]]:
    """
    Search for a song on JioSaavn API
    
    Returns:
        Dict with song details or None if failed
    """
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{JIOSAAVN_API}/api/search/songs?query={query}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status != 200:
                    return None
                
                data = await resp.json()
                if not data.get("success") or not data.get("data", {}).get("results"):
                    return None
                
                song = data["data"]["results"][0]
                
                # Extract primary artist
                artists = song.get("artists", {})
                primary_artists = artists.get("primary", [])
                artist_name = primary_artists[0].get("name", "Unknown Artist") if primary_artists else "Unknown Artist"
                
                # Get highest quality image
                images = song.get("image", [])
                image_url = None
                for img in images:
                    if img.get("quality") == "500x500":
                        image_url = img.get("url")
                        break
                if not image_url and images:
                    image_url = images[-1].get("url")
                
                # Get best audio URL
                download_urls = song.get("downloadUrl", [])
                audio_url = None
                quality_priority = ["320kbps", "160kbps", "96kbps", "48kbps", "12kbps"]
                for quality in quality_priority:
                    for dl in download_urls:
                        if dl.get("quality") == quality:
                            audio_url = dl.get("url")
                            break
                    if audio_url:
                        break
                
                return {
                    "id": song.get("id", ""),
                    "title": song.get("name", "Unknown"),
                    "artist": artist_name,
                    "duration": song.get("duration", 0),
                    "duration_min": format_duration(song.get("duration", 0)),
                    "image": image_url,
                    "audio_url": audio_url,
                    "url": song.get("url", ""),
                }
    except Exception as e:
        logger.error(f"JioSaavn search error: {e}")
        return None


async def download_image(url: str, output_path: str) -> bool:
    """Download image from URL to file"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    async with aiofiles.open(output_path, mode="wb") as f:
                        await f.write(await resp.read())
                    return True
    except Exception as e:
        logger.error(f"Image download error: {e}")
    return False


# ============================================================================
# TEMPLATE THUMBNAIL GENERATOR
# ============================================================================

async def generate_template_thumbnail(
    song_data: Dict[str, Any],
    output_path: str
) -> Optional[str]:
    """
    Generate thumbnail using template
    
    Layout:
    - Left: Song image (rounded rectangle)
    - Top-right: Title (auto-truncated to fit)
    - Middle-right: Artist name
    - Bottom-right: Duration
    """
    try:
        # Check template exists
        if not os.path.exists(TEMPLATE_PATH):
            logger.warning(f"Template not found: {TEMPLATE_PATH}")
            return None
        
        # Download song image
        temp_img_path = f"{CACHE_DIR}/temp_img_{song_data['id']}.jpg"
        if not await download_image(song_data["image"], temp_img_path):
            return None
        
        # Open images
        template = Image.open(TEMPLATE_PATH).convert("RGBA")
        song_img = Image.open(temp_img_path).convert("RGBA")
        
        # Resize song image to fit template area
        img_size = (POSITIONS["image"]["width"], POSITIONS["image"]["height"])
        song_img = song_img.resize(img_size, Image.Resampling.LANCZOS)
        
        # Create rounded mask
        mask = create_rounded_mask(img_size, POSITIONS["image"]["radius"])
        
        # Paste song image onto template
        img_pos = (POSITIONS["image"]["x"], POSITIONS["image"]["y"])
        template.paste(song_img, img_pos, mask)
        
        # Prepare text drawing
        draw = ImageDraw.Draw(template)
        
        # Load fonts
        title_font = get_font("title")
        artist_font = get_font("artist")
        duration_font = get_font("duration")
        
        # Truncate title to fit within max_width
        display_title = truncate_to_width(
            song_data["title"], 
            title_font, 
            POSITIONS["title"]["max_width"]
        )
        
        # Draw title (white, bold)
        title_pos = (POSITIONS["title"]["x"], POSITIONS["title"]["y"])
        draw.text(title_pos, display_title, font=title_font, fill=(255, 255, 255))
        
        # Draw artist (light gray)
        artist_pos = (POSITIONS["artist"]["x"], POSITIONS["artist"]["y"])
        draw.text(artist_pos, song_data["artist"], font=artist_font, fill=(200, 200, 200))
        
        # Draw duration (right-aligned, light gray)
        duration_text = f"-{song_data['duration_min']}"
        duration_pos = (POSITIONS["duration"]["x"], POSITIONS["duration"]["y"])
        draw.text(duration_pos, duration_text, font=duration_font, fill=(180, 180, 180))
        
        # Save result
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        template.save(output_path, "PNG", quality=95)
        
        # Cleanup temp file
        if os.path.exists(temp_img_path):
            os.remove(temp_img_path)
        
        logger.info(f"Generated thumbnail: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Thumbnail generation error: {e}")
        return None


# ============================================================================
# YOUTUBE THUMBNAIL GENERATOR (FALLBACK)
# ============================================================================

async def generate_youtube_thumbnail(videoid: str, output_path: str) -> Optional[str]:
    """Generate thumbnail for YouTube video (original style with enhancements)"""
    try:
        # Fetch video info
        results = VideosSearch(f"https://youtube.com/watch?v={videoid}", limit=1)
        result_data = await results.next()
        
        if not result_data or not result_data.get("result"):
            return None
        
        result = result_data["result"][0]
        title = re.sub(r"\W+", " ", result.get("title", "Unknown")).title()
        duration = result.get("duration", "Live")
        channel = result.get("channel", {}).get("name", "Unknown")
        views = result.get("viewCount", {}).get("short", "Unknown")
        thumbnail_url = result.get("thumbnails", [{}])[0].get("url", "").split("?")[0]
        
        if not thumbnail_url:
            return None
        
        # Download thumbnail
        temp_path = f"{CACHE_DIR}/yt_thumb_{videoid}.jpg"
        if not await download_image(thumbnail_url, temp_path):
            return None
        
        # Create enhanced thumbnail
        thumb = Image.open(temp_path)
        thumb = thumb.resize((1280, 720), Image.Resampling.LANCZOS)
        
        # Apply blur background
        bg = thumb.filter(ImageFilter.BoxBlur(25))
        enhancer = ImageEnhance.Brightness(bg)
        bg = enhancer.enhance(0.5)
        
        # Create circular thumbnail
        circle_size = 400
        circle_img = thumb.resize((circle_size, circle_size), Image.Resampling.LANCZOS)
        
        # Create circular mask
        mask = Image.new("L", (circle_size, circle_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse([0, 0, circle_size, circle_size], fill=255)
        
        # Paste circle onto background
        circle_pos = (120, 160)
        bg.paste(circle_img, circle_pos, mask)
        
        # Add text
        draw = ImageDraw.Draw(bg)
        title_font = get_font("title")
        artist_font = get_font("artist")
        
        # Truncate and draw title
        title_lines = [title[:30], title[30:60] if len(title) > 30 else ""]
        draw.text((565, 180), title_lines[0], font=title_font, fill=(255, 255, 255))
        if title_lines[1]:
            draw.text((565, 235), title_lines[1], font=title_font, fill=(255, 255, 255))
        
        # Draw channel and views
        draw.text((565, 320), f"{channel}  |  {views}", font=artist_font, fill=(220, 220, 220))
        
        # Draw progress bar
        if duration != "Live":
            bar_y = 380
            draw.line([(565, bar_y), (1145, bar_y)], fill=(100, 100, 100), width=8)
            draw.line([(565, bar_y), (850, bar_y)], fill=(255, 50, 100), width=8)
            draw.ellipse([(840, bar_y-10), (860, bar_y+10)], fill=(255, 50, 100))
        
        # Draw duration
        draw.text((565, 400), "00:00", font=artist_font, fill=(255, 255, 255))
        draw.text((1080, 400), duration, font=artist_font, fill=(255, 255, 255))
        
        # Save
        bg.save(output_path, "PNG", quality=95)
        
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return output_path
        
    except Exception as e:
        logger.error(f"YouTube thumbnail error: {e}")
        return None


# ============================================================================
# MAIN PUBLIC API
# ============================================================================

async def get_thumb(
    videoid: str,
    query: str = None,
    use_jiosaavn: bool = True,
    song_data: Dict[str, Any] = None
) -> Optional[str]:
    """
    Get thumbnail for a video/song
    
    Args:
        videoid: YouTube video ID or unique identifier
        query: Search query for JioSaavn
        use_jiosaavn: Whether to try JioSaavn API first
        song_data: Pre-fetched song data (optional)
    
    Returns:
        Path to generated thumbnail or None
    """
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        # Check cache first
        cache_path = f"{CACHE_DIR}/{videoid}_custom.png"
        if os.path.isfile(cache_path):
            return cache_path
        
        # Use provided song data or fetch from JioSaavn
        if song_data:
            result = await generate_template_thumbnail(song_data, cache_path)
            if result:
                return result
        
        # Try JioSaavn if enabled and query provided
        if use_jiosaavn and query:
            jiosaavn_data = await search_jiosaavn(query)
            if jiosaavn_data:
                cache_path_js = f"{CACHE_DIR}/js_{jiosaavn_data['id']}_thumb.png"
                result = await generate_template_thumbnail(jiosaavn_data, cache_path_js)
                if result:
                    return result
                # Fallback to raw image URL
                return jiosaavn_data.get("image")
        
        # Fallback to YouTube thumbnail
        return await generate_youtube_thumbnail(videoid, cache_path)
        
    except Exception as e:
        logger.error(f"get_thumb error: {e}")
        return None


async def get_jiosaavn_thumb(query: str) -> Optional[str]:
    """
    Get thumbnail specifically for JioSaavn search
    
    Args:
        query: Song search query
    
    Returns:
        Path to generated thumbnail or image URL
    """
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        # Search for song
        song_data = await search_jiosaavn(query)
        if not song_data:
            return None
        
        # Check cache
        cache_path = f"{CACHE_DIR}/js_{song_data['id']}_thumb.png"
        if os.path.isfile(cache_path):
            return cache_path
        
        # Generate thumbnail
        result = await generate_template_thumbnail(song_data, cache_path)
        return result or song_data.get("image")
        
    except Exception as e:
        logger.error(f"get_jiosaavn_thumb error: {e}")
        return None


# Legacy compatibility
get_youtube_thumb = generate_youtube_thumbnail
