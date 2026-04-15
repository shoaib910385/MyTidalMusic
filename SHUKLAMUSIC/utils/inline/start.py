from pyrogram.types import InlineKeyboardButton

import config
from pyrogram.enums import ButtonStyle
from SHUKLAMUSIC import app

def start_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_1"], url=f"https://t.me/{app.username}?startgroup=true", style=ButtonStyle.PRIMARY, icon_custom_emoji_id=5204046146955153467
            ),
            InlineKeyboardButton(text=_["S_B_2"], url=config.SUPPORT_CHAT),
        ],
        [
            InlineKeyboardButton(
                "˹ᴘσʟιᴄʏ˼",
                url="https://telegra.ph/Privacy-Policy-08-03-101",
                icon_custom_emoji_id=5409025823388741707,
                style=ButtonStyle.PRIMARY
            ),
            InlineKeyboardButton(
                "˹ᴛιᴅᴧʟ ᴛᴜηєs˼♪",
                url="http://t.me/TidalXMusicBot/tidaltunes",
                icon_custom_emoji_id=5409194306365829029,
                style=ButtonStyle.PRIMARY
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
                style=ButtonStyle.PRIMARY,
                icon_custom_emoji_id=5204046146955153467
            )
        ],
        
        [
            InlineKeyboardButton(
                "˹ᴘʀιᴠᴧᴄʏ ᴘσʟιᴄʏ˼",
                url="https://telegra.ph/Privacy-Policy-08-03-101",
                icon_custom_emoji_id=5409025823388741707,
                style=ButtonStyle.PRIMARY
            ),
            InlineKeyboardButton(
                "˹ᴛιᴅᴧʟ ᴛᴜηєs˼♪",
                url="http://t.me/TidalXMusicBot/tidaltunes",
                icon_custom_emoji_id=5409194306365829029,
                style=ButtonStyle.PRIMARY
            ),
        ],
        [
        
            InlineKeyboardButton(
                text=_["S_B_6"],
                url=config.SUPPORT_CHANNEL
            ),
            InlineKeyboardButton(
                text=_["S_B_2"],
                url=config.SUPPORT_CHAT
            ),
        ],
        [
    
            InlineKeyboardButton(
                text=_["S_B_4"],
                callback_data="settings_back_helper"
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["S_B_5"],
                url=f"https://t.me/{config.OWNER_USERNAME}",
                style=ButtonStyle.DANGER,
                icon_custom_emoji_id=5204046146955153467
            ),
        ],
    ]
    return buttons
    
    
