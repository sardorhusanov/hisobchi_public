from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.config.settings import get_settings

MAIN = [
    "🕒 Davomat",
    "👷 Ishchilar",
    "🤝 Hamkor",
    "💵 Avans",
    "🧮 Oylik",
    "📁 Loyihalar",
    "💰 Moliya",
    "📊 Hisobot",
    "⚙️ Sozlamalar",
]
HOME = "🏠 Bosh menyu"
BACK = "⬅️ Orqaga"


class Action(CallbackData, prefix="a"):
    kind: str
    id: str = ""
    value: str = ""


def button(text: str, kind: str, id="", value=""):
    return InlineKeyboardButton(
        text=text, callback_data=Action(kind=kind, id=str(id), value=str(value)).pack()
    )


def inline(rows):
    return InlineKeyboardMarkup(inline_keyboard=[*rows, [button(HOME, "home")]])


def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t) for t in MAIN[i : i + 2]] for i in range(0, len(MAIN), 2)
        ],
        resize_keyboard=True,
    )


def cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BACK), KeyboardButton(text=HOME)]], resize_keyboard=True
    )


def today():
    return datetime.now(ZoneInfo(get_settings().timezone)).date()


MONTHS = [
    "Yanvar",
    "Fevral",
    "Mart",
    "Aprel",
    "May",
    "Iyun",
    "Iyul",
    "Avgust",
    "Sentabr",
    "Oktabr",
    "Noyabr",
    "Dekabr",
]


def month_label(day):
    return f"{MONTHS[day.month - 1]} {day.year}"
