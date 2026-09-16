import enum
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Role(enum.StrEnum):
    OWNER = "OWNER"
    PARTNER = "PARTNER"
    WORKER = "WORKER"


class Status(enum.StrEnum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"


class Category(enum.StrEnum):
    BUSINESS = "BUSINESS"
    OWNER = "OWNER"
    PARTNER = "PARTNER"
    OTHER = "OTHER"


class Identity:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Updated:
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Scoped:
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id"), index=True)


class Workspace(Identity, Base):
    __tablename__ = "workspaces"
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True)


class Person(Identity, Updated, Scoped, Base):
    __tablename__ = "people"
    name: Mapped[str] = mapped_column(String(120))
    role: Mapped[Role] = mapped_column(Enum(Role, name="person_role"))
    telegram_user_id: Mapped[int | None] = mapped_column(BigInteger)
    monthly_salary: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (
        UniqueConstraint("workspace_id", "id"),
        CheckConstraint(
            "(role = 'WORKER' AND monthly_salary IS NOT NULL AND monthly_salary > 0) OR (role != 'WORKER' AND monthly_salary IS NULL)",
            name="person_salary",
        ),
    )


class Attendance(Identity, Updated, Scoped, Base):
    __tablename__ = "attendance"
    person_id: Mapped[UUID]
    work_date: Mapped[date] = mapped_column(Date)
    value: Mapped[Decimal] = mapped_column(Numeric(2, 1))
    note: Mapped[str | None] = mapped_column(String(500))
    __table_args__ = (
        ForeignKeyConstraint(["workspace_id", "person_id"], ["people.workspace_id", "people.id"]),
        UniqueConstraint("person_id", "work_date", name="attendance_person_date"),
        CheckConstraint("value IN (0.5, 1)", name="attendance_value"),
        Index("attendance_workspace_date", "workspace_id", "work_date"),
    )


class Project(Identity, Updated, Scoped, Base):
    __tablename__ = "projects"
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(String(1000))
    status: Mapped[Status] = mapped_column(
        Enum(Status, name="project_status"), default=Status.ACTIVE
    )
    __table_args__ = (UniqueConstraint("workspace_id", "id"),)


class Advance(Identity, Scoped, Base):
    __tablename__ = "advances"
    worker_id: Mapped[UUID]
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    paid_at: Mapped[date] = mapped_column(Date)
    salary_month: Mapped[date] = mapped_column(Date)
    project_id: Mapped[UUID | None]
    note: Mapped[str | None] = mapped_column(String(500))
    __table_args__ = (
        ForeignKeyConstraint(["workspace_id", "worker_id"], ["people.workspace_id", "people.id"]),
        ForeignKeyConstraint(
            ["workspace_id", "project_id"], ["projects.workspace_id", "projects.id"]
        ),
        CheckConstraint("amount > 0", name="advance_positive"),
        CheckConstraint("EXTRACT(DAY FROM salary_month) = 1", name="advance_month_start"),
        Index("advance_workspace_month", "workspace_id", "salary_month"),
    )


class ProjectIncome(Identity, Scoped, Base):
    __tablename__ = "project_incomes"
    project_id: Mapped[UUID]
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    received_at: Mapped[date] = mapped_column(Date)
    note: Mapped[str | None] = mapped_column(String(500))
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "project_id"], ["projects.workspace_id", "projects.id"]
        ),
        CheckConstraint("amount > 0", name="income_positive"),
        Index("income_workspace_date", "workspace_id", "received_at"),
    )


class Expense(Identity, Scoped, Base):
    __tablename__ = "expenses"
    project_id: Mapped[UUID | None]
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    expense_date: Mapped[date] = mapped_column(Date)
    category: Mapped[Category] = mapped_column(Enum(Category, name="expense_category"))
    beneficiary_person_id: Mapped[UUID | None]
    note: Mapped[str | None] = mapped_column(String(500))
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "project_id"], ["projects.workspace_id", "projects.id"]
        ),
        ForeignKeyConstraint(
            ["workspace_id", "beneficiary_person_id"], ["people.workspace_id", "people.id"]
        ),
        CheckConstraint("amount > 0", name="expense_positive"),
        CheckConstraint(
            "(category IN ('OWNER', 'PARTNER') AND beneficiary_person_id IS NOT NULL) OR (category IN ('BUSINESS', 'OTHER') AND beneficiary_person_id IS NULL)",
            name="expense_beneficiary",
        ),
        Index("expense_workspace_date", "workspace_id", "expense_date"),
    )
