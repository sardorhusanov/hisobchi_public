from datetime import date
from decimal import Decimal

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.bot.ui import Action, button, cancel_keyboard, inline, today
from app.services.core import AttendanceService, PeopleService
from app.services.values import parse_date

router = Router()


class AttendanceInput(StatesGroup):
    day = State()


async def show_day(message, repo, day, page=0, edit=False):
    people = await PeopleService(repo).list()
    values = {a.person_id: a.value for a in await AttendanceService(repo).day(day)}
    pages = max(1, (len(people) + 7) // 8)
    page = min(max(page, 0), pages - 1)
    rows = []
    for person in people[page * 8 : page * 8 + 8]:
        value = values.get(person.id)
        rows.append([button(f"{person.name}: {value if value else '—'}", "noop")])
        rows.append(
            [
                button(
                    ("✓ " if value == v else "") + label,
                    "att",
                    person.id.hex,
                    f"{day:%Y%m%d}{code}",
                )
                for label, v, code in [
                    ("1 kun", Decimal(1), "1"),
                    ("0.5 kun", Decimal(".5"), "5"),
                    ("—", None, "0"),
                ]
            ]
        )
    rows.append([button("Hammasi 1 kun", "all", value=f"{day:%Y%m%d}")])
    rows.append(
        [
            button("‹", "attpage", str(page - 1), f"{day:%Y%m%d}"),
            button(f"{page + 1}/{pages}", "noop"),
            button("›", "attpage", str(page + 1), f"{day:%Y%m%d}"),
        ]
    )
    text = f"{day:%d.%m.%Y} — Davomat"
    if edit:
        try:
            await message.edit_text(text, reply_markup=inline(rows))
        except TelegramBadRequest as exc:
            if "message is not modified" not in str(exc):
                raise
    else:
        await message.answer(text, reply_markup=inline(rows))


@router.callback_query(
    Action.filter(F.kind.in_({"today", "date", "att", "all", "attpage", "noop"}))
)
async def attendance(query: CallbackQuery, callback_data: Action, state: FSMContext, repo):
    c = callback_data
    if c.kind == "date":
        await state.clear()
        await state.set_state(AttendanceInput.day)
        await query.message.answer("Sanani kiriting: 15.09.2026", reply_markup=cancel_keyboard())
    elif c.kind != "noop":
        day = (
            today()
            if c.kind == "today"
            else date(int(c.value[:4]), int(c.value[4:6]), int(c.value[6:8]))
        )
        page = 0
        if c.kind == "att":
            value = {"1": Decimal(1), "5": Decimal(".5"), "0": None}[c.value[8:]]
            await AttendanceService(repo).set(c.id, day, value)
            people = await PeopleService(repo).list()
            page = next(i // 8 for i, p in enumerate(people) if p.id.hex == c.id)
        elif c.kind == "all":
            await AttendanceService(repo).all_present(day)
        elif c.kind == "attpage":
            page = int(c.id)
        await repo.session.commit()
        await show_day(query.message, repo, day, page, edit=c.kind != "today")
    await query.answer()


@router.message(AttendanceInput.day)
async def entered_day(message: Message, state: FSMContext, repo):
    day = parse_date(message.text or "")
    await state.clear()
    await show_day(message, repo, day)
