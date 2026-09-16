from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.models import Attendance, Person, Role, Workspace


class WorkspaceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def initialize(self, telegram_id: int, name: str) -> Workspace:
        # The unique key serializes concurrent /start calls in PostgreSQL.
        result = await self.session.execute(
            insert(Workspace)
            .values(telegram_user_id=telegram_id)
            .on_conflict_do_nothing(index_elements=[Workspace.telegram_user_id])
            .returning(Workspace.id)
        )
        new_id = result.scalar_one_or_none()
        workspace = (
            await self.session.scalars(
                select(Workspace).where(Workspace.telegram_user_id == telegram_id)
            )
        ).one()
        if new_id:
            self.session.add(
                Person(
                    workspace_id=new_id,
                    name=name[:120],
                    role=Role.OWNER,
                    telegram_user_id=telegram_id,
                )
            )
            await self.session.flush()
        return workspace


class Repository:
    def __init__(self, session: AsyncSession, workspace_id: UUID):
        self.session, self.workspace_id = session, workspace_id

    async def get[T: Base](self, model: type[T], record_id: UUID) -> T | None:
        return await self.session.scalar(
            select(model).where(model.workspace_id == self.workspace_id, model.id == record_id)
        )

    async def list[T: Base](self, model: type[T], *filters) -> list[T]:
        return list(
            await self.session.scalars(
                select(model)
                .where(model.workspace_id == self.workspace_id, *filters)
                .order_by(model.created_at, model.id)
            )
        )

    async def add[T: Base](self, model: type[T], **values) -> T:
        record = model(workspace_id=self.workspace_id, **values)
        self.session.add(record)
        await self.session.flush()
        return record

    async def total(self, model, column, *filters) -> Decimal:
        return await self.session.scalar(
            select(func.coalesce(func.sum(column), 0)).where(
                model.workspace_id == self.workspace_id, *filters
            )
        )

    async def remove(self, record: Base) -> None:
        assert record.workspace_id == self.workspace_id
        await self.session.delete(record)
        await self.session.flush()

    async def attendance(self, person_id: UUID, day: date, value: Decimal | None) -> None:
        if value is None:
            rows = await self.list(
                Attendance, Attendance.person_id == person_id, Attendance.work_date == day
            )
            for row in rows:
                await self.remove(row)
        else:
            await self.session.execute(
                insert(Attendance)
                .values(
                    workspace_id=self.workspace_id, person_id=person_id, work_date=day, value=value
                )
                .on_conflict_do_update(
                    constraint="attendance_person_date",
                    set_={"value": value, "updated_at": func.now()},
                    where=Attendance.workspace_id == self.workspace_id,
                )
            )
