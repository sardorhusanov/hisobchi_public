from datetime import date
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from app.models import Category, Role, Status
from app.services.values import money_input


def parse_money(value) -> Decimal:
    if isinstance(value, (float, bool)):
        raise ValueError("Send monetary values as decimal strings")
    return money_input(str(value))


MoneyInput = Annotated[Decimal, BeforeValidator(parse_money)]
Name = Annotated[str, Field(min_length=1, max_length=120)]
Note = Annotated[str, Field(max_length=500)]


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class PersonOut(Schema):
    id: UUID
    name: str
    role: Role
    monthly_salary: Decimal | None
    is_active: bool


class PersonCreate(Schema):
    name: Name
    role: Literal["WORKER", "PARTNER"]
    monthly_salary: MoneyInput | None = None


class PersonPatch(Schema):
    name: Name | None = None
    monthly_salary: MoneyInput | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def no_explicit_null(self):
        if any(getattr(self, key) is None for key in self.model_fields_set):
            raise ValueError("Fields must not be null")
        return self


class IdentityOut(Schema):
    owner: PersonOut
    telegram_user_id: int
    today: date
    version: str


class SalaryOut(Schema):
    monthly_salary: Decimal
    daily_rate: Decimal
    worked_days: Decimal
    gross: Decimal
    advances: Decimal
    remaining: Decimal


class WorkerSalaryOut(SalaryOut):
    person: PersonOut


class SalariesOut(Schema):
    month: date
    items: list[WorkerSalaryOut]
    worker_count: int
    gross: Decimal
    advances: Decimal
    remaining: Decimal


class AttendanceEntry(Schema):
    person_id: UUID
    value: Literal["1", "0.5"] | None


class AttendanceBatch(Schema):
    date: date
    items: list[AttendanceEntry] = Field(max_length=500)


class AttendancePerson(Schema):
    person: PersonOut
    value: Decimal | None


class AttendanceDay(Schema):
    date: date
    items: list[AttendancePerson]


class CalendarDay(Schema):
    date: date
    value: Decimal | None


class AttendanceMonth(Schema):
    person_id: UUID
    month: date
    worked_days: Decimal
    full_days: int
    half_days: int
    items: list[CalendarDay]


class AttendanceTotal(Schema):
    person: PersonOut
    worked_days: Decimal


class AttendanceReport(Schema):
    month: date
    worked_days: Decimal
    items: list[AttendanceTotal]


class PersonDetail(Schema):
    person: PersonOut
    salary: SalaryOut | None
    attendance: AttendanceMonth


class ProjectOut(Schema):
    id: UUID
    name: str
    description: str | None
    status: Status


class ProjectCreate(Schema):
    name: Name
    description: str = Field(default="", max_length=1000)


class ProjectPatch(Schema):
    name: Name | None = None
    description: str | None = Field(default=None, max_length=1000)
    status: Status | None = None


class ProjectSummary(Schema):
    project: ProjectOut
    income: Decimal
    expenses: Decimal
    balance: Decimal


class IncomeCreate(Schema):
    amount: MoneyInput
    received_at: date
    note: Note | None = None


class IncomeOut(Schema):
    id: UUID
    project_id: UUID
    amount: Decimal
    received_at: date
    note: str | None


class ExpenseCreate(Schema):
    amount: MoneyInput
    expense_date: date
    category: Category
    project_id: UUID | None = None
    beneficiary_person_id: UUID | None = None
    note: Note | None = None


class ExpenseOut(ExpenseCreate):
    id: UUID
    amount: Decimal


class AdvanceCreate(Schema):
    worker_id: UUID
    amount: MoneyInput
    paid_at: date
    salary_month: date
    project_id: UUID | None = None
    note: Note | None = None


class AdvanceOut(AdvanceCreate):
    id: UUID
    amount: Decimal


class Page[T](Schema):
    items: list[T]
    total: int
    amount: Decimal
    offset: int
    limit: int


class FinanceSummary(Schema):
    income: Decimal
    expenses: Decimal
    business_expenses: Decimal
    owner_withdrawals: Decimal
    partner_withdrawals: Decimal
    other_expenses: Decimal
    advances: Decimal
    net_cash_flow: Decimal


class ChartPoint(Schema):
    date: date
    income: Decimal
    expenses: Decimal
    advances: Decimal


class FinanceReport(Schema):
    start: date
    end: date
    summary: FinanceSummary
    chart: list[ChartPoint]


class AttendanceProgress(Schema):
    date: date
    total_people: int
    marked: int


class Dashboard(IdentityOut):
    month: date
    summary: FinanceSummary
    cash_flow_chart: list[ChartPoint]
    attendance: AttendanceProgress
    projects: list[ProjectSummary]
