from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.models import (
    Advance,
    Attendance,
    Category,
    Expense,
    Person,
    Project,
    ProjectIncome,
    Role,
    Status,
    Workspace,
)
from app.repositories.analytics import AnalyticsRepository
from app.repositories.core import Repository, WorkspaceRepository
from app.services.values import (
    DomainError,
    ProjectTotals,
    SalaryResult,
    calculate_salary,
    money_input,
    month_bounds,
)


class WorkspaceService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = WorkspaceRepository(session)

    async def initialize(self, telegram_id: int, name: str) -> Workspace:
        return await self.repository.initialize(telegram_id, name)


class Service:
    def __init__(self, repository: Repository) -> None:
        self.repo = repository

    async def require[T: Base](self, model: type[T], record_id: UUID | str) -> T:
        record = await self.repo.get(model, UUID(str(record_id)))
        if record is None:
            raise DomainError("Ma'lumot topilmadi. Menyudan qayta tanlang.")
        return record

    @staticmethod
    def name(value: str) -> str:
        value = value.strip()
        if not 1 <= len(value) <= 120:
            raise DomainError("Nom 1–120 ta belgidan iborat bo'lishi kerak.")
        return value

    @staticmethod
    def amount(value: Decimal) -> Decimal:
        return money_input(str(value))


class PeopleService(Service):
    async def list(self, role: Role | None = None, active: bool = True) -> list[Person]:
        filters = [Person.is_active.is_(True)] if active else []
        if role:
            filters.append(Person.role == role)
        return await self.repo.list(Person, *filters)

    async def add(self, name: str, role: Role, salary: Decimal | None = None) -> Person:
        if role == Role.OWNER:
            raise DomainError("Egasi avtomatik yaratiladi.")
        if role == Role.WORKER:
            if salary is None:
                raise DomainError("Ishchi oyligini kiriting.")
            self.amount(salary)
        elif salary is not None:
            raise DomainError("Hamkorning belgilangan oyligi yo'q.")
        return await self.repo.add(Person, name=self.name(name), role=role, monthly_salary=salary)

    async def rename(self, person_id: UUID | str, name: str) -> None:
        person = await self.require(Person, person_id)
        person.name = self.name(name)
        await self.repo.session.flush()

    async def deactivate(self, person_id: UUID | str) -> None:
        person = await self.require(Person, person_id)
        if person.role == Role.OWNER:
            raise DomainError("Egani arxivlab bo'lmaydi.")
        person.is_active = False
        await self.repo.session.flush()

    async def update(
        self,
        person_id: UUID,
        *,
        name: str | None = None,
        monthly_salary: Decimal | None = None,
        is_active: bool | None = None,
    ) -> Person:
        person = await self.require(Person, person_id)
        if name is not None:
            person.name = self.name(name)
        if monthly_salary is not None:
            if person.role != Role.WORKER:
                raise DomainError("Oylik faqat ishchi uchun belgilanadi.")
            person.monthly_salary = self.amount(monthly_salary)
        if is_active is False:
            await self.deactivate(person_id)
        elif is_active is True:
            person.is_active = True
        await self.repo.session.flush()
        return person


class AttendanceService(Service):
    async def day(self, day: date) -> list[Attendance]:
        return await self.repo.list(Attendance, Attendance.work_date == day)

    async def set(self, person_id: UUID | str, day: date, value: Decimal | None) -> None:
        person = await self.require(Person, person_id)
        if value not in (None, Decimal("0.5"), Decimal(1)):
            raise DomainError("Davomat 0.5 yoki 1 bo'lishi kerak.")
        if not person.is_active:
            raise DomainError("Bu kishi arxivlangan.")
        await self.repo.attendance(person.id, day, value)

    async def all_present(self, day: date) -> None:
        for person in await PeopleService(self.repo).list():
            await self.set(person.id, day, Decimal(1))

    async def month(self, person_id: UUID | str, month: date) -> list[Attendance]:
        person = await self.require(Person, person_id)
        start, end = month_bounds(month)
        return await self.repo.list(
            Attendance,
            Attendance.person_id == person.id,
            Attendance.work_date >= start,
            Attendance.work_date < end,
        )

    async def days(self, person_id: UUID | str, month: date) -> Decimal:
        return sum((entry.value for entry in await self.month(person_id, month)), Decimal(0))


class AdvanceService(Service):
    async def add(
        self,
        worker_id: UUID | str,
        amount: Decimal,
        paid_at: date,
        salary_month: date,
        project_id: UUID | None = None,
        note: str | None = None,
    ) -> Advance:
        worker = await self.require(Person, worker_id)
        if worker.role != Role.WORKER or not worker.is_active:
            raise DomainError("Faol ishchini tanlang.")
        if project_id:
            await self.require(Project, project_id)
        return await self.repo.add(
            Advance,
            worker_id=worker.id,
            amount=self.amount(amount),
            paid_at=paid_at,
            salary_month=salary_month.replace(day=1),
            project_id=project_id,
            note=note,
        )

    async def history(self, worker_id: UUID | str) -> list[Advance]:
        worker = await self.require(Person, worker_id)
        return await self.repo.list(Advance, Advance.worker_id == worker.id)

    async def delete(self, advance_id: UUID | str) -> None:
        await self.repo.remove(await self.require(Advance, advance_id))

    async def total(self, worker_id: UUID | str, month: date) -> Decimal:
        worker = await self.require(Person, worker_id)
        return await self.repo.total(
            Advance,
            Advance.amount,
            Advance.worker_id == worker.id,
            Advance.salary_month == month.replace(day=1),
        )


class SalaryService(Service):
    async def calculate_month(self, worker_id: UUID | str, month: date) -> SalaryResult:
        worker = await self.require(Person, worker_id)
        if worker.role != Role.WORKER:
            raise DomainError("Oylik faqat ishchilar uchun hisoblanadi.")
        days = await AttendanceService(self.repo).days(worker.id, month)
        advances = await AdvanceService(self.repo).total(worker.id, month)
        return calculate_salary(worker.monthly_salary, days, advances)

    async def calculate_many(
        self, month: date, active: bool = False
    ) -> list[tuple[Person, SalaryResult]]:
        workers = await PeopleService(self.repo).list(Role.WORKER, active=active)
        days, advances = await AnalyticsRepository(
            self.repo.session, self.repo.workspace_id
        ).salary_inputs(*month_bounds(month))
        return [
            (
                worker,
                calculate_salary(
                    worker.monthly_salary,
                    days.get(worker.id, Decimal(0)),
                    advances.get(worker.id, Decimal(0)),
                ),
            )
            for worker in workers
        ]


class ProjectService(Service):
    async def list(self, status: Status = Status.ACTIVE) -> list[Project]:
        return await self.repo.list(Project, Project.status == status)

    async def add(self, name: str) -> Project:
        return await self.repo.add(Project, name=self.name(name))

    async def complete(self, project_id: UUID | str) -> None:
        project = await self.require(Project, project_id)
        project.status = Status.COMPLETED
        await self.repo.session.flush()

    async def totals(self, project_id: UUID | str) -> ProjectTotals:
        project = await self.require(Project, project_id)
        return ProjectTotals(
            await self.repo.total(
                ProjectIncome, ProjectIncome.amount, ProjectIncome.project_id == project.id
            ),
            await self.repo.total(Expense, Expense.amount, Expense.project_id == project.id),
        )

    async def update(
        self,
        project_id: UUID,
        *,
        name: str | None = None,
        description: str | None = None,
        status: Status | None = None,
    ) -> Project:
        project = await self.require(Project, project_id)
        if name is not None:
            project.name = self.name(name)
        if description is not None:
            if len(description) > 1000:
                raise DomainError("Tavsif 1000 belgidan oshmasin.")
            project.description = description
        if status == Status.COMPLETED:
            await self.complete(project_id)
        elif status == Status.ACTIVE and project.status == Status.COMPLETED:
            raise DomainError("Tugallangan loyihani qayta ochish qo'llab-quvvatlanmaydi.")
        await self.repo.session.flush()
        return project


class FinanceService(Service):
    async def income(
        self, project_id: UUID | str, amount: Decimal, day: date, note: str | None = None
    ) -> ProjectIncome:
        project = await self.require(Project, project_id)
        if project.status != Status.ACTIVE:
            raise DomainError("Loyiha tugallangan.")
        return await self.repo.add(
            ProjectIncome,
            project_id=project.id,
            amount=self.amount(amount),
            received_at=day,
            note=note,
        )

    async def expense(
        self,
        amount: Decimal,
        day: date,
        category: Category,
        project_id: UUID | None = None,
        beneficiary_id: UUID | None = None,
        note: str | None = None,
    ) -> Expense:
        if project_id:
            project = await self.require(Project, project_id)
            if project.status != Status.ACTIVE:
                raise DomainError("Loyiha tugallangan.")
        if category in (Category.OWNER, Category.PARTNER):
            if not beneficiary_id:
                raise DomainError("Pul olgan kishini tanlang.")
            person = await self.require(Person, beneficiary_id)
            if person.role.value != category.value:
                raise DomainError("Kishi toifasi mos emas.")
        elif beneficiary_id:
            raise DomainError("Bu xarajat uchun pul oluvchi ko'rsatilmaydi.")
        return await self.repo.add(
            Expense,
            amount=self.amount(amount),
            expense_date=day,
            category=category,
            project_id=project_id,
            beneficiary_person_id=beneficiary_id,
            note=note,
        )


class ReportService(Service):
    async def attendance(self, month: date) -> list[tuple[Person, Decimal]]:
        service = AttendanceService(self.repo)
        return [
            (p, await service.days(p.id, month))
            for p in await PeopleService(self.repo).list(active=False)
        ]

    async def salaries(self, month: date) -> list[tuple[Person, SalaryResult]]:
        return await SalaryService(self.repo).calculate_many(month)

    async def advances(self, month: date) -> list[Advance]:
        return await self.repo.list(Advance, Advance.salary_month == month.replace(day=1))

    async def finance(self, month: date) -> dict[str, Decimal | dict[Category, Decimal]]:
        return await self.finance_range(*month_bounds(month))

    async def finance_range(self, start: date, end: date) -> dict:
        if end <= start or (end - start).days > 366:
            raise DomainError("Davr 1–366 kun bo'lishi kerak.")
        income = await self.repo.total(
            ProjectIncome,
            ProjectIncome.amount,
            ProjectIncome.received_at >= start,
            ProjectIncome.received_at < end,
        )
        expenses = {
            category: await self.repo.total(
                Expense,
                Expense.amount,
                Expense.category == category,
                Expense.expense_date >= start,
                Expense.expense_date < end,
            )
            for category in Category
        }
        advances = await self.repo.total(
            Advance, Advance.amount, Advance.paid_at >= start, Advance.paid_at < end
        )
        return {
            "income": income,
            "expenses": expenses,
            "advances": advances,
            "net": income - sum(expenses.values(), Decimal(0)) - advances,
        }
