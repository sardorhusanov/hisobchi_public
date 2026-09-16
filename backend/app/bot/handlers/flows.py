from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.bot.ui import Action, button, cancel_keyboard, inline, main_keyboard, month_label, today
from app.models import Category, Person, Project, Role
from app.services.core import AdvanceService, FinanceService, PeopleService, ProjectService
from app.services.values import DomainError, money, money_input, parse_date, parse_month

router = Router()


class Input(StatesGroup):
    name = State()
    amount = State()
    month = State()
    category = State()
    beneficiary = State()
    day = State()
    note = State()
    confirm = State()


async def confirm(message, state):
    d = await state.get_data()
    labels = {
        "addperson": "Kishi qo'shish",
        "rename": "Ismni o'zgartirish",
        "addproject": "Loyiha qo'shish",
        "addadvance": "Avans",
        "income": "Pul tushumi",
        "expense": "Xarajat",
        "archive": "Arxivlash",
        "complete": "Loyihani tugatish",
    }
    lines = [labels[d["kind"]], d.get("label", ""), d.get("name", "")]
    if "amount" in d:
        lines.append(money(Decimal(d["amount"])))
    if "month" in d:
        lines.append("Oylik davri: " + month_label(date.fromisoformat(d["month"])))
    if "day" in d:
        lines.append("Sana: " + date.fromisoformat(d["day"]).strftime("%d.%m.%Y"))
    if "category" in d:
        lines.append(
            {
                "BUSINESS": "Biznes",
                "OWNER": "Egasi olgan",
                "PARTNER": "Hamkor olgan",
                "OTHER": "Boshqa",
            }[d["category"]]
        )
    if d.get("beneficiary_label"):
        lines.append("Pul oluvchi: " + d["beneficiary_label"])
    if d.get("note"):
        lines.append(d["note"])
    nonce = uuid4().hex[:12]
    await state.update_data(nonce=nonce)
    await state.set_state(Input.confirm)
    rows = [[button("✅ Tasdiqlash", "save", nonce)]]
    if d["kind"] in ("addadvance", "income", "expense"):
        rows.append([button("Sanani o'zgartirish", "editday"), button("Izoh", "editnote")])
    if d["kind"] == "addadvance":
        rows.append([button("Oylik davrini o'zgartirish", "editmonth")])
    await message.answer(
        "\n".join(filter(None, lines)) + "\n\nSaqlaysizmi?",
        reply_markup=inline(rows),
    )


@router.callback_query(
    Action.filter(
        F.kind.in_(
            {
                "addperson",
                "rename",
                "addproject",
                "addadvance",
                "income",
                "expense",
                "archive",
                "complete",
            }
        )
    )
)
async def begin(query: CallbackQuery, callback_data: Action, state: FSMContext, repo):
    c = callback_data
    await state.clear()
    data = dict(kind=c.kind, record_id=c.id or None, role=c.value)
    if c.kind in ("addadvance", "income", "expense"):
        data.update(day=today().isoformat(), note=None)
    if c.kind == "addadvance":
        data["month"] = today().replace(day=1).isoformat()
    if c.kind in ("rename", "addadvance", "archive"):
        person = await PeopleService(repo).require(Person, c.id)
        data["label"] = person.name
    if c.kind in ("income", "complete") or (c.kind == "expense" and c.id):
        project = await ProjectService(repo).require(Project, c.id)
        data["label"] = project.name
    await state.update_data(**data)
    if c.kind in ("archive", "complete"):
        await confirm(query.message, state)
    elif c.kind in ("addperson", "rename", "addproject"):
        await state.set_state(Input.name)
        await query.message.answer(
            "Nomini kiriting:" if c.kind == "addproject" else "Ismini kiriting:",
            reply_markup=cancel_keyboard(),
        )
    else:
        await state.set_state(Input.amount)
        await query.message.answer("Summani kiriting: 500 000", reply_markup=cancel_keyboard())
    await query.answer()


@router.message(Input.name)
async def name(message: Message, state: FSMContext):
    value = PeopleService.name(message.text or "")
    await state.update_data(name=value)
    d = await state.get_data()
    if d["kind"] == "addperson" and d["role"] == "WORKER":
        await state.set_state(Input.amount)
        await message.answer("Oylik maoshni kiriting: 6 000 000")
    else:
        await confirm(message, state)


async def ask_day(message, state):
    await state.set_state(Input.day)
    await message.answer(
        "To'lov sanasi: bugun yoki DD.MM.YYYY shaklida kiriting.",
        reply_markup=inline([[button("Bugun", "flowday")]]),
    )


async def ask_note(message, state):
    await state.set_state(Input.note)
    await message.answer(
        "Izoh kiriting yoki o'tkazib yuboring.",
        reply_markup=inline([[button("Izohsiz", "skipnote")]]),
    )


@router.callback_query(
    Input.confirm, Action.filter(F.kind.in_({"editday", "editnote", "editmonth"}))
)
async def edit_optional(query: CallbackQuery, callback_data: Action, state: FSMContext):
    if callback_data.kind == "editday":
        await ask_day(query.message, state)
    elif callback_data.kind == "editnote":
        await ask_note(query.message, state)
    else:
        await state.set_state(Input.month)
        await query.message.answer(
            "Oylik davrini YYYY-MM shaklida kiriting.",
            reply_markup=inline([[button(month_label(today()), "flowmonth")]]),
        )
    await query.answer()


@router.message(Input.amount)
async def amount(message: Message, state: FSMContext):
    value = money_input(message.text or "")
    await state.update_data(amount=str(value))
    d = await state.get_data()
    if d["kind"] == "addperson":
        await confirm(message, state)
    elif d["kind"] == "addadvance":
        await confirm(message, state)
    elif d["kind"] == "expense":
        await state.set_state(Input.category)
        await message.answer(
            "Xarajat turini tanlang:",
            reply_markup=inline(
                [
                    [button(label, "category", value=cat)]
                    for label, cat in [
                        ("Biznes xarajati", "BUSINESS"),
                        ("Egasi olgan", "OWNER"),
                        ("Hamkor olgan", "PARTNER"),
                        ("Boshqa", "OTHER"),
                    ]
                ]
            ),
        )
    else:
        await confirm(message, state)


@router.message(Input.month)
async def month(message: Message, state: FSMContext):
    await state.update_data(month=parse_month(message.text or "").isoformat())
    await confirm(message, state)


@router.callback_query(Input.month, Action.filter(F.kind == "flowmonth"))
async def current_month(query: CallbackQuery, state: FSMContext):
    await state.update_data(month=today().replace(day=1).isoformat())
    await confirm(query.message, state)
    await query.answer()


@router.callback_query(Input.category, Action.filter(F.kind == "category"))
async def category(query: CallbackQuery, callback_data: Action, state: FSMContext, repo):
    cat = Category(callback_data.value)
    await state.update_data(category=cat.value)
    if cat in (Category.OWNER, Category.PARTNER):
        people = await PeopleService(repo).list(Role(cat.value))
        if not people:
            raise DomainError("Avval hamkor qo'shing.")
        await state.set_state(Input.beneficiary)
        await query.message.answer(
            "Kim pul oldi?",
            reply_markup=inline([[button(p.name, "beneficiary", p.id.hex)] for p in people]),
        )
    else:
        await confirm(query.message, state)
    await query.answer()


@router.callback_query(Input.beneficiary, Action.filter(F.kind == "beneficiary"))
async def beneficiary(query: CallbackQuery, callback_data: Action, state: FSMContext, repo):
    person = await PeopleService(repo).require(Person, callback_data.id)
    await state.update_data(beneficiary_id=person.id.hex, beneficiary_label=person.name)
    await confirm(query.message, state)
    await query.answer()


@router.message(Input.day)
async def day(message: Message, state: FSMContext):
    await state.update_data(day=parse_date(message.text or "").isoformat())
    await confirm(message, state)


@router.callback_query(Input.day, Action.filter(F.kind == "flowday"))
async def current_day(query: CallbackQuery, state: FSMContext):
    await state.update_data(day=today().isoformat())
    await confirm(query.message, state)
    await query.answer()


@router.message(Input.note)
async def note(message: Message, state: FSMContext):
    value = (message.text or "").strip()
    if not 1 <= len(value) <= 500:
        raise DomainError("Izoh 1–500 ta belgidan iborat bo'lishi kerak.")
    await state.update_data(note=value)
    await confirm(message, state)


@router.callback_query(Input.note, Action.filter(F.kind == "skipnote"))
async def skip_note(query: CallbackQuery, state: FSMContext):
    await state.update_data(note=None)
    await confirm(query.message, state)
    await query.answer()


@router.callback_query(Input.confirm, Action.filter(F.kind == "save"))
async def save(query: CallbackQuery, callback_data: Action, state: FSMContext, repo):
    d = await state.get_data()
    if callback_data.id != d.get("nonce"):
        raise DomainError("Bu tasdiqlash eskirgan. Oxirgi xabardan foydalaning.")
    kind = d["kind"]
    record_id = UUID(d["record_id"]) if d.get("record_id") else None
    value = Decimal(d["amount"]) if "amount" in d else None
    day = date.fromisoformat(d["day"]) if "day" in d else None
    if kind == "addperson":
        await PeopleService(repo).add(d["name"], Role(d["role"]), value)
    elif kind == "rename":
        await PeopleService(repo).rename(record_id, d["name"])
    elif kind == "archive":
        await PeopleService(repo).deactivate(record_id)
    elif kind == "addproject":
        await ProjectService(repo).add(d["name"])
    elif kind == "complete":
        await ProjectService(repo).complete(record_id)
    elif kind == "addadvance":
        await AdvanceService(repo).add(
            record_id, value, day, date.fromisoformat(d["month"]), note=d.get("note")
        )
    elif kind == "income":
        await FinanceService(repo).income(record_id, value, day, d.get("note"))
    elif kind == "expense":
        await FinanceService(repo).expense(
            value,
            day,
            Category(d["category"]),
            record_id,
            UUID(d["beneficiary_id"]) if d.get("beneficiary_id") else None,
            d.get("note"),
        )
    else:
        raise DomainError("Amal topilmadi.")
    # Commit before announcing success; event isolation prevents double-tap saves.
    await repo.session.commit()
    await state.clear()
    await query.message.edit_text("✅ Saqlandi.", reply_markup=inline([]))
    await query.message.answer("Bosh menyu", reply_markup=main_keyboard())
    await query.answer()
