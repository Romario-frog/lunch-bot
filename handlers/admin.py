from aiogram import Router, F
from aiogram.types import Message

from services.log_service import get_last_logs
from services.role_service import is_admin, list_users

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


@router.message(F.text == '👥 Користувачі')
async def users(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer('Цей розділ доступний тільки адміну.')
        return
    data = list_users()
    lines = ['Користувачі:']
    lines.append(f"Адміни: {len(data.get('admins', {}))}")
    for uid, u in data.get('admins', {}).items():
        lines.append(f"• admin | {u.get('full_name') or u.get('name', '')} | {uid}")
    lines.append(f"Оператори: {len(data.get('operators', {}))}")
    for uid, u in data.get('operators', {}).items():
        lines.append(f"• operator | {u.get('full_name') or u.get('name', '')} | {uid}")
    lines.append(f"Заявки: {len(data.get('pending', {}))}")
    for uid, u in data.get('pending', {}).items():
        lines.append(f"• pending | {u.get('full_name') or u.get('name', '')} | {uid}")
    await message.answer('\n'.join(lines))
