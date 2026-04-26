from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import settings
from keyboards.main_menu import admin_menu, operator_menu
from services.log_service import add_log
from services.role_service import add_pending, approve_operator, has_access, is_admin, reject_pending

router = Router()


def request_access_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📝 Подати заявку на доступ', callback_data='access_request')]
    ])


def approve_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='✅ Додати як оператора', callback_data=f'approve_operator:{user_id}'),
            InlineKeyboardButton(text='❌ Відхилити', callback_data=f'reject_user:{user_id}'),
        ]
    ])


@router.message(Command('id'))
async def show_id(message: Message):
    await message.answer(f'Ваш Telegram ID: {message.from_user.id}')


@router.callback_query(F.data == 'access_request')
async def request_access(callback: CallbackQuery, bot: Bot):
    user = callback.from_user
    if has_access(user.id):
        menu = admin_menu() if is_admin(user.id) else operator_menu()
        await callback.message.answer('✅ Доступ вже активний.', reply_markup=menu)
        await callback.answer()
        return

    add_pending(user.id, user.full_name, user.username)
    add_log('access_request', user.id, user.full_name, target_name=user.full_name)
    admin_text = (
        '🆕 Нова заявка на доступ\n\n'
        f'ПІБ: {user.full_name}\n'
        f'Username: @{user.username if user.username else "немає"}\n'
        f'Telegram ID: {user.id}\n\n'
        'Підтвердити користувача як оператора?'
    )
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(admin_id, admin_text, reply_markup=approve_keyboard(user.id))
        except Exception:
            pass
    await callback.message.answer('✅ Заявку відправлено адміну. Після підтвердження меню стане доступним.')
    await callback.answer()


@router.callback_query(F.data.startswith('approve_operator:'))
async def approve(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        await callback.answer('Доступно тільки адміну', show_alert=True)
        return
    user_id = int(callback.data.split(':', 1)[1])
    user = approve_operator(user_id)
    if not user:
        await callback.message.answer('Заявка вже оброблена або не знайдена.')
        await callback.answer()
        return
    add_log('approve_operator', callback.from_user.id, callback.from_user.full_name, target_name=user.get('full_name', ''))
    await callback.message.answer(f'✅ Користувача {user.get("full_name", user_id)} додано як оператора.')
    try:
        await bot.send_message(user_id, '✅ Ваш доступ підтверджено. Тепер ви можете користуватися меню.', reply_markup=operator_menu())
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith('reject_user:'))
async def reject(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        await callback.answer('Доступно тільки адміну', show_alert=True)
        return
    user_id = int(callback.data.split(':', 1)[1])
    user = reject_pending(user_id)
    add_log('reject_user', callback.from_user.id, callback.from_user.full_name, target_name=(user or {}).get('full_name', str(user_id)))
    await callback.message.answer('❌ Заявку відхилено.')
    try:
        await bot.send_message(user_id, '❌ Заявку на доступ відхилено. Зверніться до адміністратора.')
    except Exception:
        pass
    await callback.answer()
