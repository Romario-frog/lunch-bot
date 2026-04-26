from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def duration_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='15 хв'), KeyboardButton(text='30 хв'), KeyboardButton(text='45 хв')],
            [KeyboardButton(text='⬅️ Назад')],
        ],
        resize_keyboard=True,
        input_field_placeholder='Оберіть тривалість'
    )
