from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from handlers.register import request_access_keyboard
from keyboards.main_menu import admin_menu, operator_menu
from services.role_service import has_access, is_admin

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    user = message.from_user
    if not has_access(user.id):
        await message.answer(
            'Привіт! У вас поки немає доступу до Lunch Bot.\n\n'
            'Натисніть кнопку нижче, щоб подати заявку адміну.',
            reply_markup=request_access_keyboard(),
        )
        return

    menu = admin_menu() if is_admin(user.id) else operator_menu()
    await message.answer('Привіт! Я Lunch Bot. Оберіть потрібну дію в меню нижче.', reply_markup=menu)
