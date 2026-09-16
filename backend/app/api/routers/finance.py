from uuid import UUID

from fastapi import APIRouter, Response

from app.api.dependencies.filters import Limit, Month, Offset, Period
from app.api.dependencies.workspace import CurrentRepository
from app.api.schemas.models import (
    AdvanceCreate,
    AdvanceOut,
    ExpenseCreate,
    ExpenseOut,
    FinanceReport,
    IncomeOut,
    Page,
)
from app.models import Category
from app.services.core import AdvanceService, FinanceService
from app.services.miniapp import MiniAppService

router = APIRouter(tags=["Finance and advances"])


@router.get("/advances", response_model=Page[AdvanceOut])
async def advances(
    month: Month,
    repo: CurrentRepository,
    worker_id: UUID | None = None,
    project_id: UUID | None = None,
    offset: Offset = 0,
    limit: Limit = 30,
):
    return await MiniAppService(repo).history(
        "advances",
        month=month,
        person_id=worker_id,
        project_id=project_id,
        offset=offset,
        limit=limit,
    )


@router.post("/advances", response_model=AdvanceOut, status_code=201)
async def add_advance(body: AdvanceCreate, repo: CurrentRepository):
    return await AdvanceService(repo).add(**body.model_dump())


@router.delete("/advances/{advance_id}", status_code=204)
async def delete_advance(advance_id: UUID, repo: CurrentRepository):
    await AdvanceService(repo).delete(advance_id)
    return Response(status_code=204)


@router.get("/expenses", response_model=Page[ExpenseOut])
async def expenses(
    period: Period,
    repo: CurrentRepository,
    project_id: UUID | None = None,
    person_id: UUID | None = None,
    category: Category | None = None,
    offset: Offset = 0,
    limit: Limit = 30,
):
    return await MiniAppService(repo).history(
        "expenses",
        *period,
        person_id=person_id,
        project_id=project_id,
        category=category,
        offset=offset,
        limit=limit,
    )


@router.post("/expenses", response_model=ExpenseOut, status_code=201)
async def add_expense(body: ExpenseCreate, repo: CurrentRepository):
    return await FinanceService(repo).expense(
        body.amount,
        body.expense_date,
        body.category,
        body.project_id,
        body.beneficiary_person_id,
        body.note,
    )


@router.get("/finance/summary", response_model=FinanceReport)
async def summary(period: Period, repo: CurrentRepository):
    return await MiniAppService(repo).finance_report(*period)


@router.get("/finance/income", response_model=Page[IncomeOut])
async def income(
    period: Period,
    repo: CurrentRepository,
    project_id: UUID | None = None,
    offset: Offset = 0,
    limit: Limit = 30,
):
    return await MiniAppService(repo).history(
        "income", *period, project_id=project_id, offset=offset, limit=limit
    )


@router.get("/finance/advances", response_model=Page[AdvanceOut])
async def cash_advances(
    period: Period,
    repo: CurrentRepository,
    worker_id: UUID | None = None,
    project_id: UUID | None = None,
    offset: Offset = 0,
    limit: Limit = 30,
):
    return await MiniAppService(repo).history(
        "advances", *period, person_id=worker_id, project_id=project_id, offset=offset, limit=limit
    )
