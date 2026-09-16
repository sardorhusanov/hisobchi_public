from uuid import UUID

from fastapi import APIRouter

from app.api.dependencies.filters import Month, Period
from app.api.dependencies.workspace import CurrentRepository
from app.api.schemas.models import Dashboard, FinanceReport, IdentityOut, ProjectSummary
from app.services.miniapp import MiniAppService

router = APIRouter(tags=["Overview"])


@router.post("/auth/telegram", response_model=IdentityOut)
async def authenticate(repo: CurrentRepository):
    return await MiniAppService(repo).identity()


@router.get("/me", response_model=IdentityOut)
async def me(repo: CurrentRepository):
    return await MiniAppService(repo).identity()


@router.get("/dashboard", response_model=Dashboard)
async def dashboard(month: Month, repo: CurrentRepository):
    return await MiniAppService(repo).dashboard(month)


@router.get("/reports/monthly", response_model=FinanceReport)
async def monthly_report(period: Period, repo: CurrentRepository):
    return await MiniAppService(repo).finance_report(*period)


@router.get("/reports/projects/{project_id}", response_model=ProjectSummary)
async def project_report(project_id: UUID, repo: CurrentRepository):
    return await MiniAppService(repo).project_detail(project_id)
