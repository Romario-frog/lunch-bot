from aiogram import Router, F
from aiogram.types import Message

from services.log_service import get_last_logs
from services.role_service import is_admin

router = Router()


@router.message(F.text == '📝 Логи')
async def logs(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer('Цей розділ доступний тільки адміну.')
        return
    items = get_last_logs(15)
    if not items:
        await message.answer('Логів поки немає.')
        return
    lines = ['Останні дії:']
    for item in items:
        lines.append(f"• {item.get('created_at')} | {item.get('actor_name')} | {item.get('action')} | {item.get('target_name')}")
    await message.answer('\n'.join(lines))
