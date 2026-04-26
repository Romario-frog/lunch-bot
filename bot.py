import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from handlers import admin, booking, rules, start, stats
from services.google_sheet_service import ensure_sheets
from services.reminder_service import setup_scheduler


async def main():
    logging.basicConfig(level=logging.INFO)
    if not settings.bot_token:
        raise RuntimeError('BOT_TOKEN is empty. Check .env or Render Environment Variables.')
    ensure_sheets()
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start.router)
    dp.include_router(booking.router)
    dp.include_router(stats.router)
    dp.include_router(admin.router)
    dp.include_router(rules.router)
    setup_scheduler(bot)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
