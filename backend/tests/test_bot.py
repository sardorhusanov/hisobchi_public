from contextlib import asynccontextmanager
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from aiogram import Bot, Dispatcher
from aiogram.client.session.base import BaseSession
from aiogram.fsm.storage.memory import SimpleEventIsolation
from aiogram.methods import (
    AnswerCallbackQuery,
    EditMessageReplyMarkup,
    EditMessageText,
    SendMessage,
)
from aiogram.types import Chat, Message, Update, User

from app.bot.handlers import make_router
from app.bot.middleware import DatabaseMiddleware
from app.bot.ui import Action, cancel_keyboard, main_keyboard, today
from app.models import Role
from app.repositories.core import Repository
from app.services.core import PeopleService, ProjectService, SalaryService, WorkspaceService


class TelegramSession(BaseSession):
    def __init__(self):
        super().__init__()
        self.calls = []

    async def close(self):
        pass

    async def make_request(self, bot, method, timeout=None):
        self.calls.append(method)
        if isinstance(method, AnswerCallbackQuery):
            return True
        if isinstance(method, EditMessageReplyMarkup):
            return Message(
                message_id=method.message_id,
                date=datetime.now(UTC),
                chat=Chat(id=int(method.chat_id), type="private"),
                reply_markup=method.reply_markup,
            )
        if isinstance(method, (SendMessage, EditMessageText)):
            return Message(
                message_id=len(self.calls),
                date=datetime.now(UTC),
                chat=Chat(id=int(method.chat_id), type="private"),
                text=method.text,
                reply_markup=method.reply_markup if isinstance(method, EditMessageText) else None,
            )
        raise AssertionError(type(method))

    async def stream_content(self, *args, **kwargs):
        yield b""


def test_keyboard_lifecycle():
    main = main_keyboard()
    assert main.one_time_keyboard is True
    assert main.resize_keyboard is True

    cancel = cancel_keyboard()
    kinds = {
        Action.unpack(button.callback_data).kind
        for row in cancel.inline_keyboard
        for button in row
        if button.callback_data
    }
    assert kinds == {"home"}


@pytest.mark.skipif(
    not __import__("os").getenv("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL is not configured"
)
async def test_bot_end_to_end(context, monkeypatch):
    session, _ = context

    @asynccontextmanager
    async def factory():
        yield session

    monkeypatch.setattr("app.bot.middleware.Session", factory)
    from app.config.settings import Settings

    monkeypatch.setattr(
        "app.bot.handlers.common.get_settings",
        lambda: Settings(_env_file=None, mini_app_url="https://app.example"),
    )
    dispatcher = Dispatcher(events_isolation=SimpleEventIsolation())
    router = make_router()
    router.message.outer_middleware(DatabaseMiddleware())
    router.callback_query.outer_middleware(DatabaseMiddleware())
    dispatcher.include_router(router)
    telegram = TelegramSession()
    bot = Bot("123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi", session=telegram)
    user_id = uuid4().int % (2**40)
    user = User(id=user_id, is_bot=False, first_name="Sardor")
    update_id = 0

    async def send(text=None, kind=None, id="", value=""):
        nonlocal update_id
        update_id += 1
        message = Message(
            message_id=update_id,
            date=datetime.now(UTC),
            chat=Chat(id=user_id, type="private"),
            from_user=user,
            text=text,
        )
        if kind:
            payload = dict(
                callback_query={
                    "id": str(update_id),
                    "from": user.model_dump(),
                    "chat_instance": "test",
                    "message": message.model_dump(),
                    "data": Action(kind=kind, id=id, value=value).pack(),
                }
            )
        else:
            payload = dict(message=message)
        await dispatcher.feed_update(bot, Update(update_id=update_id, **payload))

    def last_save():
        for method in reversed(telegram.calls):
            keyboard = getattr(method, "reply_markup", None)
            if hasattr(keyboard, "inline_keyboard"):
                for row in keyboard.inline_keyboard:
                    for button in row:
                        if button.callback_data and button.callback_data.startswith("a:save:"):
                            return Action.unpack(button.callback_data).id
        raise AssertionError("No confirmation")

    await send("/start")
    assert any(
        getattr(button, "web_app", None) and button.web_app.url == "https://app.example"
        for call in telegram.calls
        for row in getattr(getattr(call, "reply_markup", None), "inline_keyboard", [])
        for button in row
    )
    await send("👷 Ishchilar")
    await send(kind="addperson", value="WORKER")
    await send("Ali")
    await send("6 000 000")
    nonce = last_save()
    await send(kind="save", id=nonce)
    await send(kind="save", id=nonce)  # Double tap must not create a duplicate.
    workspace = await WorkspaceService(session).initialize(user_id, "Sardor")
    repo = Repository(session, workspace.id)
    workers = await PeopleService(repo).list(Role.WORKER)
    assert len(workers) == 1
    worker = workers[0]
    await send(kind="today")
    attendance_labels = [
        button.text
        for call in telegram.calls
        for row in getattr(getattr(call, "reply_markup", None), "inline_keyboard", [])
        for button in row
    ]
    assert any(label.startswith("👷 Ishchi · Ali:") for label in attendance_labels)
    assert any(label.startswith("👤 Egasi ·") for label in attendance_labels)
    await send(kind="att", id=worker.id.hex, value=f"{today():%Y%m%d}5")
    await send(kind="addadvance", id=worker.id.hex)
    await send("50 000")
    await send(kind="editmonth")
    await send(kind="flowmonth")
    await send(kind="editday")
    await send(kind="flowday")
    await send(kind="editnote")
    await send(kind="skipnote")
    await send(kind="save", id=last_save())
    salary = await SalaryService(repo).calculate_month(worker.id, today())
    assert salary.remaining == Decimal(50000)
    await send(kind="salary", id=worker.id.hex)
    await send(kind="currentreport")
    assert any("Qolgan: 50 000" in (getattr(c, "text", "") or "") for c in telegram.calls)
    await send(kind="addproject")
    await send("Test project")
    await send(kind="save", id=last_save())
    assert len(await ProjectService(repo).list()) == 1
    project = (await ProjectService(repo).list())[0]
    await send(kind="income", id=project.id.hex)
    await send("1 000 000")
    await send(kind="save", id=last_save())
    await send(kind="expense", id=project.id.hex)
    await send("200 000")
    await send(kind="category", value="BUSINESS")
    await send(kind="save", id=last_save())
    totals = await ProjectService(repo).totals(project.id)
    assert totals.balance == Decimal("800000")
    await send(kind="addperson", value="PARTNER")
    await send("Hamkor")
    await send(kind="save", id=last_save())
    partner = (await PeopleService(repo).list(Role.PARTNER))[0]
    await send(kind="expense")
    await send("100 000")
    await send(kind="category", value="PARTNER")
    await send(kind="beneficiary", id=partner.id.hex)
    await send(kind="save", id=last_save())
    await send(kind="report", value="finance")
    await send(kind="currentreport")
    assert any("Hamkor olgan: 100 000" in (getattr(c, "text", "") or "") for c in telegram.calls)
    await send(kind="date")
    await send("15.09.2025")
    attendance_labels = [
        button.text
        for call in telegram.calls
        for row in getattr(getattr(call, "reply_markup", None), "inline_keyboard", [])
        for button in row
    ]
    assert any(label.startswith("🤝 Hamkor · Hamkor:") for label in attendance_labels)
    await send(kind="all", value="20250915")
    await send(kind="personatt", id=partner.id.hex)
    await send("2025-09")
    assert any("Jami: 1.0 kun" in (getattr(c, "text", "") or "") for c in telegram.calls)
    await send(kind="addperson", value="WORKER")
    await send("Cancelled")
    await send("🏠 Bosh menyu")
    assert len(await PeopleService(repo).list(Role.WORKER)) == 1
    assert not any("Amal bajarilmadi" in (getattr(c, "text", "") or "") for c in telegram.calls)
    await dispatcher.storage.close()
    await bot.session.close()
