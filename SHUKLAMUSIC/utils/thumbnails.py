"""
SHUKLAMUSIC - Thumbnail Generator
Simple and reliable thumbnail generation
"""

import os
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# Paths
TEMPLATE_PATH = "assets/template.png"  # Relative to bot root
CACHE_DIR = "cache"

# Default positions for 1280x720 template
IMG_X, IMG_Y = 75, 110
IMG_SIZE = 500
IMG_RADIUS = 40

TITLE_X, TITLE_Y = 620, 135
ARTIST_X, ARTIST_Y = 620, 195
DURATION_X, DURATION_Y = 1080, 315

TITLE_MAX_WIDTH = 420


def get_font(size):
    """Get font - tries multiple options"""
    font_paths = [
        f"assets/font.ttf",
        f"assets/font2.ttf", 
        f"assets/font3.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                pass
    return ImageFont.load_default()


def truncate_text(text, font, max_width):
    """Truncate text to fit width"""
    if not text:
        return ""
    
    # Check if full text fits
    try:
        bbox = font.getbbox(text)
        if bbox and bbox[2] <= max_width:
            return text
    except:
        pass
    
    # Truncate with ellipsis
    words = text.split()
    result = ""
    for word in words:
        test = result + " " + word if result else word
        try:
            bbox = font.getbbox(test + "...")
            if bbox and bbox[2] <= max_width:
                result = test
            else:
                return result + "..." if result else word[:15] + "..."
        except:
            if len(test) > 25:
                return result + "..." if result else word[:15] + "..."
            result = test
    return result


def create_rounded_mask(size, radius):
    """Create rounded rectangle mask"""
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, size[0], size[1]], radius=radius, fill=255)
    return mask


async def download_image(url):
    """Download image and return PIL Image"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    return Image.open(BytesIO(data)).convert("RGBA")
    except Exception as e:
        print(f"Download error: {e}")
    return None


def generate_thumbnail_sync(song_img, title, artist, duration, output_path):
    """Synchronous thumbnail generation"""
    try:
        # Check template exists
        if not os.path.exists(TEMPLATE_PATH):
            print(f"Template not found: {TEMPLATE_PATH}")
            return None
        
        # Load template
        template = Image.open(TEMPLATE_PATH).convert("RGBA")
        
        # Resize song image
        song_img = song_img.resize((IMG_SIZE, IMG_SIZE), Image.Resampling.LANCZOS)
        
        # Create rounded mask and paste
        mask = create_rounded_mask((IMG_SIZE, IMG_SIZE), IMG_RADIUS)
        template.paste(song_img, (IMG_X, IMG_Y), mask)
        
        # Draw text
        draw = ImageDraw.Draw(template)
        title_font = get_font(34)
        artist_font = get_font(26)
        duration_font = get_font(22)
        
        # Title (truncated)
        display_title = truncate_text(title, title_font, TITLE_MAX_WIDTH)
        draw.text((TITLE_X, TITLE_Y), display_title, font=title_font, fill=(255, 255, 255))
        
        # Artist
        draw.text((ARTIST_X, ARTIST_Y), artist, font=artist_font, fill=(200, 200, 200))
        
        # Duration
        draw.text((DURATION_X, DURATION_Y), f"-{duration}", font=duration_font, fill=(180, 180, 180))
        
        # Save
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        template.save(output_path, "PNG")
        
        return output_path
        
    except Exception as e:
        print(f"Generate error: {e}")
        return None


async def gen_thumb(song_data):
    """
    Generate thumbnail from song data
    
    song_data = {
        "title": "Song Name",
        "artist": "Artist Name", 
        "duration": "3:45",
        "thumb": "https://image-url.jpg"
    }
    
    Returns: path to generated thumbnail or None
    """
    try:
        # Create cache path
        cache_key = song_data.get("title", "unknown").replace(" ", "_")[:30]
        output_path = f"{CACHE_DIR}/thumb_{cache_key}.png"
        
        # Check cache
        if os.path.exists(output_path):
            return output_path
        
        # Download song image
        img_url = song_data.get("thumb") or song_data.get("image")
        if not img_url:
            return None
        
        song_img = await download_image(img_url)
        if not song_img:
            return None
        
        # Generate thumbnail
        result = generate_thumbnail_sync(
            song_img,
            song_data.get("title", "Unknown"),
            song_data.get("artist", "Unknown Artist"),
            song_data.get("duration", "0:00"),
            output_path
        )
        
        return result
        
    except Exception as e:
        print(f"gen_thumb error: {e}")
        return None


# Legacy function name for compatibility
async def get_thumb(videoid, query=None, use_jiosaavn=True, song_data=None):
    """
    Legacy compatibility function
    Returns YouTube thumbnail URL or STREAM_IMG_URL fallback
    """
    import config
    
    # If song_data provided, try template
    if song_data:
        result = await gen_thumb(song_data)
        if result:
            return result
    
    # Return YouTube thumbnail
    if videoid:
        return f"https://img.youtube.com/vi/{videoid}/maxresdefault.jpg"
    
    # Fallback
    return config.STREAM_IMG_URL
