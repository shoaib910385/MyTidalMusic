import aiohttp
import io
import traceback
from datetime import datetime, timedelta
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message
from PIL import Image, ImageDraw, ImageFont
from SHUKLAMUSIC import app

@app.on_message(filters.command("ton"))
async def ton_price_command(client, message: Message):
    msg = await message.reply_text("⏳ Fetching latest TON prices and generating image...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://tonapi.io/v2/rates?tokens=ton&currencies=usd") as resp_usd:
                usd_data = await resp_usd.json()
                
            async with session.get("https://tonapi.io/v2/rates?tokens=ton&currencies=inr") as resp_inr:
                inr_data = await resp_inr.json()
        
        # Parse and convert to float before rounding
        ton_usd = usd_data["rates"]["TON"]
        usd_price = round(float(ton_usd["prices"]["USD"]), 4) 
        usd_24h = round(float(ton_usd["diff_24h"]["USD"]), 2)
        usd_7d = round(float(ton_usd["diff_7d"]["USD"]), 2)
        usd_30d = ton_usd["diff_30d"]["USD"]

        ton_inr = inr_data["rates"]["TON"]
        inr_price = round(float(ton_inr["prices"]["INR"]), 2)
        inr_24h = ton_inr["diff_24h"]["INR"]
        inr_7d = ton_inr["diff_7d"]["INR"]
        inr_30d = ton_inr["diff_30d"]["INR"]

        # --- IMAGE GENERATION ---
        try:
            img = Image.open("base_template.png")
        except Exception:
            await msg.edit_text("❌ **Failed to load base_template.png.** Make sure it's in the bot folder.")
            return

        draw = ImageDraw.Draw(img)

        try:
            # Adjust sizes to match your template resolution
            font_price = ImageFont.truetype("Poppins-Bold.ttf", 90)
            font_change = ImageFont.truetype("Poppins-Bold.ttf", 40)
            font_dates = ImageFont.truetype("Poppins-Bold.ttf", 20)
        except Exception:
            await msg.edit_text("❌ **Poppins-Bold.ttf missing.** Please add the font file to the bot folder.")
            return

        price_text = f"${usd_price:.4f}"
        daily_text = f"{'+' if usd_24h > 0 else ''}{usd_24h}%"
        weekly_text = f"{'+' if usd_7d > 0 else ''}{usd_7d}%"

        color_green = (11, 209, 44)
        color_red = (255, 59, 48)
        daily_color = color_green if usd_24h >= 0 else color_red
        weekly_color = color_green if usd_7d >= 0 else color_red

        # Coordinate adjustments might be needed based on your image size
        draw.text((100, 200), price_text, font=font_price, fill=(255, 255, 255))
        draw.text((380, 450), daily_text, font=font_change, fill=daily_color, anchor="mm")
        draw.text((640, 450), weekly_text, font=font_change, fill=weekly_color, anchor="mm")

        # Dynamic Dates
        today = datetime.now()
        start_x, spacing_x, y_coord = 110, 120, 750
        
        for i in range(8):
            date_calc = today - timedelta(days=(7-i))
            date_str = date_calc.strftime("%b. %d")
            x_coord = start_x + (i * spacing_x)
            draw.text((x_coord, y_coord), date_str, font=font_dates, fill=(150, 150, 150), anchor="mm")

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        img_byte_arr.name = "ton_stats.png"

        # --- CAPTION ---
        text = (
            f"<b><u>TON PRICES</u>:</b>\n"
            f"1 TON = ${usd_price}\n"
            f"1 TON = ₹{inr_price}\n\n"
            f"<blockquote><b><u>USD Changes:</u></b>\n24h: {usd_24h}%\n7d: {usd_7d}%\n30d: {usd_30d}%</blockquote>"
            f"<blockquote expandable><b><u>INR Changes:</u></b>\n24h: {inr_24h}%\n7d: {inr_7d}%\n30d: {inr_30d}%</blockquote>"
            f"<blockquote>ʙʏ : @hehe_stalker</blockquote>"
        )

        await message.reply_photo(photo=img_byte_arr, caption=text, parse_mode=ParseMode.HTML)
        await msg.delete()

    except Exception:
        error_traceback = traceback.format_exc()
        await msg.edit_text(f"❌ **Error occurred:**\n\n<pre>{error_traceback}</pre>", parse_mode=ParseMode.HTML)
