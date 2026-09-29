import logging

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from app.bot.ui import safe_clear_keyboard
from app.db.session import Session
from app.repositories.core import Repository
from app.services.core import WorkspaceService
from app.services.values import DomainError

logger = logging.getLogger(__name__)


class DatabaseMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if not isinstance(event, (Message, CallbackQuery)) or not event.from_user:
            return
        message = event if isinstance(event, Message) else event.message
        if not message or message.chat.type != "private":
            if isinstance(event, CallbackQuery):
                await event.answer("Botni shaxsiy chatda oching.", show_alert=True)
            elif message:
                await message.answer("Botni shaxsiy chatda oching.")
            return
        try:
            async with Session() as session:
                workspace = await WorkspaceService(session).initialize(
                    event.from_user.id, event.from_user.first_name
                )
                data["repo"] = Repository(session, workspace.id)
                result = await handler(event, data)
                await session.commit()
                return result
        except (DomainError, ValueError) as exc:
            text = (
                str(exc)
                if isinstance(exc, DomainError)
                else "Ma'lumot noto'g'ri. Menyudan qayta tanlang."
            )
        except Exception:
            logger.exception("Bot operation failed", extra={"telegram_id": event.from_user.id})
            text = "Amal bajarilmadi. Qayta urinib ko'ring yoki bosh menyuga qayting."
        if isinstance(event, CallbackQuery):
            await safe_clear_keyboard(event.message)
            await event.answer(text, show_alert=True)
        else:
            await message.answer(text)
