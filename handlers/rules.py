from aiogram import Router, F
from aiogram.types import Message

router = Router()

RULES_TEXT = '''Правила обідів:
• Максимум 2 людини на один час.
• Оператор може керувати тільки своїм обідом.
• Адмін може керувати обідами всіх.
• Нагадування приходить в особисті повідомлення за 15 хвилин.
• Основні обіди зберігаються в Google Sheet на листі bot_data.'''


@router.message(F.text == 'ℹ️ Правила')
async def rules(message: Message):
    await message.answer(RULES_TEXT)
