from pyrogram.types import InlineKeyboardButton

import config
from SHUKLAMUSIC import app

def start_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_1"], url=f"https://t.me/{app.username}?startgroup=true"
            ),
            InlineKeyboardButton(text=_["S_B_2"], url=config.SUPPORT_CHAT),
        ],
        [
            InlineKeyboardButton(
                "˹ᴘσʟιᴄʏ˼",
                url="https://telegra.ph/Privacy-Policy-08-03-101"
            ),
            InlineKeyboardButton(
                "˹ᴛιᴅᴧʟ ᴛᴜηєs˼♪",
                url="http://t.me/TidalXMusicBot/tidaltunes"
            ),
        ],
        
    ]
    return buttons


def private_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_3"],
                url=f"https://t.me/{app.username}?startgroup=true",
            )
        ],
        
        [
            InlineKeyboardButton(
                "˹ᴘʀιᴠᴧᴄʏ ᴘσʟιᴄʏ˼",
                url="https://telegra.ph/Privacy-Policy-08-03-101"
            ),
            InlineKeyboardButton(
                "˹ᴛιᴅᴧʟ ᴛᴜηєs˼♪",
                url="http://t.me/TidalXMusicBot/tidaltunes"
            ),
        ],
        
            InlineKeyboardButton(
                text=_["S_B_6"],
                url=config.SUPPORT_CHANNEL
            ),
            InlineKeyboardButton(
                text=_["S_B_2"],
                url=config.SUPPORT_CHAT
            ),
        ],
    
            InlineKeyboardButton(
                text=_["S_B_4"],
                callback_data="settings_back_helper"
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["S_B_5"],
                url=f"https://t.me/{config.OWNER_USERNAME}"
            ),
        ],
    ]
    return buttons
    
    
