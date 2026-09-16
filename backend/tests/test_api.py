import os
import time
from datetime import date
from decimal import Decimal
from uuid import uuid4

import httpx
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker
from test_auth import TOKEN, signed_data

from app.api.main import create_app
from app.config.settings import Settings, get_settings
from app.models import Role
from app.repositories.core import Repository
from app.services.core import AdvanceService, PeopleService, ProjectService, WorkspaceService

pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL is not configured"
)


async def test_api_workflows_and_isolation(context, monkeypatch):
    session, _ = context
    factory = async_sessionmaker(
        bind=session.bind, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )
    monkeypatch.setattr("app.api.dependencies.workspace.Session", factory)
    application = create_app()
    application.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None, bot_token=TOKEN
    )
    user_id = uuid4().int % (2**40)
    auth = {"Authorization": "tma " + signed_data(user_id, int(time.time()))}
    other = await WorkspaceService(session).initialize(uuid4().int % (2**40), "Other")
    other_repo = Repository(session, other.id)
    foreign_person = await PeopleService(other_repo).add(
        "Private worker", Role.WORKER, Decimal("1000")
    )
    foreign_project = await ProjectService(other_repo).add("Private project")
    foreign_advance = await AdvanceService(other_repo).add(
        foreign_person.id, Decimal("100"), date(2026, 9, 15), date(2026, 9, 1)
    )
    transport = httpx.ASGITransport(app=application, client=("127.0.0.1", 1234))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.get("/api/v1/dashboard")).status_code == 401
        assert (
            await client.get("/api/v1/dashboard", headers={"Authorization": "tma altered"})
        ).status_code == 401
        assert (
            await client.get("/api/v1/dashboard", headers={"X-Dev-Auth": "1"})
        ).status_code == 401
        client.headers.update(auth)
        me = (await client.post("/api/v1/auth/telegram")).json()
        assert me["telegram_user_id"] == user_id
        assert me["owner"]["role"] == "OWNER"
        worker_response = await client.post(
            "/api/v1/people", json={"name": "Ali", "role": "WORKER", "monthly_salary": "6 000 000"}
        )
        assert worker_response.status_code == 201, worker_response.text
        worker = worker_response.json()
        assert worker["monthly_salary"] == "6000000"
        assert (
            await client.post("/api/v1/people", json={"name": "Bad", "role": "OWNER"})
        ).status_code == 422
        assert (
            await client.post(
                "/api/v1/people", json={"name": "Bad", "role": "WORKER", "monthly_salary": "0"}
            )
        ).status_code == 422
        assert (
            await client.post(
                "/api/v1/people", json={"name": "Bad", "role": "PARTNER", "monthly_salary": "100"}
            )
        ).status_code == 422
        partner = (
            await client.post("/api/v1/people", json={"name": "Hamkor", "role": "PARTNER"})
        ).json()
        attendance = await client.put(
            "/api/v1/attendance",
            json={
                "date": "2026-09-15",
                "items": [
                    {"person_id": worker["id"], "value": "0.5"},
                    {"person_id": partner["id"], "value": "1"},
                ],
            },
        )
        assert attendance.status_code == 200, attendance.text
        assert (
            await client.put(
                "/api/v1/attendance",
                json={"date": "2026-09-15", "items": [{"person_id": worker["id"], "value": "0.2"}]},
            )
        ).status_code == 422
        monthly = (
            await client.get(
                "/api/v1/attendance/monthly", params={"person_id": worker["id"], "month": "2026-09"}
            )
        ).json()
        assert monthly["worked_days"] == "0.5"
        assert monthly["half_days"] == 1
        project_response = await client.post(
            "/api/v1/projects", json={"name": "Project A", "description": "Test"}
        )
        assert project_response.status_code == 201, project_response.text
        project = project_response.json()
        advance = await client.post(
            "/api/v1/advances",
            json={
                "worker_id": worker["id"],
                "amount": "50000",
                "paid_at": "2026-09-15",
                "salary_month": "2026-09-01",
                "project_id": project["id"],
            },
        )
        assert advance.status_code == 201, advance.text
        salaries = (await client.get("/api/v1/salaries?month=2026-09")).json()
        assert salaries["gross"] == "100000.00"
        assert salaries["remaining"] == "50000.00"
        assert len(salaries["items"]) == 1
        for amount in ["1000000", "400000"]:
            income = await client.post(
                f"/api/v1/projects/{project['id']}/income",
                json={"amount": amount, "received_at": "2026-09-15"},
            )
            assert income.status_code == 201, income.text
        for category, amount, person_id in [
            ("BUSINESS", "200000", None),
            ("OWNER", "100000", me["owner"]["id"]),
            ("PARTNER", "50000", partner["id"]),
        ]:
            expense = await client.post(
                "/api/v1/expenses",
                json={
                    "amount": amount,
                    "expense_date": "2026-09-15",
                    "category": category,
                    "project_id": project["id"],
                    "beneficiary_person_id": person_id,
                },
            )
            assert expense.status_code == 201, expense.text
        summary = (await client.get("/api/v1/finance/summary?month=2026-09")).json()
        assert summary["summary"]["income"] == "1400000.00"
        assert summary["summary"]["business_expenses"] == "200000.00"
        assert summary["summary"]["owner_withdrawals"] == "100000.00"
        assert summary["summary"]["partner_withdrawals"] == "50000.00"
        assert summary["summary"]["advances"] == "50000.00"
        assert summary["summary"]["net_cash_flow"] == "1000000.00"
        assert len(summary["chart"]) == 30
        assert summary["chart"][14]["income"] == "1400000.00"
        report = (await client.get(f"/api/v1/reports/projects/{project['id']}")).json()
        assert report["balance"] == "1050000.00"  # Advances are not project expenses.
        dashboard = (await client.get("/api/v1/dashboard?month=2026-09")).json()
        assert dashboard["summary"] == summary["summary"]
        assert dashboard["attendance"]["total_people"] == 3
        assert dashboard["projects"][0]["project"]["id"] == project["id"]
        history = (await client.get(f"/api/v1/projects/{project['id']}/income?limit=1")).json()
        assert history["total"] == 2 and len(history["items"]) == 1
        assert history["amount"] == "1400000.00"
        assert (
            await client.get("/api/v1/finance/summary?start=2020-01-01&end=2026-01-01")
        ).status_code == 422
        assert (
            await client.patch(f"/api/v1/people/{worker['id']}", json={"monthly_salary": "9000000"})
        ).status_code == 200
        salary = (await client.get(f"/api/v1/salaries/{worker['id']}?month=2026-09")).json()
        assert salary["gross"] == "150000.00"
        for path in [
            f"/people/{foreign_person.id}",
            f"/projects/{foreign_project.id}",
            f"/salaries/{foreign_person.id}",
            f"/reports/projects/{foreign_project.id}",
            f"/projects/{foreign_project.id}/income",
            f"/projects/{foreign_project.id}/expenses",
            f"/attendance/monthly?person_id={foreign_person.id}",
            f"/advances?worker_id={foreign_person.id}",
        ]:
            response = await client.get("/api/v1" + path)
            assert response.status_code in (404, 422), (path, response.text)
            assert "Private" not in response.text
        assert (await client.delete(f"/api/v1/advances/{foreign_advance.id}")).status_code == 422
        bad_advance = await client.post(
            "/api/v1/advances",
            json={
                "worker_id": worker["id"],
                "amount": "100",
                "paid_at": "2026-09-15",
                "salary_month": "2026-09-01",
                "project_id": str(foreign_project.id),
            },
        )
        assert bad_advance.status_code == 422
        bad_expense = await client.post(
            "/api/v1/expenses",
            json={
                "amount": "100",
                "expense_date": "2026-09-15",
                "category": "OWNER",
                "beneficiary_person_id": str(foreign_person.id),
            },
        )
        assert bad_expense.status_code == 422
        assert (
            await client.patch(f"/api/v1/people/{foreign_person.id}", json={"name": "Stolen"})
        ).status_code == 422
        assert (
            await client.post(
                f"/api/v1/projects/{foreign_project.id}/income",
                json={"amount": "100", "received_at": "2026-09-15"},
            )
        ).status_code == 422
        # The whole attendance batch rolls back if any ID is outside the workspace.
        response = await client.put(
            "/api/v1/attendance",
            json={
                "date": "2026-09-15",
                "items": [
                    {"person_id": worker["id"], "value": "1"},
                    {"person_id": str(foreign_person.id), "value": "1"},
                ],
            },
        )
        assert response.status_code == 422
        month = (
            await client.get(
                "/api/v1/attendance/monthly", params={"person_id": worker["id"], "month": "2026-09"}
            )
        ).json()
        assert month["worked_days"] == "0.5"
        assert (await client.delete("/api/v1/advances/" + advance.json()["id"])).status_code == 204
        assert (
            await client.patch(f"/api/v1/projects/{project['id']}", json={"status": "COMPLETED"})
        ).status_code == 200
        assert (
            await client.post(
                f"/api/v1/projects/{project['id']}/income",
                json={"amount": "100", "received_at": "2026-09-15"},
            )
        ).status_code == 422
        assert (
            await client.patch(f"/api/v1/people/{worker['id']}", json={"is_active": False})
        ).status_code == 200
        assert len((await client.get("/api/v1/people?role=WORKER")).json()) == 0
