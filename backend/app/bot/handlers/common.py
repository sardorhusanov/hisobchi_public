from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

from app.bot.ui import BACK, HOME, MAIN, Action, button, inline, main_keyboard
from app.config.settings import get_settings
from app.models import Role, Status
from app.services.core import PeopleService

router = Router()


async def home(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bosh menyu", reply_markup=main_keyboard())
    if get_settings().mini_app_url:
        await message.answer(
            "Hisobotlar va boshqaruv",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📱 Ilovani ochish",
                            web_app=WebAppInfo(url=get_settings().mini_app_url),
                        )
                    ]
                ]
            ),
        )


@router.message(CommandStart())
@router.message(F.text.in_({HOME, BACK}))
async def start(message: Message, state: FSMContext):
    await home(message, state)


@router.callback_query(Action.filter(F.kind == "home"))
async def home_callback(query: CallbackQuery, state: FSMContext):
    await home(query.message, state)
    await query.answer()


@router.message(F.text.in_(MAIN))
async def menu(message: Message, state: FSMContext, repo):
    await state.clear()
    text = message.text
    rows = []
    if text == MAIN[0]:
        rows = [
            [button("Bugungi davomat", "today"), button("Boshqa sana", "date")],
            [button("Oylik davomat", "report", value="attendance")],
        ]
    elif text in (MAIN[1], MAIN[2]):
        role = Role.WORKER if text == MAIN[1] else Role.PARTNER
        rows = [
            [
                button(
                    "Ishchi qo'shish" if role == Role.WORKER else "Hamkor qo'shish",
                    "addperson",
                    value=role.value,
                )
            ]
        ]
        rows += [[button(p.name, "person", p.id.hex)] for p in await PeopleService(repo).list(role)]
    elif text == MAIN[3]:
        rows = [
            [button(p.name, "worker", p.id.hex)]
            for p in await PeopleService(repo).list(Role.WORKER, active=False)
        ]
    elif text == MAIN[4]:
        rows = [[button("Oylik hisoboti", "report", value="salary")]]
        rows += [
            [button(p.name, "salary", p.id.hex)]
            for p in await PeopleService(repo).list(Role.WORKER, active=False)
        ]
    elif text == MAIN[5]:
        rows = [
            [button("Loyiha qo'shish", "addproject")],
            [button("Faol loyihalar", "projects", value=Status.ACTIVE.value)],
            [button("Tugallangan loyihalar", "projects", value=Status.COMPLETED.value)],
        ]
    elif text == MAIN[6]:
        rows = [
            [button("Umumiy xarajat", "expense")],
            [button("Pul tushumi", "incomechoose")],
            [button("Oylik moliya", "report", value="finance")],
        ]
    elif text == MAIN[7]:
        rows = [
            [button(label, "report", value=kind)]
            for label, kind in [
                ("Oylik", "salary"),
                ("Davomat", "attendance"),
                ("Avanslar", "advances"),
                ("Moliya", "finance"),
            ]
        ]
        rows.append([button("Loyihalar", "projects", value="ACTIVE")])
    else:
        owner = (await PeopleService(repo).list(Role.OWNER))[0]
        text = f"Sozlamalar\nIsmingiz: {owner.name}"
        rows = [[button("Ismni o'zgartirish", "rename", owner.id.hex)]]
    # Chunk long menus to respect Telegram keyboard limits.
    if not rows:
        text += "\nHozircha ma'lumot yo'q."
    for offset in range(0, max(len(rows), 1), 40):
        await message.answer(text, reply_markup=inline(rows[offset : offset + 40]))
