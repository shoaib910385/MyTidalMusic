# Thumbnail credits @hehe_staller
# Enhanced with JioSaavn API support and custom template
import traceback
import random
import logging
import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from py_yt import VideosSearch

logging.basicConfig(level=logging.INFO)

# JioSaavn API Base URL
JIOSAAVN_API = "https://jiosavan-lilac.vercel.app"


def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    newImage = image.resize((newWidth, newHeight))
    return newImage


def truncate(text):
    list = text.split(" ")
    text1 = ""
    text2 = ""    
    for i in list:
        if len(text1) + len(i) < 30:        
            text1 += " " + i
        elif len(text2) + len(i) < 30:       
            text2 += " " + i

    text1 = text1.strip()
    text2 = text2.strip()     
    return [text1, text2]


def random_color():
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))


def generate_gradient(width, height, start_color, end_color):
    base = Image.new('RGBA', (width, height), start_color)
    top = Image.new('RGBA', (width, height), end_color)
    mask = Image.new('L', (width, height))
    mask_data = []
    for y in range(height):
        mask_data.extend([int(60 * (y / height))] * width)
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base


def add_border(image, border_width, border_color):
    width, height = image.size
    new_width = width + 2 * border_width
    new_height = height + 2 * border_width
    new_image = Image.new("RGBA", (new_width, new_height), border_color)
    new_image.paste(image, (border_width, border_width))
    return new_image


def crop_center_circle(img, output_size, border, border_color, crop_scale=1.5):
    half_the_width = img.size[0] / 2
    half_the_height = img.size[1] / 2
    larger_size = int(output_size * crop_scale)
    img = img.crop(
        (
            half_the_width - larger_size/2,
            half_the_height - larger_size/2,
            half_the_width + larger_size/2,
            half_the_height + larger_size/2
        )
    )
    
    img = img.resize((output_size - 2*border, output_size - 2*border))
    
    final_img = Image.new("RGBA", (output_size, output_size), border_color)
    
    mask_main = Image.new("L", (output_size - 2*border, output_size - 2*border), 0)
    draw_main = ImageDraw.Draw(mask_main)
    draw_main.ellipse((0, 0, output_size - 2*border, output_size - 2*border), fill=255)
    
    final_img.paste(img, (border, border), mask_main)
    
    mask_border = Image.new("L", (output_size, output_size), 0)
    draw_border = ImageDraw.Draw(mask_border)
    draw_border.ellipse((0, 0, output_size, output_size), fill=255)
    
    result = Image.composite(final_img, Image.new("RGBA", final_img.size, (0, 0, 0, 0)), mask_border)
    
    return result


def draw_text_with_shadow(background, draw, position, text, font, fill, shadow_offset=(3, 3), shadow_blur=5):
    shadow = Image.new('RGBA', background.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    
    shadow_draw.text(position, text, font=font, fill="black")
    
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
    
    background.paste(shadow, shadow_offset, shadow)
    
    draw.text(position, text, font=font, fill=fill)


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
        logging.error(f"JioSaavn API Error: {e}")
        return None


async def generate_jiosaavn_thumbnail(song_data: dict, output_path: str):
    """
    Generate custom thumbnail using template for JioSaavn songs
    Template layout:
    - Left side: Song image (red area)
    - Top right: Song title up to 4 words (green area)
    - Middle right: Artist name (blue area)
    - Bottom right: Duration (purple area)
    """
    try:
        # Template path (user should place template.png in assets folder)
        template_path = "SHUKLAMUSIC/assets/template.png"
        
        # Check if template exists
        if not os.path.exists(template_path):
            logging.warning(f"Template not found at {template_path}, using fallback method")
            return None
        
        # Download song image
        song_img_path = None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(song_data["image"], timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        song_img_data = await resp.read()
                        song_img_path = f"cache/temp_song_img_{song_data['id']}.jpg"
                        os.makedirs("cache", exist_ok=True)
                        async with aiofiles.open(song_img_path, mode="wb") as f:
                            await f.write(song_img_data)
                    else:
                        return None
        except Exception as e:
            logging.error(f"Error downloading song image: {e}")
            return None
        
        # Open template and song image
        template = Image.open(template_path).convert("RGBA")
        song_img = Image.open(song_img_path).convert("RGBA")
        
        # Resize song image to fit in template (left side area ~400x400)
        song_img_size = (380, 380)
        song_img = song_img.resize(song_img_size, Image.Resampling.LANCZOS)
        
        # Create rounded corners mask for song image
        mask = Image.new("L", song_img_size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.rounded_rectangle([0, 0, song_img_size[0], song_img_size[1]], radius=30, fill=255)
        
        # Paste song image onto template (left side position)
        img_position = (60, 60)
        template.paste(song_img, img_position, mask)
        
        # Prepare text drawing
        draw = ImageDraw.Draw(template)
        
        # Load fonts - try Google Sans first, then fallbacks
        title_font = None
        artist_font = None
        duration_font = None
        
        font_paths = [
            ("SHUKLAMUSIC/assets/GoogleSans-Bold.ttf", 42),
            ("SHUKLAMUSIC/assets/GoogleSans-Regular.ttf", 32),
            ("SHUKLAMUSIC/assets/GoogleSans-Medium.ttf", 28),
        ]
        
        fallback_font_paths = [
            ("SHUKLAMUSIC/assets/font.ttf", 42),
            ("SHUKLAMUSIC/assets/font2.ttf", 32),
            ("SHUKLAMUSIC/assets/font3.ttf", 28),
        ]
        
        try:
            title_font = ImageFont.truetype(font_paths[0][0], font_paths[0][1])
            artist_font = ImageFont.truetype(font_paths[1][0], font_paths[1][1])
            duration_font = ImageFont.truetype(font_paths[2][0], font_paths[2][1])
        except:
            try:
                title_font = ImageFont.truetype(fallback_font_paths[0][0], fallback_font_paths[0][1])
                artist_font = ImageFont.truetype(fallback_font_paths[1][0], fallback_font_paths[1][1])
                duration_font = ImageFont.truetype(fallback_font_paths[2][0], fallback_font_paths[2][1])
            except:
                title_font = ImageFont.load_default()
                artist_font = ImageFont.load_default()
                duration_font = ImageFont.load_default()
        
        # Truncate title to 4 words max
        title_words = song_data["title"].split()[:4]
        display_title = " ".join(title_words)
        if len(song_data["title"].split()) > 4:
            display_title += "..."
        
        # Draw text with shadow for better visibility
        # Green area - Title (top right)
        title_position = (480, 120)
        draw_text_with_shadow(template, draw, title_position, display_title, title_font, (255, 255, 255))
        
        # Blue area - Artist (middle right)
        artist_position = (480, 190)
        draw_text_with_shadow(template, draw, artist_position, song_data["artist"], artist_font, (200, 200, 200))
        
        # Purple area - Duration (bottom right)
        duration_position = (1050, 350)
        draw.text(duration_position, song_data["duration_min"], font=duration_font, fill=(180, 180, 180))
        
        # Save thumbnail
        template.save(output_path, "PNG")
        
        # Cleanup temp file
        if song_img_path and os.path.exists(song_img_path):
            os.remove(song_img_path)
        
        logging.info(f"Generated JioSaavn thumbnail: {output_path}")
        return output_path
        
    except Exception as e:
        logging.error(f"JioSaavn thumbnail generation error: {e}")
        traceback.print_exc()
        return None


async def get_thumb(videoid: str, query: str = None, use_jiosaavn: bool = False):
    """
    Get thumbnail for a video/song
    
    Args:
        videoid: YouTube video ID or JioSaavn song ID
        query: Search query (optional, for JioSaavn search)
        use_jiosaavn: Whether to try JioSaavn API first
    
    Returns:
        Path to generated thumbnail or None
    """
    try:
        # Check if already cached
        cache_path = f"cache/{videoid}_v4.png"
        if os.path.isfile(cache_path):
            return cache_path
        
        # Try JioSaavn if requested
        if use_jiosaavn and query:
            jiosaavn_data = await search_jiosaavn_song(query)
            if jiosaavn_data:
                thumb_path = f"cache/jiosaavn_{jiosaavn_data['id']}_thumb.png"
                result = await generate_jiosaavn_thumbnail(jiosaavn_data, thumb_path)
                if result:
                    return result
                # If template generation fails, return the song image URL
                return jiosaavn_data["image"]
        
        # Fallback to YouTube thumbnail generation
        return await get_youtube_thumb(videoid)
        
    except Exception as e:
        logging.error(f"Error in get_thumb: {e}")
        return None


async def get_youtube_thumb(videoid: str):
    """
    Original YouTube thumbnail generation (fallback method)
    """
    try:
        if os.path.isfile(f"cache/{videoid}_v4.png"):
            return f"cache/{videoid}_v4.png"

        url = f"https://www.youtube.com/watch?v={videoid}"
        results = VideosSearch(url, limit=1)
        for result in (await results.next())["result"]:
            title = result.get("title")
            if title:
                title = re.sub("\W+", " ", title).title()
            else:
                title = "Unsupported Title"
            duration = result.get("duration")
            if not duration:
                duration = "Live"
            thumbnail_data = result.get("thumbnails")
            if thumbnail_data:
                thumbnail = thumbnail_data[0]["url"].split("?")[0]
            else:
                thumbnail = None
            views_data = result.get("viewCount")
            if views_data:
                views = views_data.get("short")
                if not views:
                    views = "Unknown Views"
            else:
                views = "Unknown Views"
            channel_data = result.get("channel")
            if channel_data:
                channel = channel_data.get("name")
                if not channel:
                    channel = "Unknown Channel"
            else:
                channel = "Unknown Channel"

        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                content = await resp.read()
                if resp.status == 200:
                    content_type = resp.headers.get('Content-Type')
                    if 'jpeg' in content_type or 'jpg' in content_type:
                        extension = 'jpg'
                    elif 'png' in content_type:
                        extension = 'png'
                    else:
                        logging.error(f"Unexpected content type: {content_type}")
                        return None

                    filepath = f"cache/thumb{videoid}.png"
                    os.makedirs("cache", exist_ok=True)
                    f = await aiofiles.open(filepath, mode="wb")
                    await f.write(content)
                    await f.close()
                    
        image_path = f"cache/thumb{videoid}.png"
        youtube = Image.open(image_path)
        image1 = changeImageSize(1280, 720, youtube)
        
        image2 = image1.convert("RGBA")
        background = image2.filter(filter=ImageFilter.BoxBlur(20))
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.6)

        start_gradient_color = random_color()
        end_gradient_color = random_color()
        gradient_image = generate_gradient(1280, 720, start_gradient_color, end_gradient_color)
        background = Image.blend(background, gradient_image, alpha=0.2)
        
        draw = ImageDraw.Draw(background)
        
        try:
            arial = ImageFont.truetype("SHUKLAMUSIC/assets/font2.ttf", 30)
            font = ImageFont.truetype("SHUKLAMUSIC/assets/font.ttf", 30)
            title_font = ImageFont.truetype("SHUKLAMUSIC/assets/font3.ttf", 45)
        except:
            arial = ImageFont.load_default()
            font = ImageFont.load_default()
            title_font = ImageFont.load_default()

        circle_thumbnail = crop_center_circle(youtube, 400, 20, start_gradient_color)
        circle_thumbnail = circle_thumbnail.resize((400, 400))
        circle_position = (120, 160)
        background.paste(circle_thumbnail, circle_position, circle_thumbnail)

        text_x_position = 565
        title1 = truncate(title)
        draw_text_with_shadow(background, draw, (text_x_position, 180), title1[0], title_font, (255, 255, 255))
        draw_text_with_shadow(background, draw, (text_x_position, 230), title1[1], title_font, (255, 255, 255))
        draw_text_with_shadow(background, draw, (text_x_position, 320), f"{channel}  |  {views[:23]}", arial, (255, 255, 255))

        line_length = 580  
        line_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

        if duration != "Live":
            color_line_percentage = random.uniform(0.15, 0.85)
            color_line_length = int(line_length * color_line_percentage)
            white_line_length = line_length - color_line_length

            start_point_color = (text_x_position, 380)
            end_point_color = (text_x_position + color_line_length, 380)
            draw.line([start_point_color, end_point_color], fill=line_color, width=9)
        
            start_point_white = (text_x_position + color_line_length, 380)
            end_point_white = (text_x_position + line_length, 380)
            draw.line([start_point_white, end_point_white], fill="white", width=8)
        
            circle_radius = 10 
            circle_position = (end_point_color[0], end_point_color[1])
            draw.ellipse([circle_position[0] - circle_radius, circle_position[1] - circle_radius,
                      circle_position[0] + circle_radius, circle_position[1] + circle_radius], fill=line_color)
        else:
            line_color = (255, 0, 0)
            start_point_color = (text_x_position, 380)
            end_point_color = (text_x_position + line_length, 380)
            draw.line([start_point_color, end_point_color], fill=line_color, width=9)
        
            circle_radius = 10 
            circle_position = (end_point_color[0], end_point_color[1])
            draw.ellipse([circle_position[0] - circle_radius, circle_position[1] - circle_radius,
                          circle_position[0] + circle_radius, circle_position[1] + circle_radius], fill=line_color)

        draw_text_with_shadow(background, draw, (text_x_position, 400), "00:00", arial, (255, 255, 255))
        draw_text_with_shadow(background, draw, (1080, 400), duration, arial, (255, 255, 255))
        
        # Play icons
        try:
            play_icons = Image.open("SHUKLAMUSIC/assets/assets/play_icons.png")
            play_icons = play_icons.resize((580, 62))
            background.paste(play_icons, (text_x_position, 450), play_icons)
        except:
            pass

        if os.path.exists(f"cache/thumb{videoid}.png"):
            os.remove(f"cache/thumb{videoid}.png")

        background_path = f"cache/{videoid}_v4.png"
        background.save(background_path)
        
        return background_path

    except Exception as e:
        logging.error(f"Error generating thumbnail for video {videoid}: {e}")
        traceback.print_exc()
        return None


async def get_jiosaavn_thumb(song_data: dict = None, query: str = None):
    """
    Get thumbnail for JioSaavn song
    
    Args:
        song_data: Pre-fetched JioSaavn song data (optional)
        query: Search query to fetch song data (optional)
    
    Returns:
        Path to generated thumbnail or image URL
    """
    try:
        # If no song data provided, search for it
        if not song_data and query:
            song_data = await search_jiosaavn_song(query)
        
        if not song_data:
            return None
        
        # Check if already cached
        cache_path = f"cache/jiosaavn_{song_data['id']}_thumb.png"
        if os.path.isfile(cache_path):
            return cache_path
        
        # Generate custom thumbnail
        result = await generate_jiosaavn_thumbnail(song_data, cache_path)
        if result:
            return result
        
        # Fallback to song image URL
        return song_data.get("image")
        
    except Exception as e:
        logging.error(f"Error getting JioSaavn thumbnail: {e}")
        return None
