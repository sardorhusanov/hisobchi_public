import re
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal


class DomainError(ValueError):
    pass


def money_input(text: str) -> Decimal:
    text = text.strip()
    if not re.fullmatch(
        r"(?:[0-9]+|[0-9]{1,3}(?: [0-9]{3})+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]{1,2})?", text
    ):
        raise DomainError("Summani raqam bilan kiriting: 6 000 000")
    value = Decimal(text.replace(" ", "").replace(",", ""))
    if not Decimal(0) < value <= Decimal("9999999999999999.99"):
        raise DomainError("Summa musbat va 10 000 000 000 000 000 dan kichik bo'lishi kerak.")
    return value


def money(value: Decimal) -> str:
    return f"{value:,.2f}".replace(",", " ").removesuffix(".00") + " so'm"


def month_bounds(month: date) -> tuple[date, date]:
    start = month.replace(day=1)
    if start.year == 9999 and start.month == 12:
        raise DomainError("Bu oy qo'llab-quvvatlanmaydi. Boshqa oyni tanlang.")
    end = date(start.year + (start.month == 12), start.month % 12 + 1, 1)
    return start, end


def parse_month(text: str) -> date:
    try:
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}", text):
            raise ValueError
        return date.fromisoformat(text + "-01")
    except ValueError:
        raise DomainError("Oy formati: 2026-09") from None


def parse_date(text: str) -> date:
    try:
        from datetime import datetime

        return datetime.strptime(text, "%d.%m.%Y").date()
    except ValueError:
        raise DomainError("Sana formati: 15.09.2026") from None


@dataclass(frozen=True)
class SalaryResult:
    monthly_salary: Decimal
    daily_rate: Decimal
    worked_days: Decimal
    gross: Decimal
    advances: Decimal
    remaining: Decimal


def calculate_salary(monthly: Decimal, days: Decimal, advances: Decimal) -> SalaryResult:
    daily = monthly / Decimal(30)
    gross = (monthly * days / Decimal(30)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return SalaryResult(monthly, daily, days, gross, advances, gross - advances)


@dataclass(frozen=True)
class ProjectTotals:
    income: Decimal
    expenses: Decimal

    @property
    def balance(self) -> Decimal:
        return self.income - self.expenses
