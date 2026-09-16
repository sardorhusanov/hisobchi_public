from uuid import UUID

from fastapi import APIRouter

from app.api.dependencies.filters import Limit, Offset
from app.api.dependencies.workspace import CurrentRepository
from app.api.schemas.models import (
    ExpenseOut,
    IncomeCreate,
    IncomeOut,
    Page,
    ProjectCreate,
    ProjectOut,
    ProjectPatch,
    ProjectSummary,
)
from app.models import Status
from app.services.core import FinanceService, ProjectService
from app.services.miniapp import MiniAppService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=list[ProjectSummary])
async def projects(repo: CurrentRepository, status: Status = Status.ACTIVE):
    return await MiniAppService(repo).projects(status)


@router.post("", response_model=ProjectOut, status_code=201)
async def create_project(body: ProjectCreate, repo: CurrentRepository):
    project = await ProjectService(repo).add(body.name)
    return await ProjectService(repo).update(project.id, description=body.description)


@router.get("/{project_id}", response_model=ProjectSummary)
async def project(project_id: UUID, repo: CurrentRepository):
    return await MiniAppService(repo).project_detail(project_id)


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(project_id: UUID, body: ProjectPatch, repo: CurrentRepository):
    return await ProjectService(repo).update(project_id, **body.model_dump(exclude_unset=True))


@router.post("/{project_id}/income", response_model=IncomeOut, status_code=201)
async def income(project_id: UUID, body: IncomeCreate, repo: CurrentRepository):
    return await FinanceService(repo).income(project_id, body.amount, body.received_at, body.note)


@router.get("/{project_id}/income", response_model=Page[IncomeOut])
async def income_history(
    project_id: UUID, repo: CurrentRepository, offset: Offset = 0, limit: Limit = 30
):
    return await MiniAppService(repo).history(
        "income", project_id=project_id, offset=offset, limit=limit
    )


@router.get("/{project_id}/expenses", response_model=Page[ExpenseOut])
async def expense_history(
    project_id: UUID, repo: CurrentRepository, offset: Offset = 0, limit: Limit = 30
):
    return await MiniAppService(repo).history(
        "expenses", project_id=project_id, offset=offset, limit=limit
    )
