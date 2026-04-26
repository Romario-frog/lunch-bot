from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def lunch_slots_keyboard() -> ReplyKeyboardMarkup:
    """Оператор вводить час вручну, щоб меню не забивалося десятками кнопок."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='⬅️ Назад')]],
        resize_keyboard=True,
        input_field_placeholder='Напишіть час, наприклад 17:15'
    )
