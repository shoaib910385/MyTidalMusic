import aiohttp
import io
import os
import traceback
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message
from PIL import Image, ImageDraw, ImageFont
from SHUKLAMUSIC import app

# Automatically detect the folder where the script is located
current_dir = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(current_dir, "balance_base.png")
FONT_PATH = os.path.join(current_dir, "Poppins-Bold.ttf")

@app.on_message(filters.command("balance"))
async def bal_command(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("❌ Please provide a username or TON address.\nExample: `/balance @subdict`")

    # --- INPUT PARSING LOGIC ---
    raw_input = message.command[1].lower()
    
    # Clean up the input to get the raw username/address
    target = raw_input.replace("https://", "").replace("http://", "").replace("t.me/", "").replace("@", "")
    
    # Remove trailing slashes if any
    target = target.strip("/")

    # Determine display name and API target
    if len(target) > 20 and not target.endswith(".t.me"):
        # It's likely a raw TON wallet address
        api_target = target
        display_name = f"{target[:6]}...{target[-4:]}"
    else:
        # It's a username/domain
        # Ensure we don't double up on .t.me if user provided username.t.me
        clean_username = target.replace(".t.me", "")
        api_target = f"{clean_username}.t.me"
        display_name = f"@{clean_username}"

    msg = await message.reply_text(f"⏳ Fetching balance for {display_name}...")

    try:
        async with aiohttp.ClientSession() as session:
            # Fetch Account Info
            async with session.get(f"https://tonapi.io/v2/accounts/{api_target}") as resp_acc:
                acc_data = await resp_acc.json()
                
            if "error" in acc_data:
                err_msg = acc_data.get("error", "")
                if "not resolved" in err_msg or "entity not found" in err_msg:
                    return await msg.edit_text("❌ No account found. Ensure the username has a TON DNS or use a wallet address.")
                else:
                    return await msg.edit_text(f"❌ **API Error:** {err_msg}")

            # Fetch Rates
            async with session.get("https://tonapi.io/v2/rates?tokens=ton&currencies=usd,inr") as resp_rates:
                rates_data = await resp_rates.json()

        # Parse Data
        nano_balance = int(acc_data.get("balance", 0))
        ton_balance = nano_balance / 1e9

        usd_rate = float(rates_data["rates"]["TON"]["prices"]["USD"])
        inr_rate = float(rates_data["rates"]["TON"]["prices"]["INR"])

        usd_value = ton_balance * usd_rate
        inr_value = ton_balance * inr_rate

        # Formatting values
        ton_str = f"{ton_balance:,.2f}"
        usd_str = f"${usd_value:,.2f}"
        inr_str = f"₹{inr_value:,.2f}"

        # --- IMAGE GENERATION ---
        if not os.path.exists(TEMPLATE_PATH):
            return await msg.edit_text("❌ **Template image missing!**")

        img = Image.open(TEMPLATE_PATH)
        draw = ImageDraw.Draw(img)

        try:
            font_title = ImageFont.truetype(FONT_PATH, 190)
            font_values = ImageFont.truetype(FONT_PATH, 170)
        except:
            return await msg.edit_text("❌ **Font file error!**")

        WHITE = (255, 255, 255)
        DARK_GREY = (90, 90, 90)
        img_width, _ = img.size

        # Draw Header
        draw.text((img_width / 2, 170), f"{display_name}'s Balance", font=font_title, fill=WHITE, anchor="mt")

        # Draw Values (Right Aligned)
        right_align_x = img_width - 376
        draw.text((right_align_x, 800), ton_str, font=font_values, fill=DARK_GREY, anchor="rm")
        draw.text((right_align_x, 1190), usd_str, font=font_values, fill=DARK_GREY, anchor="rm")
        draw.text((right_align_x, 1600), inr_str, font=font_values, fill=DARK_GREY, anchor="rm")

        # Save and Send
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        caption = (
            f"<b>{display_name} 's balance</b>\n"
            f"<blockquote expandable><b>TON:</b> {ton_str}\n"
            f"<b>USD:</b> {usd_str}\n"
            f"<b>INR:</b> {inr_str}</blockquote>\n"
            f"<blockquote>• ʙʏ : @hehe_stalker</blockquote>"
        )

        await message.reply_photo(photo=img_byte_arr, has_spoiler=True, caption=caption, parse_mode=ParseMode.HTML)
        await msg.delete()

    except Exception:
        await msg.edit_text(f"❌ **Critical Error:**\n\n<pre>{traceback.format_exc()}</pre>", parse_mode=ParseMode.HTML)
