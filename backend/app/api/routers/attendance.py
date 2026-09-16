from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter

from app.api.dependencies.filters import Month
from app.api.dependencies.workspace import CurrentRepository
from app.api.schemas.models import AttendanceBatch, AttendanceDay, AttendanceMonth, AttendanceReport
from app.services.miniapp import MiniAppService

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.get("", response_model=AttendanceDay)
async def attendance(repo: CurrentRepository, date: date):
    return await MiniAppService(repo).daily_attendance(date)


@router.put("", response_model=AttendanceDay)
async def save_attendance(body: AttendanceBatch, repo: CurrentRepository):
    return await MiniAppService(repo).batch_attendance(
        body.date,
        [(entry.person_id, Decimal(entry.value) if entry.value else None) for entry in body.items],
    )


@router.get("/monthly", response_model=AttendanceMonth)
async def monthly(person_id: UUID, month: Month, repo: CurrentRepository):
    return await MiniAppService(repo).monthly_attendance(person_id, month)


@router.get("/report", response_model=AttendanceReport)
async def report(month: Month, repo: CurrentRepository):
    return await MiniAppService(repo).attendance_report(month)
