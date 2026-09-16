"""Frontend-facing read models; all accounting stays in the shared services."""

from dataclasses import asdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

from app.config.settings import get_settings
from app.models import (
    Advance,
    Category,
    Expense,
    Person,
    Project,
    ProjectIncome,
    Role,
    Status,
)
from app.repositories.analytics import AnalyticsRepository
from app.services.core import (
    AttendanceService,
    PeopleService,
    ProjectService,
    ReportService,
    SalaryService,
    Service,
)
from app.services.values import DomainError, ProjectTotals, month_bounds

ZERO = Decimal(0)


class MiniAppService(Service):
    @property
    def analytics(self) -> AnalyticsRepository:
        return AnalyticsRepository(self.repo.session, self.repo.workspace_id)

    def today(self) -> date:
        return datetime.now(ZoneInfo(get_settings().timezone)).date()

    async def identity(self) -> dict:
        owner = (await PeopleService(self.repo).list(Role.OWNER))[0]
        return {
            "owner": owner,
            "telegram_user_id": owner.telegram_user_id,
            "today": self.today(),
            "version": "0.2.0",
        }

    async def salaries(self, month: date, active: bool = False) -> dict:
        rows = await SalaryService(self.repo).calculate_many(month, active)
        items = [{"person": p, **asdict(r)} for p, r in rows]
        return {
            "month": month,
            "items": items,
            "worker_count": len(items),
            "gross": sum((r.gross for _, r in rows), ZERO),
            "advances": sum((r.advances for _, r in rows), ZERO),
            "remaining": sum((r.remaining for _, r in rows), ZERO),
        }

    async def person_detail(self, person_id: UUID, month: date) -> dict:
        person = await self.require(Person, person_id)
        salary = (
            asdict(await SalaryService(self.repo).calculate_month(person.id, month))
            if person.role == Role.WORKER
            else None
        )
        return {
            "person": person,
            "salary": salary,
            "attendance": await self.monthly_attendance(person.id, month),
        }

    async def daily_attendance(self, day: date) -> dict:
        people = await PeopleService(self.repo).list()
        entries = {
            entry.person_id: entry.value for entry in await AttendanceService(self.repo).day(day)
        }
        return {"date": day, "items": [{"person": p, "value": entries.get(p.id)} for p in people]}

    async def batch_attendance(self, day: date, entries: list[tuple[UUID, Decimal | None]]) -> dict:
        if len({person_id for person_id, _ in entries}) != len(entries):
            raise DomainError("Bir kishi ikki marta kiritilgan.")
        for person_id, value in entries:
            await AttendanceService(self.repo).set(person_id, day, value)
        return await self.daily_attendance(day)

    async def monthly_attendance(self, person_id: UUID, month: date) -> dict:
        entries = await AttendanceService(self.repo).month(person_id, month)
        start, end = month_bounds(month)
        values = {entry.work_date: entry.value for entry in entries}
        return {
            "person_id": person_id,
            "month": start,
            "worked_days": sum(values.values(), ZERO),
            "full_days": sum(value == Decimal(1) for value in values.values()),
            "half_days": sum(value == Decimal("0.5") for value in values.values()),
            "items": [
                {"date": start + timedelta(days=i), "value": values.get(start + timedelta(days=i))}
                for i in range((end - start).days)
            ],
        }

    async def attendance_report(self, month: date) -> dict:
        days, _ = await self.analytics.salary_inputs(*month_bounds(month))
        people = await PeopleService(self.repo).list(active=False)
        return {
            "month": month,
            "worked_days": sum(days.values(), ZERO),
            "items": [{"person": p, "worked_days": days.get(p.id, ZERO)} for p in people],
        }

    async def projects(self, status: Status = Status.ACTIVE) -> list[dict]:
        projects = await ProjectService(self.repo).list(status)
        income, expenses = await self.analytics.project_inputs()
        return [
            {
                "project": p,
                "income": income.get(p.id, ZERO),
                "expenses": expenses.get(p.id, ZERO),
                "balance": ProjectTotals(income.get(p.id, ZERO), expenses.get(p.id, ZERO)).balance,
            }
            for p in projects
        ]

    async def project_detail(self, project_id: UUID) -> dict:
        project = await self.require(Project, project_id)
        totals = await ProjectService(self.repo).totals(project.id)
        return {
            "project": project,
            "income": totals.income,
            "expenses": totals.expenses,
            "balance": totals.balance,
        }

    async def finance(self, start: date, end: date) -> dict:
        report = await ReportService(self.repo).finance_range(start, end)
        return {
            "income": report["income"],
            "business_expenses": report["expenses"][Category.BUSINESS],
            "owner_withdrawals": report["expenses"][Category.OWNER],
            "partner_withdrawals": report["expenses"][Category.PARTNER],
            "other_expenses": report["expenses"][Category.OTHER],
            "expenses": sum(report["expenses"].values(), ZERO),
            "advances": report["advances"],
            "net_cash_flow": report["net"],
        }

    async def chart(self, start: date, end: date) -> list[dict]:
        income = await self.analytics.grouped(
            ProjectIncome,
            ProjectIncome.received_at,
            ProjectIncome.amount,
            ProjectIncome.received_at >= start,
            ProjectIncome.received_at < end,
        )
        expenses = await self.analytics.grouped(
            Expense,
            Expense.expense_date,
            Expense.amount,
            Expense.expense_date >= start,
            Expense.expense_date < end,
        )
        advances = await self.analytics.grouped(
            Advance,
            Advance.paid_at,
            Advance.amount,
            Advance.paid_at >= start,
            Advance.paid_at < end,
        )
        return [
            {
                "date": start + timedelta(days=i),
                "income": income.get(start + timedelta(days=i), ZERO),
                "expenses": expenses.get(start + timedelta(days=i), ZERO),
                "advances": advances.get(start + timedelta(days=i), ZERO),
            }
            for i in range((end - start).days)
        ]

    async def finance_report(self, start: date, end: date) -> dict:
        summary = await self.finance(start, end)  # Validates bounded date range first.
        return {
            "start": start,
            "end": end - timedelta(days=1),
            "summary": summary,
            "chart": await self.chart(start, end),
        }

    async def dashboard(self, month: date) -> dict:
        identity = await self.identity()
        people = await PeopleService(self.repo).list()
        finance = await self.finance_report(*month_bounds(month))
        return {
            **identity,
            "month": month,
            "summary": finance["summary"],
            "cash_flow_chart": finance["chart"],
            "attendance": {
                "date": self.today(),
                "total_people": len(people),
                "marked": await self.analytics.marked_count(self.today()),
            },
            "projects": (await self.projects())[:5],
        }

    async def history(
        self,
        kind: str,
        start: date | None = None,
        end: date | None = None,
        month: date | None = None,
        person_id: UUID | None = None,
        project_id: UUID | None = None,
        category: Category | None = None,
        offset: int = 0,
        limit: int = 30,
    ) -> dict:
        models = {
            "income": (ProjectIncome, ProjectIncome.received_at),
            "expenses": (Expense, Expense.expense_date),
            "advances": (Advance, Advance.paid_at),
        }
        model, date_column = models[kind]
        filters = []
        if start:
            filters.append(date_column >= start)
        if end:
            filters.append(date_column < end)
        if project_id:
            await self.require(Project, project_id)
            filters.append(model.project_id == project_id)
        if person_id:
            await self.require(Person, person_id)
            if model == Advance:
                filters.append(Advance.worker_id == person_id)
            elif model == Expense:
                filters.append(Expense.beneficiary_person_id == person_id)
        if month and model == Advance:
            filters.append(Advance.salary_month == month.replace(day=1))
        if category and model == Expense:
            filters.append(Expense.category == category)
        rows, count = await self.analytics.page(
            model, date_column, *filters, offset=offset, limit=limit
        )
        total = await self.repo.total(model, model.amount, *filters)
        return {"items": rows, "total": count, "amount": total, "offset": offset, "limit": limit}
