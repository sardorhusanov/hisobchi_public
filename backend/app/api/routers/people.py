from uuid import UUID

from fastapi import APIRouter

from app.api.dependencies.filters import Month
from app.api.dependencies.workspace import CurrentRepository
from app.api.schemas.models import (
    PersonCreate,
    PersonDetail,
    PersonOut,
    PersonPatch,
    SalariesOut,
    SalaryOut,
)
from app.models import Role
from app.services.core import PeopleService, SalaryService
from app.services.miniapp import MiniAppService

router = APIRouter(tags=["People and salary"])


@router.get("/people", response_model=list[PersonOut])
async def people(repo: CurrentRepository, role: Role | None = None, active: bool = True):
    return await PeopleService(repo).list(role, active)


@router.post("/people", response_model=PersonOut, status_code=201)
async def create_person(body: PersonCreate, repo: CurrentRepository):
    return await PeopleService(repo).add(body.name, Role(body.role), body.monthly_salary)


@router.get("/people/{person_id}", response_model=PersonDetail)
async def person(person_id: UUID, month: Month, repo: CurrentRepository):
    return await MiniAppService(repo).person_detail(person_id, month)


@router.patch("/people/{person_id}", response_model=PersonOut)
async def update_person(person_id: UUID, body: PersonPatch, repo: CurrentRepository):
    return await PeopleService(repo).update(person_id, **body.model_dump(exclude_unset=True))


@router.get("/salaries", response_model=SalariesOut)
async def salaries(month: Month, repo: CurrentRepository, active: bool = False):
    return await MiniAppService(repo).salaries(month, active)


@router.get("/salaries/{worker_id}", response_model=SalaryOut)
async def salary(worker_id: UUID, month: Month, repo: CurrentRepository):
    return await SalaryService(repo).calculate_month(worker_id, month)
