from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

import config

def start_panel(_, bot_username: str):
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(
            text=_["S_B_1"],
            url=f"https://t.me/{bot_username}?startgroup=true"
        ),
        InlineKeyboardButton(
            text=_["S_B_2"],
            url=config.SUPPORT_CHAT
        ),
    )

    kb.row(
        InlineKeyboardButton(
            text="˹ᴘσʟιᴄʏ˼",
            url="https://telegra.ph/Privacy-Policy-08-03-101",
            style="primary"
        ),
        InlineKeyboardButton(
            text="˹ᴛιᴅᴧʟ ᴛᴜηєs˼♪",
            url="http://t.me/TidalXMusicBot/tidaltunes"
        ),
    )

    return kb.as_markup()


def private_panel(_, bot_username: str):
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(
            text=_["S_B_3"],
            url=f"https://t.me/{bot_username}?startgroup=true"
        )
    )

    kb.row(
        InlineKeyboardButton(
            text="˹ᴘʀιᴠᴧᴄʏ ᴘσʟιᴄʏ˼",
            url="https://telegra.ph/Privacy-Policy-08-03-101"
        ),
        InlineKeyboardButton(
            text="˹ᴛιᴅᴧʟ ᴛᴜηєs˼♪",
            url="http://t.me/TidalXMusicBot/tidaltunes"
        ),
    )

    kb.row(
        InlineKeyboardButton(
            text=_["S_B_6"],
            url=config.SUPPORT_CHANNEL
        ),
        InlineKeyboardButton(
            text=_["S_B_2"],
            url=config.SUPPORT_CHAT
        ),
    )

    kb.row(
        InlineKeyboardButton(
            text=_["S_B_4"],
            callback_data="settings_back_helper"
        )
    )

    kb.row(
        InlineKeyboardButton(
            text=_["S_B_5"],
            url=f"https://t.me/{config.OWNER_USERNAME}"
        )
    )

    return kb.as_markup()
