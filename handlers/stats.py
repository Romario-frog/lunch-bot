from aiogram import Router, F
from aiogram.types import Message

from handlers.register import request_access_keyboard
from services.role_service import has_access
from services.stats_service import format_current_lunches, format_today_stats

router = Router()


async def _deny_if_no_access(message: Message) -> bool:
    if has_access(message.from_user.id):
        return False
    await message.answer('У вас поки немає доступу. Подайте заявку адміну.', reply_markup=request_access_keyboard())
    return True


@router.message(F.text == '📋 Хто зараз на обіді')
async def current(message: Message):
    if await _deny_if_no_access(message):
        return
    await message.answer(format_current_lunches())


@router.message(F.text.in_({'🗓 Розклад обідів', '📊 Статистика'}))
async def stats(message: Message):
    if await _deny_if_no_access(message):
        return
    await message.answer(format_today_stats())
