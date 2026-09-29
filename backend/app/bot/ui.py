from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram.exceptions import TelegramBadRequest
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
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
_PROMPT_MESSAGE_ID = "_prompt_message_id"
_IGNORED_EDIT_ERRORS = (
    "message is not modified",
    "message can't be edited",
    "message to edit not found",
)


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
        one_time_keyboard=True,
        input_field_placeholder="Bo'limni tanlang",
    )


def cancel_keyboard():
    return inline([])


async def safe_edit_text(message: Message, text: str, reply_markup=None):
    try:
        return await message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as exc:
        error = str(exc).lower()
        if "message is not modified" in error:
            return message
        if any(reason in error for reason in _IGNORED_EDIT_ERRORS[1:]):
            return await message.answer(text, reply_markup=reply_markup)
        raise


async def safe_clear_keyboard(message: Message | None):
    if not message:
        return
    try:
        await message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest as exc:
        if not any(reason in str(exc).lower() for reason in _IGNORED_EDIT_ERRORS):
            raise


async def remember_prompt(state: FSMContext, message: Message):
    await state.update_data(**{_PROMPT_MESSAGE_ID: message.message_id})


async def answer_prompt(message: Message, state: FSMContext, text: str, reply_markup):
    prompt = await message.answer(text, reply_markup=reply_markup)
    await remember_prompt(state, prompt)
    return prompt


async def edit_prompt(message: Message, state: FSMContext, text: str, reply_markup):
    prompt = await safe_edit_text(message, text, reply_markup=reply_markup)
    await remember_prompt(state, prompt)


async def clear_prompt(message: Message, state: FSMContext):
    data = await state.get_data()
    prompt_id = data.get(_PROMPT_MESSAGE_ID)
    if not prompt_id:
        return
    try:
        await message.bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=prompt_id,
            reply_markup=None,
        )
    except TelegramBadRequest as exc:
        if not any(reason in str(exc).lower() for reason in _IGNORED_EDIT_ERRORS):
            raise
    await state.update_data(**{_PROMPT_MESSAGE_ID: None})


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
