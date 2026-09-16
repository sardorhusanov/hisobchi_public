from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot.ui import Action, button, inline, month_label
from app.models import Advance, Person, Project, Status
from app.services.core import AdvanceService, PeopleService, ProjectService
from app.services.values import money

router = Router()


@router.callback_query(
    Action.filter(
        F.kind.in_(
            {"person", "worker", "history", "deladvance", "projects", "project", "incomechoose"}
        )
    )
)
async def records(query: CallbackQuery, callback_data: Action, repo):
    c = callback_data
    rows = []
    text = "Tanlang"
    if c.kind in ("person", "worker"):
        p = await PeopleService(repo).require(Person, c.id)
        text = p.name + (f"\nOylik: {money(p.monthly_salary)}" if p.monthly_salary else "")
        rows = [
            [button("Oylik davomat", "personatt", p.id.hex)],
            [button("Ismni o'zgartirish", "rename", p.id.hex)],
            [button("Arxivlash", "archive", p.id.hex)],
        ]
        if p.monthly_salary:
            rows[:0] = [
                [button("Avans berish", "addadvance", p.id.hex)],
                [button("Avanslar tarixi", "history", p.id.hex)],
                [button("Oylik hisoblash", "salary", p.id.hex)],
            ]
    elif c.kind == "history":
        entries = await AdvanceService(repo).history(c.id)
        text = "Avanslar tarixi (o'chirish uchun tanlang)"
        rows = [
            [
                button(
                    f"{a.paid_at:%d.%m.%Y}: {money(a.amount)} / {month_label(a.salary_month)}",
                    "deladvance",
                    a.id.hex,
                )
            ]
            for a in entries
        ]
    elif c.kind == "deladvance":
        a = await AdvanceService(repo).require(Advance, c.id)
        text = f"{money(a.amount)} avansni o'chirish?\nOylik davri: {month_label(a.salary_month)}"
        rows = [[button("Ha, o'chirish", "confirmdelete", a.id.hex)]]
    elif c.kind in ("projects", "incomechoose"):
        projects = await ProjectService(repo).list(Status(c.value) if c.value else Status.ACTIVE)
        text = "Loyihani tanlang"
        rows = [
            [button(p.name, "project" if c.kind == "projects" else "income", p.id.hex)]
            for p in projects
        ]
    else:
        p = await ProjectService(repo).require(Project, c.id)
        totals = await ProjectService(repo).totals(p.id)
        text = f"{p.name}\nTushum: {money(totals.income)}\nXarajatlar: {money(totals.expenses)}\nQoldiq: {money(totals.balance)}"
        rows = [[button("Hisobot", "project", p.id.hex)]]
        if p.status == Status.ACTIVE:
            rows += [
                [button("Pul tushumi", "income", p.id.hex), button("Xarajat", "expense", p.id.hex)],
                [button("Loyiha tugatish", "complete", p.id.hex)],
            ]
    if not rows:
        text += "\nHozircha ma'lumot yo'q."
    for offset in range(0, max(1, len(rows)), 40):
        await query.message.answer(text, reply_markup=inline(rows[offset : offset + 40]))
    await query.answer()


@router.callback_query(Action.filter(F.kind == "confirmdelete"))
async def delete(query: CallbackQuery, callback_data: Action, repo):
    await AdvanceService(repo).delete(callback_data.id)
    await repo.session.commit()
    await query.message.edit_text("Avans o'chirildi.", reply_markup=inline([]))
    await query.answer()
