from aiogram import Router, F
from aiogram.types import Message

from services.stats_service import format_current_lunches, format_today_stats

router = Router()


@router.message(F.text == '📋 Хто зараз на обіді')
async def current(message: Message):
    await message.answer(format_current_lunches())


@router.message(F.text == '📊 Статистика')
async def stats(message: Message):
    await message.answer(format_today_stats())
