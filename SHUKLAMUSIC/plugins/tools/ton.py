import aiohttp
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message
from SHUKLAMUSIC import app

@app.on_message(filters.command("ton"))
async def ton_price_command(client, message: Message):
    # Send a waiting message while fetching data
    msg = await message.reply_text("Fetching latest TON prices...")
    
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
        usd_price = round(ton_usd["prices"]["USD"], 2)
        usd_24h = ton_usd["diff_24h"]["USD"]
        usd_7d = ton_usd["diff_7d"]["USD"]
        usd_30d = ton_usd["diff_30d"]["USD"]

        # Parse INR stats
        ton_inr = inr_data["rates"]["TON"]
        inr_price = round(ton_inr["prices"]["INR"], 2)
        inr_24h = ton_inr["diff_24h"]["INR"]
        inr_7d = ton_inr["diff_7d"]["INR"]
        inr_30d = ton_inr["diff_30d"]["INR"]

        # Constructing the message with HTML Blockquotes
        text = (
            f"<b>TON PRICES:</b>\n"
            f"1 TON = ${usd_price}\n"
            f"1 TON = ₹{inr_price}\n\n"
            f"<blockquote>"
            f"<b>USD Changes:</b>\n"
            f"24h: {usd_24h}\n"
            f"7d: {usd_7d}\n"
            f"30d: {usd_30d}\n"
            f"</blockquote>"
            f"<blockquote expandable>"
            f"<b>INR Changes:</b>\n"
            f"24h: {inr_24h}\n"
            f"7d: {inr_7d}\n"
            f"30d: {inr_30d}\n"
            f"</blockquote>"
            f"<blockquote>"
            f"ʙʏ : @hehe_stalker"
            f"</blockquote>"
        )

        # Edit the waiting message with the final result
        await msg.edit_text(text, parse_mode=ParseMode.HTML)

    except Exception as e:
        # Fallback if API is down or something breaks
        await msg.edit_text("thoda hang ho gaya… couldn't fetch the TON price right now.")
