"""Run with TEST_DATABASE_URL pointing to an empty, migrated test database."""

import os
from datetime import date
from decimal import Decimal as D
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Advance, Attendance, Category, Person, Role
from app.repositories.core import Repository
from app.services.core import (
    AdvanceService,
    AttendanceService,
    FinanceService,
    PeopleService,
    ProjectService,
    ReportService,
    SalaryService,
    WorkspaceService,
)
from app.services.values import DomainError

pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL is not configured"
)


async def test_initialization_idempotent(context):
    session, repo = context
    service = WorkspaceService(session)
    user_id = uuid4().int % (2**62)
    a = await service.initialize(user_id, "Owner")
    b = await service.initialize(user_id, "Changed")
    assert a.id == b.id
    people = await PeopleService(Repository(session, a.id)).list()
    assert len(people) == 1
    assert people[0].role == Role.OWNER
    assert people[0].monthly_salary is None


async def test_salary_attendance_and_advances(context):
    _, repo = context
    worker = await PeopleService(repo).add("Ali", Role.WORKER, D(6000000))
    attendance = AttendanceService(repo)
    await attendance.set(worker.id, date(2026, 9, 1), D(1))
    await attendance.set(worker.id, date(2026, 9, 2), D(1))
    await attendance.set(worker.id, date(2026, 9, 2), D(".5"))
    await attendance.set(worker.id, date(2026, 10, 1), D(1))
    await AdvanceService(repo).add(worker.id, D(100000), date(2026, 8, 30), date(2026, 9, 1))
    await AdvanceService(repo).add(worker.id, D(50000), date(2026, 9, 2), date(2026, 9, 1))
    await AdvanceService(repo).add(worker.id, D(900000), date(2026, 9, 2), date(2026, 10, 1))
    result = await SalaryService(repo).calculate_month(worker.id, date(2026, 9, 15))
    assert result.worked_days == D("1.5")
    assert result.gross == D(300000)
    assert result.advances == D(150000)
    assert result.remaining == D(150000)
    await attendance.set(worker.id, date(2026, 9, 2), None)
    assert await attendance.days(worker.id, date(2026, 9, 1)) == D(1)
    assert len(await AdvanceService(repo).history(worker.id)) == 3


async def test_project_and_finance(context):
    _, repo = context
    project = await ProjectService(repo).add("Project A")
    owner = (await PeopleService(repo).list(Role.OWNER))[0]
    partner = await PeopleService(repo).add("Partner", Role.PARTNER)
    worker = await PeopleService(repo).add("Worker", Role.WORKER, D(6000000))
    finance = FinanceService(repo)
    day = date(2026, 9, 15)
    await finance.income(project.id, D(10000000), day)
    await finance.income(project.id, D(4000000), day)
    await finance.expense(D(2000000), day, Category.BUSINESS, project.id)
    await finance.expense(D(500000), day, Category.OWNER, project.id, owner.id)
    await finance.expense(D(100000), day, Category.PARTNER, beneficiary_id=partner.id)
    await AdvanceService(repo).add(worker.id, D(300000), day, day)
    totals = await ProjectService(repo).totals(project.id)
    assert totals.income == D(14000000)
    assert totals.expenses == D(2500000)
    assert totals.balance == D(11500000)
    report = await ReportService(repo).finance(day)
    assert report["advances"] == D(300000)
    assert report["net"] == D(11100000)
    with pytest.raises(DomainError):
        await finance.expense(D(1), day, Category.OWNER, beneficiary_id=partner.id)


async def test_workspace_isolation(context):
    session, repo = context
    other = await WorkspaceService(session).initialize(uuid4().int % (2**62), "Other")
    foreign = Repository(session, other.id)
    person = await PeopleService(foreign).add("Foreign", Role.WORKER, D(100))
    project = await ProjectService(foreign).add("Foreign project")
    assert await repo.get(Person, person.id) is None
    with pytest.raises(DomainError):
        await AttendanceService(repo).set(person.id, date(2026, 9, 1), D(1))
    with pytest.raises(DomainError):
        await SalaryService(repo).calculate_month(person.id, date(2026, 9, 1))
    with pytest.raises(DomainError):
        await FinanceService(repo).income(project.id, D(1), date(2026, 9, 1))
    with pytest.raises(IntegrityError):
        async with session.begin_nested():
            await repo.add(Attendance, person_id=person.id, work_date=date(2026, 9, 1), value=D(1))


async def test_database_constraints(context):
    session, repo = context
    worker = await PeopleService(repo).add("Ali", Role.WORKER, D(100))
    for model, values in [
        (Person, dict(name="Bad", role=Role.WORKER, monthly_salary=D(0))),
        (Attendance, dict(person_id=worker.id, work_date=date(2026, 9, 1), value=D(".2"))),
        (
            Advance,
            dict(
                worker_id=worker.id,
                amount=D(-1),
                paid_at=date(2026, 9, 1),
                salary_month=date(2026, 9, 1),
            ),
        ),
    ]:
        with pytest.raises(IntegrityError):
            async with session.begin_nested():
                await repo.add(model, **values)


async def test_committed_data_survives_new_connection():
    from sqlalchemy import delete
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.models import Workspace

    engine = create_async_engine(os.environ["TEST_DATABASE_URL"])
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    user_id = uuid4().int % (2**62)
    workspace_id = None
    try:
        async with sessions.begin() as session:
            workspace = await WorkspaceService(session).initialize(user_id, "Persistent owner")
            workspace_id = workspace.id
            await PeopleService(Repository(session, workspace_id)).add(
                "Persistent worker", Role.WORKER, D("6000000")
            )
        await engine.dispose()
        async with sessions.begin() as session:
            workspace = await WorkspaceService(session).initialize(user_id, "Persistent owner")
            assert workspace.id == workspace_id
            people = await PeopleService(Repository(session, workspace_id)).list()
            assert len(people) == 2
            assert any(p.monthly_salary == D("6000000") for p in people)
    finally:
        if workspace_id:
            async with sessions.begin() as session:
                await session.execute(delete(Person).where(Person.workspace_id == workspace_id))
                await session.execute(delete(Workspace).where(Workspace.id == workspace_id))
        await engine.dispose()
