from SHUKLAMUSIC import app
from pyrogram import filters
from pyrogram.types import Message
import aiohttp


@app.on_message(filters.command("ton"))
async def ton_price(_, message: Message):
    """
    /ton - Get current TON coin price in USD and INR with change stats
    """
    
    # API endpoints
    usd_api = "https://tonapi.io/v2/rates?tokens=ton&currencies=usd"
    inr_api = "https://tonapi.io/v2/rates?tokens=ton&currencies=inr"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Fetch both APIs concurrently
            async with session.get(usd_api) as usd_resp, \
                       session.get(inr_api) as inr_resp:
                
                if usd_resp.status != 200 or inr_resp.status != 200:
                    return await message.reply_text("⚠️ API error, try again later.")
                
                usd_data = await usd_resp.json()
                inr_data = await inr_resp.json()
        
        # Extract USD data
        usd_price = usd_data["rates"]["TON"]["prices"]["USD"]
        usd_24h = usd_data["rates"]["TON"]["diff_24h"]["USD"]
        usd_7d = usd_data["rates"]["TON"]["diff_7d"]["USD"]
        usd_30d = usd_data["rates"]["TON"]["diff_30d"]["USD"]
        
        # Extract INR data
        inr_price = inr_data["rates"]["TON"]["prices"]["INR"]
        inr_24h = inr_data["rates"]["TON"]["diff_24h"]["INR"]
        inr_7d = inr_data["rates"]["TON"]["diff_7d"]["INR"]
        inr_30d = inr_data["rates"]["TON"]["diff_30d"]["INR"]
        
        # Format prices (round to 4 decimal places for clean look)
        usd_formatted = f"{usd_price:.4f}"
        inr_formatted = f"{inr_price:.4f}"
        
        # Build response with blockquotes (using HTML parsing)
        text = (
            f"<b>💎 TON PRICES</b>\n\n"
            f"1 TON = <code>${usd_formatted}</code>\n"
            f"1 TON = <code>₹{inr_formatted}</code>\n\n"
            f"<b>📊 USD Changes</b>\n"
            f"<blockquote expandable>24h: {usd_24h}\n"
            f"7d: {usd_7d}\n"
            f"30d: {usd_30d}</blockquote>\n"
            f"<b>📊 INR Changes</b>\n"
            f"<blockquote expandable>24h: {inr_24h}\n"
            f"7d: {inr_7d}\n"
            f"30d: {inr_30d}</blockquote>\n• ʙʏ : @hehe_stalker"
        )
        
        await message.reply_text(text, parse_mode="HTML")
        
    except Exception as e:
        await message.reply_text("❌ Failed to fetch TON price. Try again later.")
