from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards.main_menu import admin_menu, operator_menu
from services.role_service import is_admin, remember_user

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    user = message.from_user
    remember_user(user.id, user.full_name, user.username)
    menu = admin_menu() if is_admin(user.id) else operator_menu()
    await message.answer(
        'Привіт! Я бот для обідів. Оберіть потрібну дію в меню нижче.',
        reply_markup=menu,
    )
