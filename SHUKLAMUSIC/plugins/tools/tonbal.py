import aiohttp
import io
import os
import traceback
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message
from PIL import Image, ImageDraw, ImageFont
from SHUKLAMUSIC import app

# Automatically detect the folder where tonbal.py is located
current_dir = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(current_dir, "balance_base.png")
FONT_PATH = os.path.join(current_dir, "Poppins-Bold.ttf")

@app.on_message(filters.command("bal"))
async def bal_command(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("❌ Please provide a username or TON address.\nExample: `/bal @subdict`")

    target = message.command[1]
    
    # Format target for the API and display name
    if target.startswith("@"):
        username = target.replace("@", "")
        api_target = f"{username}.t.me"
        display_name = target
    else:
        api_target = target
        # Shorten display name if it's a long address to prevent overlapping in the image
        display_name = f"{target[:6]}...{target[-4:]}" if len(target) > 20 else target

    msg = await message.reply_text(f"⏳ Fetching balance for {display_name}...")

    try:
        async with aiohttp.ClientSession() as session:
            # Fetch Account Info
            async with session.get(f"https://tonapi.io/v2/accounts/{api_target}") as resp_acc:
                acc_data = await resp_acc.json()
                
            # Error handling for missing domains / invalid addresses
            if "error" in acc_data:
                err_msg = acc_data.get("error", "")
                if "not resolved: can't unmarshal null" in err_msg or "entity not found" in err_msg:
                    return await msg.edit_text("❌ No domain found with this user, try with a TON address.")
                else:
                    return await msg.edit_text(f"❌ **API Error:** {err_msg}")

            # Fetch Rates
            async with session.get("https://tonapi.io/v2/rates?tokens=ton&currencies=usd") as resp_usd:
                usd_data = await resp_usd.json()
            async with session.get("https://tonapi.io/v2/rates?tokens=ton&currencies=inr") as resp_inr:
                inr_data = await resp_inr.json()

        # Parse Data & Math Conversions
        # 1 TON = 1,000,000,000 nanoTON
        nano_balance = int(acc_data.get("balance", 0))
        ton_balance = nano_balance / 1e9

        usd_rate = float(usd_data["rates"]["TON"]["prices"]["USD"])
        inr_rate = float(inr_data["rates"]["TON"]["prices"]["INR"])

        usd_value = ton_balance * usd_rate
        inr_value = ton_balance * inr_rate

        # Formatting values for image and text
        ton_str = f"{ton_balance:.2f}" if ton_balance > 0 else "0.00"
        usd_str = f"${usd_value:.2f}"
        inr_str = f"₹{inr_value:.2f}"

        # --- IMAGE GENERATION ---
        if not os.path.exists(TEMPLATE_PATH):
            return await msg.edit_text(f"❌ **Template not found!**\nPath checked: `{TEMPLATE_PATH}`\nMake sure 'balance_base.png' is in your folder.")

        try:
            img = Image.open(TEMPLATE_PATH)
        except Exception as e:
            return await msg.edit_text(f"❌ **Error opening image:** {str(e)}")

        draw = ImageDraw.Draw(img)

        if not os.path.exists(FONT_PATH):
            return await msg.edit_text(f"❌ **Font not found!**\nPath checked: `{FONT_PATH}`")

        try:
            # Adjust sizes based on your exact image resolution if necessary
            font_title = ImageFont.truetype(FONT_PATH, 190)
            font_values = ImageFont.truetype(FONT_PATH, 170)
        except Exception as e:
            return await msg.edit_text(f"❌ **Error loading font:** {str(e)}")

        # Colors
        WHITE = (255, 255, 255)
        DARK_GREY = (90, 90, 90) # Dim black/dark grey as requested

        # Image Dimensions for center calculations
        img_width, img_height = img.size

        # Draw Top Middle Title text
        title_text = f"{display_name}'s Balance"
        draw.text((img_width / 2, 170), title_text, font=font_title, fill=WHITE, anchor="mt")

        # Draw Right-Aligned Values (TON, USD, INR)
        # Note: You might need to tweak the Y coordinates (320, 520, 720) depending on your actual template's layout.
        right_align_x = img_width - 376
        
        # TON Value
        draw.text((right_align_x, 800), ton_str, font=font_values, fill=DARK_GREY, anchor="rm")
        # USD Value
        draw.text((right_align_x, 1190), usd_str, font=font_values, fill=DARK_GREY, anchor="rm")
        # INR Value
        draw.text((right_align_x, 1600), inr_str, font=font_values, fill=DARK_GREY, anchor="rm")

        # Save to memory
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        img_byte_arr.name = f"{display_name}_balance.png"
        
        # --- CAPTION GENERATION ---
        text = (
            f"<b>{display_name} 's balance</b>\n"
            f"<blockquote expandable><b>TON:</b> {ton_str}\n"
            f"<b>USD:</b> {usd_str}\n"
            f"<b>INR:</b> {inr_str}</blockquote>\n"
            f"<blockquote>• ʙʏ : @hehe_stalker</blockquote>"
        )

        await message.reply_photo(photo=img_byte_arr, caption=text, parse_mode=ParseMode.HTML)
        await msg.delete()

    except Exception:
        error_traceback = traceback.format_exc()
        await msg.edit_text(f"❌ **Critical Error:**\n\n<pre>{error_traceback}</pre>", parse_mode=ParseMode.HTML)
