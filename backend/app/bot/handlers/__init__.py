from aiogram import Router
from aiogram.types import CallbackQuery, Message

from app.bot.ui import safe_clear_keyboard

from . import attendance, common, flows, records, reports


def make_router():
    router = Router()
    for child in (common.router, attendance.router, reports.router, records.router, flows.router):
        router.include_router(child)
    fallback = Router()
    router.include_router(fallback)

    @fallback.callback_query()
    async def unknown_callback(query: CallbackQuery):
        await safe_clear_keyboard(query.message)
        await query.answer("Tugma eskirgan. Bosh menyudan qayta boshlang.", show_alert=True)

    @fallback.message()
    async def unknown_message(message: Message):
        await message.answer("Menyu tugmalaridan foydalaning yoki 🏠 Bosh menyu tugmasini bosing.")

    return router
