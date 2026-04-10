import aiohttp
import io
from datetime import datetime, timedelta
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message
from PIL import Image, ImageDraw, ImageFont
from SHUKLAMUSIC import app

@app.on_message(filters.command("ton", "priceton", "toncoin"))
async def ton_price_command(client, message: Message):
    # Send a waiting message while fetching data
    msg = await message.reply_text("Fetching latest TON prices and generating image...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Fetch USD Data
            async with session.get("https://tonapi.io/v2/rates?tokens=ton&currencies=usd") as resp_usd:
                usd_data = await resp_usd.json()
                
            # Fetch INR Data
            async with session.get("https://tonapi.io/v2/rates?tokens=ton&currencies=inr") as resp_inr:
                inr_data = await resp_inr.json()
        
        # Parse USD stats
        ton_usd = usd_data["rates"]["TON"]
        usd_price = round(ton_usd["prices"]["USD"], 4) # Rounded to 4 decimals for the image
        usd_24h = round(ton_usd["diff_24h"]["USD"], 2)
        usd_7d = round(ton_usd["diff_7d"]["USD"], 2)
        usd_30d = ton_usd["diff_30d"]["USD"]

        # Parse INR stats
        ton_inr = inr_data["rates"]["TON"]
        inr_price = round(ton_inr["prices"]["INR"], 2)
        inr_24h = ton_inr["diff_24h"]["INR"]
        inr_7d = ton_inr["diff_7d"]["INR"]
        inr_30d = ton_inr["diff_30d"]["INR"]

        # ==========================================
        # IMAGE GENERATION LOGIC
        # ==========================================
        
        # 1. Open your base template
        img = Image.open("base_template.png")
        draw = ImageDraw.Draw(img)

        # 2. Load Poppins Bold Font
        try:
            # Adjust sizes as needed based on your template's resolution
            font_price = ImageFont.truetype("Poppins-Bold.ttf", 90)
            font_change = ImageFont.truetype("Poppins-Bold.ttf", 40)
            font_dates = ImageFont.truetype("Poppins-Bold.ttf", 20)
        except IOError:
            await msg.edit_text("Error: 'Poppins-Bold.ttf' not found. Please add the font file.")
            return

        # 3. Format Text
        price_text = f"${usd_price:.4f}"
        daily_text = f"{'+' if usd_24h > 0 else ''}{usd_24h}%"
        weekly_text = f"{'+' if usd_7d > 0 else ''}{usd_7d}%"

        # Determine colors (Green for positive, Red for negative)
        color_green = (11, 209, 44)
        color_red = (255, 59, 48)
        daily_color = color_green if usd_24h >= 0 else color_red
        weekly_color = color_green if usd_7d >= 0 else color_red

        # 4. Draw Text onto Image
        # Note: You will likely need to slightly adjust the (X, Y) coordinates below 
        # to perfectly match the exact pixel dimensions of your base_template.png

        # Draw Price (Top Left)
        draw.text((100, 200), price_text, font=font_price, fill=(255, 255, 255))
        
        # Draw Changes (Centered in the purple pills using anchor="mm")
        draw.text((380, 450), daily_text, font=font_change, fill=daily_color, anchor="mm")
        draw.text((640, 450), weekly_text, font=font_change, fill=weekly_color, anchor="mm")

        # 5. Draw Dynamic Dates on Bottom Axis
        today = datetime.now()
        start_x = 110      # X-coordinate for the first date
        spacing_x = 120    # Distance between each date
        y_coord = 750      # Y-coordinate near the bottom
        
        for i in range(8):
            # Calculate past dates (7 days ago up to today)
            date_calc = today - timedelta(days=(7-i))
            date_str = date_calc.strftime("%b. %d")
            
            x_coord = start_x + (i * spacing_x)
            draw.text((x_coord, y_coord), date_str, font=font_dates, fill=(150, 150, 150), anchor="mm")

        # 6. Save image to memory buffer
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        img_byte_arr.name = "ton_stats.png"

        # ==========================================
        # CAPTION & SENDING LOGIC
        # ==========================================

        text = (
            f"<b>TON PRICES:</b>\n"
            f"1 TON = ${usd_price}\n"
            f"1 TON = ₹{inr_price}\n\n"
            
            f"<blockquote>"
            f"<b>USD Changes:</b>\n"
            f"24h: {usd_24h}%\n"
            f"7d: {usd_7d}%\n"
            f"30d: {usd_30d}%\n"
            f"</blockquote>"
            
            f"<blockquote expandable>"
            f"<b>INR Changes:</b>\n"
            f"24h: {inr_24h}%\n"
            f"7d: {inr_7d}%\n"
            f"30d: {inr_30d}%\n"
            f"</blockquote>"
            
            f"<blockquote>"
            f"ʙʏ : @hehe_stalker"
            f"</blockquote>"
        )

        # Send photo and delete the "fetching" message
        await message.reply_photo(photo=img_byte_arr, caption=text, parse_mode=ParseMode.HTML)
        await msg.delete()

    except Exception as e:
        # Fallback if API is down or something breaks
        await msg.edit_text(f"thoda hang ho gaya… couldn't fetch the TON price right now.\nError: {str(e)}")
