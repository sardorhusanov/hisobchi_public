import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage, SimpleEventIsolation

from app.bot.handlers import make_router
from app.bot.middleware import DatabaseMiddleware
from app.config.settings import get_settings
from app.db.session import engine


async def main():
    settings = get_settings()
    if not settings.bot_token:
        raise SystemExit("Set BOT_TOKEN in backend/.env")
    logging.basicConfig(level=settings.log_level)
    dispatcher = Dispatcher(storage=MemoryStorage(), events_isolation=SimpleEventIsolation())
    router = make_router()
    router.message.outer_middleware(DatabaseMiddleware())
    router.callback_query.outer_middleware(DatabaseMiddleware())
    dispatcher.include_router(router)
    try:
        async with Bot(settings.bot_token) as bot:
            await dispatcher.start_polling(bot)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
