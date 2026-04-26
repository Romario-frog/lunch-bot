from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def operator_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='🍽 Запланувати обід')],
            [KeyboardButton(text='🔁 Перенести обід'), KeyboardButton(text='❌ Скасувати обід')],
            [KeyboardButton(text='👀 Мій обід'), KeyboardButton(text='📋 Хто зараз на обіді')],
            [KeyboardButton(text='🗓 Розклад обідів'), KeyboardButton(text='ℹ️ Правила')],
        ],
        resize_keyboard=True,
        input_field_placeholder='Оберіть дію'
    )


def admin_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='🍽 Запланувати обід')],
            [KeyboardButton(text='🔁 Перенести обід'), KeyboardButton(text='❌ Скасувати обід')],
            [KeyboardButton(text='👀 Мій обід'), KeyboardButton(text='📋 Хто зараз на обіді')],
            [KeyboardButton(text='🗓 Розклад обідів'), KeyboardButton(text='👥 Користувачі')],
            [KeyboardButton(text='📝 Логи'), KeyboardButton(text='ℹ️ Правила')],
        ],
        resize_keyboard=True,
        input_field_placeholder='Адмін-меню'
    )
