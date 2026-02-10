import math
from pyrogram.types import InlineKeyboardButton
from SHUKLAMUSIC.utils.formatters import time_to_seconds


# --- Monkey Patch to allow style parameter ---
_original_init = InlineKeyboardButton.__init__

def _new_init(self, *args, style=None, **kwargs):
    _original_init(self, *args, **kwargs)
    self.style = style

InlineKeyboardButton.__init__ = _new_init


# ==========================================
# TRACK MARKUP
# ==========================================
def track_markup(_, videoid, user_id, channel, fplay):
    return [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
                style="primary"
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
                style="success"
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
                style="danger"
            )
        ],
    ]


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

    return [
        [
            InlineKeyboardButton(
                text=" ˹ηєᴛᴡᴏʀᴋ˼ ",
                url="https://t.me/thedrxnet",
                style="success"
            ),
            InlineKeyboardButton(
                text=" ˹ϻʏ ʜᴏϻє˼ ",
                url="https://t.me/drx_supportchat",
                style="primary"
            ),
        ],
        [
            InlineKeyboardButton(
                text="˹ᴘʀιᴠᴧᴄʏ˼",
                url="https://telegra.ph/Privacy-Policy-08-03-101",
                style="primary"
            ),
            InlineKeyboardButton(
                text="˹ᴛιᴅᴧʟ ᴛᴜηєs˼♪",
                url="http://t.me/TidalXMusicBot/tidaltunes",
                style="success"
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data="close",
                style="danger"
            )
        ],
    ]


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
    return [
        [
            InlineKeyboardButton(
                text=_["P_B_3"],
                callback_data=f"LiveStream {videoid}|{user_id}|{mode}|{channel}|{fplay}",
                style="primary"
            )
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
                style="danger"
            )
        ],
    ]


# ==========================================
# SLIDER MARKUP
# ==========================================
def slider_markup(_, videoid, user_id, query, query_type, channel, fplay):
    query = query[:20]

    return [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
                style="primary"
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
                style="success"
            ),
        ],
        [
            InlineKeyboardButton(
                text="◁",
                callback_data=f"slider B|{query_type}|{query}|{user_id}|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {query}|{user_id}",
                style="danger"
            ),
            InlineKeyboardButton(
                text="▷",
                callback_data=f"slider F|{query_type}|{query}|{user_id}|{channel}|{fplay}",
            ),
        ],
    ]
