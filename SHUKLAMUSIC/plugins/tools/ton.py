from SHUKLAMUSIC import app
from pyrogram import filters
from pyrogram.types import Message
import aiohttp
import asyncio


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
            # Fetch both APIs concurrently with timeout
            try:
                async with session.get(usd_api, timeout=aiohttp.ClientTimeout(total=10)) as usd_resp, \
                           session.get(inr_api, timeout=aiohttp.ClientTimeout(total=10)) as inr_resp:
                    
                    if usd_resp.status != 200 or inr_resp.status != 200:
                        return await message.reply_text("⚠️ API error (non-200 status), try again later.")
                    
                    usd_data = await usd_resp.json()
                    inr_data = await inr_resp.json()
                    
            except asyncio.TimeoutError:
                return await message.reply_text("⏱️ API timeout, try again later.")
        
        # Extract USD data - handle both "TON" and "ton" keys
        usd_rates = usd_data.get("rates", {})
        ton_usd = usd_rates.get("TON") or usd_rates.get("ton", {})
        
        usd_price = ton_usd.get("prices", {}).get("USD") or ton_usd.get("prices", {}).get("usd", 0)
        usd_24h = ton_usd.get("diff_24h", {}).get("USD") or ton_usd.get("diff_24h", {}).get("usd", "N/A")
        usd_7d = ton_usd.get("diff_7d", {}).get("USD") or ton_usd.get("diff_7d", {}).get("usd", "N/A")
        usd_30d = ton_usd.get("diff_30d", {}).get("USD") or ton_usd.get("diff_30d", {}).get("usd", "N/A")
        
        # Extract INR data
        inr_rates = inr_data.get("rates", {})
        ton_inr = inr_rates.get("TON") or inr_rates.get("ton", {})
        
        inr_price = ton_inr.get("prices", {}).get("INR") or ton_inr.get("prices", {}).get("inr", 0)
        inr_24h = ton_inr.get("diff_24h", {}).get("INR") or ton_inr.get("diff_24h", {}).get("inr", "N/A")
        inr_7d = ton_inr.get("diff_7d", {}).get("INR") or ton_inr.get("diff_7d", {}).get("inr", "N/A")
        inr_30d = ton_inr.get("diff_30d", {}).get("INR") or ton_inr.get("diff_30d", {}).get("inr", "N/A")
        
        # Check if we got valid prices
        if not usd_price or not inr_price:
            return await message.reply_text("❌ Could not parse price data from API.")
        
        # Format prices (round to 4 decimal places for clean look)
        usd_formatted = f"{float(usd_price):.4f}"
        inr_formatted = f"{float(inr_price):.4f}"
        
        # Build response with blockquotes (using HTML parsing)
        text = (
            f"<b>💎 TON PRICES</b>\n\n"
            f"1 TON = <code>${usd_formatted}</code>\n"
            f"1 TON = <code>₹{inr_formatted}</code>\n\n"
            f"<b>📊 USD Changes</b>\n"
            f"<blockquote expandable>"
            f"24h: {usd_24h}\n"
            f"7d: {usd_7d}\n"
            f"30d: {usd_30d}"
            f"</blockquote>\n\n"
            f"<b>📊 INR Changes</b>\n"
            f"<blockquote expandable>"
            f"24h: {inr_24h}\n"
            f"7d: {inr_7d}\n"
            f"30d: {inr_30d}"
            f"</blockquote>"
        )
        
        await message.reply_text(text, parse_mode="HTML")
        
    except aiohttp.ClientError as e:
        await message.reply_text(f"❌ Network error: {str(e)[:50]}")
    except KeyError as e:
        await message.reply_text(f"❌ Data parsing error: missing key {str(e)}")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)[:50]}")
