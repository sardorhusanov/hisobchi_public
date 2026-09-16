from datetime import date, datetime, timedelta
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import Depends, Query

from app.config.settings import get_settings
from app.services.values import DomainError, month_bounds, parse_month


def selected_month(month: str | None = None) -> date:
    return (
        parse_month(month)
        if month
        else datetime.now(ZoneInfo(get_settings().timezone)).date().replace(day=1)
    )


Month = Annotated[date, Depends(selected_month)]
Offset = Annotated[int, Query(ge=0)]
Limit = Annotated[int, Query(ge=1, le=100)]


def selected_period(
    month: Month, start: date | None = None, end: date | None = None
) -> tuple[date, date]:
    if (start is None) != (end is None):
        raise DomainError("Boshlanish va tugash sanalarini kiriting.")
    if start is None:
        return month_bounds(month)
    if end == date.max or end < start or (end - start).days > 365:
        raise DomainError("Davr 1–366 kun bo'lishi kerak.")
    return start, end + timedelta(days=1)


Period = Annotated[tuple[date, date], Depends(selected_period)]
