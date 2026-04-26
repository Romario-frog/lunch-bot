from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def operator_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='🍽 Запланувати обід'), KeyboardButton(text='🔁 Перенести обід')],
            [KeyboardButton(text='❌ Скасувати обід'), KeyboardButton(text='👀 Мій обід')],
            [KeyboardButton(text='📋 Хто зараз на обіді'), KeyboardButton(text='📊 Статистика')],
            [KeyboardButton(text='ℹ️ Правила')],
        ],
        resize_keyboard=True,
        input_field_placeholder='Оберіть дію в меню'
    )


def admin_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='🍽 Запланувати обід'), KeyboardButton(text='🔁 Перенести обід')],
            [KeyboardButton(text='❌ Скасувати обід'), KeyboardButton(text='👀 Мій обід')],
            [KeyboardButton(text='📋 Хто зараз на обіді'), KeyboardButton(text='📊 Статистика')],
            [KeyboardButton(text='📝 Логи'), KeyboardButton(text='ℹ️ Правила')],
        ],
        resize_keyboard=True,
        input_field_placeholder='Адмін-меню'
    )
