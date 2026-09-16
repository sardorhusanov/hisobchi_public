from datetime import date
from decimal import Decimal as D

import pytest

from app.services.values import (
    DomainError,
    ProjectTotals,
    calculate_salary,
    money_input,
    month_bounds,
    parse_month,
)


@pytest.mark.parametrize(
    ("days", "advances", "gross", "remaining"),
    [
        ("1", "0", "200000", "200000"),
        ("0.5", "0", "100000", "100000"),
        ("18.5", "1000000", "3700000", "2700000"),
        ("0", "0", "0", "0"),
        ("0", "500000", "0", "-500000"),
        ("1", "500000", "200000", "-300000"),
        ("31", "0", "6200000", "6200000"),
    ],
)
def test_salary(days, advances, gross, remaining):
    result = calculate_salary(D(6000000), D(days), D(advances))
    assert result.daily_rate == D(200000)
    assert result.gross == D(gross)
    assert result.remaining == D(remaining)


def test_multiple_entries_and_advances():
    result = calculate_salary(
        D(6000000), sum(map(D, ["1", ".5", "1"])), sum(map(D, ["100000", "150000"]))
    )
    assert result.worked_days == D("2.5")
    assert result.gross == D(500000)
    assert result.remaining == D(250000)


def test_round_only_final_gross():
    assert calculate_salary(D(100), D(30), D(0)).gross == D("100.00")
    assert calculate_salary(D(100), D(1), D(0)).gross == D("3.33")


def test_project_totals():
    result = ProjectTotals(sum(map(D, ["10000000", "4000000"])), sum(map(D, ["2000000", "500000"])))
    assert result.income == D(14000000)
    assert result.expenses == D(2500000)
    assert result.balance == D(11500000)


@pytest.mark.parametrize("text", ["6000000", "6 000 000", "6,000,000", "6000000.00"])
def test_amount_input(text):
    assert money_input(text) == D(6000000)


@pytest.mark.parametrize(
    "text",
    ["0", "-1", "NaN", "Infinity", "1e6", "1,5", "6 00 000", "1.001", "", "10000000000000000"],
)
def test_invalid_amount_input(text):
    with pytest.raises(DomainError):
        money_input(text)


def test_month_bounds():
    assert month_bounds(date(2026, 12, 15)) == (date(2026, 12, 1), date(2027, 1, 1))
    assert parse_month("2024-02") == date(2024, 2, 1)
