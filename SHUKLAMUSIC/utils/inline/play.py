import math
from pyrogram.raw.types import (
    ReplyInlineMarkup,
    KeyboardButtonRow,
    KeyboardButtonUrl,
    KeyboardButtonCallback
)
from SHUKLAMUSIC.utils.formatters import time_to_seconds


# ==========================================
# TRACK MARKUP
# ==========================================
def track_markup(_, videoid, user_id, channel, fplay):
    return ReplyInlineMarkup(
        rows=[
            KeyboardButtonRow(
                buttons=[
                    KeyboardButtonCallback(
                        text=_["P_B_1"],
                        data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}".encode(),
                        style="primary"
                    ),
                    KeyboardButtonCallback(
                        text=_["P_B_2"],
                        data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}".encode(),
                        style="success"
                    )
                ]
            ),
            KeyboardButtonRow(
                buttons=[
                    KeyboardButtonCallback(
                        text=_["CLOSE_BUTTON"],
                        data=f"forceclose {videoid}|{user_id}".encode(),
                        style="danger"
                    )
                ]
            )
        ]
    )


# ==========================================
# STREAM MARKUP TIMER
# ==========================================
def stream_markup_timer(_, chat_id, played, dur):
    played_sec = time_to_seconds(played)
    duration_sec = time_to_seconds(dur)

    percentage = 0 if duration_sec == 0 else (played_sec / duration_sec) * 100
    umm = math.floor(percentage)

    if 0 < umm <= 10:
        bar = "▰▱▱▱▱▱▱▱▱▱"
    elif 10 < umm < 20:
        bar = "▰▰▱▱▱▱▱▱▱▱"
    elif 20 <= umm < 30:
        bar = "▰▰▰▱▱▱▱▱▱▱"
    elif 30 <= umm < 40:
        bar = "▰▰▰▰▱▱▱▱▱▱"
    elif 40 <= umm < 50:
        bar = "▰▰▰▰▰▱▱▱▱▱"
    elif 50 <= umm < 60:
        bar = "▰▰▰▰▰▰▱▱▱▱"
    elif 60 <= umm < 70:
        bar = "▰▰▰▰▰▰▰▱▱▱"
    elif 70 <= umm < 80:
        bar = "▰▰▰▰▰▰▰▰▱▱"
    elif 80 <= umm < 95:
        bar = "▰▰▰▰▰▰▰▰▰▱"
    else:
        bar = "▰▰▰▰▰▰▰▰▰▰"

    return ReplyInlineMarkup(
        rows=[
            KeyboardButtonRow(
                buttons=[
                    KeyboardButtonUrl(
                        text=" ˹ηєᴛᴡᴏʀᴋ˼ ",
                        url="https://t.me/thedrxnet",
                        style="success",
                        icon_custom_emoji_id=5204046146955153467
                    ),
                    KeyboardButtonUrl(
                        text=" ˹ϻʏ ʜᴏϻє˼ ",
                        url="https://t.me/drx_supportchat",
                        style="primary",
                        icon_custom_emoji_id=5424663180838182778
                    )
                ]
            ),
            KeyboardButtonRow(
                buttons=[
                    KeyboardButtonUrl(
                        text="˹ᴘʀιᴠᴧᴄʏ˼",
                        url="https://telegra.ph/Privacy-Policy-08-03-101",
                        style="primary",
                        icon_custom_emoji_id=5409029744693897259
                    ),
                    KeyboardButtonUrl(
                        text="˹ᴛιᴅᴧʟ ᴛᴜηєs˼♪",
                        url="http://t.me/TidalXMusicBot/tidaltunes",
                        style="success",
                        icon_custom_emoji_id=6141008793179261507
                    )
                ]
            ),
            KeyboardButtonRow(
                buttons=[
                    KeyboardButtonCallback(
                        text=_["CLOSE_BUTTON"],
                        data=b"close",
                        style="danger",
                        icon_custom_emoji_id=5224674827633175944
                    )
                ]
            )
        ]
    )


# ==========================================
# SIMPLE STREAM MARKUP
# ==========================================
def stream_markup(_, chat_id):
    return stream_markup_timer(_, chat_id, "0:00", "0:01")


# ==========================================
# PLAYLIST MARKUP
# ==========================================
def playlist_markup(_, videoid, user_id, ptype, channel, fplay):
    return track_markup(_, videoid, user_id, channel, fplay)


# ==========================================
# LIVESTREAM MARKUP
# ==========================================
def livestream_markup(_, videoid, user_id, mode, channel, fplay):
    return ReplyInlineMarkup(
        rows=[
            KeyboardButtonRow(
                buttons=[
                    KeyboardButtonCallback(
                        text=_["P_B_3"],
                        data=f"LiveStream {videoid}|{user_id}|{mode}|{channel}|{fplay}".encode(),
                        style="primary"
                    )
                ]
            ),
            KeyboardButtonRow(
                buttons=[
                    KeyboardButtonCallback(
                        text=_["CLOSE_BUTTON"],
                        data=f"forceclose {videoid}|{user_id}".encode(),
                        style="danger"
                    )
                ]
            )
        ]
    )


# ==========================================
# SLIDER MARKUP
# ==========================================
def slider_markup(_, videoid, user_id, query, query_type, channel, fplay):
    query = query[:20]

    return ReplyInlineMarkup(
        rows=[
            KeyboardButtonRow(
                buttons=[
                    KeyboardButtonCallback(
                        text=_["P_B_1"],
                        data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}".encode(),
                        style="primary"
                    ),
                    KeyboardButtonCallback(
                        text=_["P_B_2"],
                        data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}".encode(),
                        style="success"
                    )
                ]
            ),
            KeyboardButtonRow(
                buttons=[
                    KeyboardButtonCallback(
                        text="◁",
                        data=f"slider B|{query_type}|{query}|{user_id}|{channel}|{fplay}".encode()
                    ),
                    KeyboardButtonCallback(
                        text=_["CLOSE_BUTTON"],
                        data=f"forceclose {query}|{user_id}".encode(),
                        style="danger"
                    ),
                    KeyboardButtonCallback(
                        text="▷",
                        data=f"slider F|{query_type}|{query}|{user_id}|{channel}|{fplay}".encode()
                    )
                ]
            )
        ]
    )
