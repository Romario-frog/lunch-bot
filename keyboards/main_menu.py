from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu(role: str = "operator") -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text='🍽 Запланувати обід')],
        [KeyboardButton(text='🔁 Перенести обід'), KeyboardButton(text='❌ Скасувати обід')],
        [KeyboardButton(text='👀 Мій обід'), KeyboardButton(text='📋 Хто зараз на обіді')],
        [KeyboardButton(text='🗓 Розклад обідів'), KeyboardButton(text='ℹ️ Правила')],
    ]

    if role == "admin":
        keyboard.insert(3, [KeyboardButton(text='👥 Користувачі')])
        keyboard.append([KeyboardButton(text='📝 Логи')])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder='Адмін-меню' if role == "admin" else 'Оберіть дію'
    )


def operator_menu() -> ReplyKeyboardMarkup:
    return get_main_menu("operator")


def admin_menu() -> ReplyKeyboardMarkup:
    return get_main_menu("admin")