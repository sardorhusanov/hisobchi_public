from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.bot.ui import Action, button, cancel_keyboard, inline, month_label, today
from app.models import Category, Person
from app.services.core import AttendanceService, PeopleService, ReportService, SalaryService
from app.services.values import DomainError, money, parse_month

router = Router()


class ReportInput(StatesGroup):
    month = State()


async def send_report(message, repo, kind, month, person_id=None):
    lines = [month_label(month)]
    service = ReportService(repo)
    if kind == "salary":
        if person_id:
            person = await PeopleService(repo).require(Person, person_id)
            results = [(person, await SalaryService(repo).calculate_month(person.id, month))]
        else:
            results = await service.salaries(month)
        for person, r in results:
            lines.append(
                f"\n{person.name}\nOylik: {money(r.monthly_salary)}\n1 kunlik: {money(r.daily_rate)}\nIshlagan: {r.worked_days} kun\nHisoblangan: {money(r.gross)}\nAvans: {money(r.advances)}\nQolgan: {money(r.remaining)}"
            )
    elif kind == "attendance":
        if person_id:
            person = await PeopleService(repo).require(Person, person_id)
            entries = await AttendanceService(repo).month(person.id, month)
            lines.append(person.name)
            lines.extend(
                f"{e.work_date:%d.%m.%Y}: {e.value} kun"
                for e in sorted(entries, key=lambda e: e.work_date)
            )
            lines.append(f"Jami: {await AttendanceService(repo).days(person.id, month)} kun")
        else:
            lines.extend(f"{p.name}: {days} kun" for p, days in await service.attendance(month))
    elif kind == "advances":
        people = {p.id: p.name for p in await PeopleService(repo).list(active=False)}
        entries = await service.advances(month)
        lines.append("Oylik davriga yozilgan avanslar:")
        lines.extend(
            f"{e.paid_at:%d.%m.%Y} — {people[e.worker_id]}: {money(e.amount)}" for e in entries
        )
        if not entries:
            lines.append("Avanslar yo'q.")
    elif kind == "finance":
        r = await service.finance(month)
        lines += [
            f"Tushum: {money(r['income'])}",
            f"Biznes xarajatlari: {money(r['expenses'][Category.BUSINESS])}",
            f"Egasi olgan: {money(r['expenses'][Category.OWNER])}",
            f"Hamkor olgan: {money(r['expenses'][Category.PARTNER])}",
            f"Boshqa xarajatlar: {money(r['expenses'][Category.OTHER])}",
            f"Jami xarajatlar: {money(sum(r['expenses'].values()))}",
            f"Ishchi avanslari: {money(r['advances'])}",
            f"Sof pul harakati: {money(r['net'])}",
            "Avanslar to'langan sana bo'yicha hisoblandi.",
        ]
    else:
        raise DomainError("Hisobot topilmadi.")
    chunk = ""
    for line in lines:
        if len(chunk) + len(line) > 3500:
            await message.answer(chunk)
            chunk = ""
        chunk += line + "\n"
    await message.answer(chunk or "Ma'lumot yo'q.", reply_markup=inline([]))


@router.callback_query(Action.filter(F.kind.in_({"report", "salary", "personatt"})))
async def report_start(query: CallbackQuery, callback_data: Action, state: FSMContext):
    c = callback_data
    await state.clear()
    await state.set_state(ReportInput.month)
    await state.update_data(
        kind=c.value if c.kind == "report" else ("salary" if c.kind == "salary" else "attendance"),
        person_id=c.id or None,
    )
    await query.message.answer(
        "Oyni kiriting (2026-09) yoki joriy oyni tanlang.", reply_markup=cancel_keyboard()
    )
    await query.message.answer(
        "Hisobot davri", reply_markup=inline([[button(month_label(today()), "currentreport")]])
    )
    await query.answer()


@router.callback_query(ReportInput.month, Action.filter(F.kind == "currentreport"))
async def current_report(query: CallbackQuery, state: FSMContext, repo):
    data = await state.get_data()
    await send_report(query.message, repo, data["kind"], today(), data["person_id"])
    await state.clear()
    await query.answer()


@router.message(ReportInput.month)
async def report_month(message: Message, state: FSMContext, repo):
    month = parse_month(message.text or "")
    data = await state.get_data()
    await send_report(message, repo, data["kind"], month, data["person_id"])
    await state.clear()
