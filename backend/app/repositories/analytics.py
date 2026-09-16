"""Bounded histories and grouped aggregates shared by bot/API services."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select

from app.models import Advance, Attendance, Expense, Person, ProjectIncome
from app.repositories.core import Repository


class AnalyticsRepository(Repository):
    async def grouped(self, model, key, value, *filters) -> dict:
        rows = await self.session.execute(
            select(key, func.sum(value))
            .where(model.workspace_id == self.workspace_id, *filters)
            .group_by(key)
        )
        return dict(rows.all())

    async def salary_inputs(
        self, start: date, end: date
    ) -> tuple[dict[UUID, Decimal], dict[UUID, Decimal]]:
        days = await self.grouped(
            Attendance,
            Attendance.person_id,
            Attendance.value,
            Attendance.work_date >= start,
            Attendance.work_date < end,
        )
        advances = await self.grouped(
            Advance, Advance.worker_id, Advance.amount, Advance.salary_month == start
        )
        return days, advances

    async def project_inputs(self) -> tuple[dict[UUID, Decimal], dict[UUID, Decimal]]:
        return (
            await self.grouped(ProjectIncome, ProjectIncome.project_id, ProjectIncome.amount),
            await self.grouped(Expense, Expense.project_id, Expense.amount),
        )

    async def page(
        self, model, date_column, *filters, offset: int = 0, limit: int = 30
    ) -> tuple[list, int]:
        predicates = (model.workspace_id == self.workspace_id, *filters)
        count = await self.session.scalar(
            select(func.count()).select_from(model).where(*predicates)
        )
        rows = await self.session.scalars(
            select(model)
            .where(*predicates)
            .order_by(date_column.desc(), model.created_at.desc(), model.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(rows), count

    async def marked_count(self, day: date) -> int:
        return await self.session.scalar(
            select(func.count())
            .select_from(Attendance)
            .join(
                Person,
                (Person.id == Attendance.person_id) & (Person.workspace_id == self.workspace_id),
            )
            .where(
                Attendance.workspace_id == self.workspace_id,
                Attendance.work_date == day,
                Person.is_active.is_(True),
            )
        )
