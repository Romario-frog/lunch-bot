from datetime import date

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from services.booking_service import create_booking, move_booking, cancel_booking, find_user_booking

router = Router()


class BookingStates(StatesGroup):
    waiting_book_time = State()
    waiting_move_time = State()


def _valid_time(text: str) -> bool:
    parts = text.strip().split(':')
    if len(parts) != 2:
        return False
    try:
        h, m = int(parts[0]), int(parts[1])
    except ValueError:
        return False
    return 0 <= h <= 23 and 0 <= m <= 59


@router.message(F.text == '🍽 Запланувати обід')
async def book_start(message: Message, state: FSMContext):
    await state.set_state(BookingStates.waiting_book_time)
    await message.answer('Введіть час початку обіду у форматі HH:MM. Наприклад: 15:00')


@router.message(BookingStates.waiting_book_time)
async def book_finish(message: Message, state: FSMContext):
    start_time = message.text.strip()
    if not _valid_time(start_time):
        await message.answer('Неправильний формат. Напишіть так: 15:00')
        return
    user = message.from_user
    ok, text = create_booking(
        day=date.today(),
        user_id=user.id,
        username=user.username or '',
        full_name=user.full_name,
        start_time=start_time,
        actor_id=user.id,
        actor_name=user.full_name,
    )
    await state.clear()
    await message.answer(text)


@router.message(F.text == '🔁 Перенести обід')
async def move_start(message: Message, state: FSMContext):
    await state.set_state(BookingStates.waiting_move_time)
    await message.answer('Введіть новий час обіду у форматі HH:MM. Наприклад: 16:15')


@router.message(BookingStates.waiting_move_time)
async def move_finish(message: Message, state: FSMContext):
    start_time = message.text.strip()
    if not _valid_time(start_time):
        await message.answer('Неправильний формат. Напишіть так: 16:15')
        return
    user = message.from_user
    ok, text = move_booking(
        day=date.today(),
        user_id=user.id,
        username=user.username or '',
        full_name=user.full_name,
        new_start_time=start_time,
        actor_id=user.id,
        actor_name=user.full_name,
    )
    await state.clear()
    await message.answer(text)


@router.message(F.text == '❌ Скасувати обід')
async def cancel(message: Message):
    user = message.from_user
    ok, text = cancel_booking(date.today(), user.id, user.id, user.full_name)
    await message.answer(text)


@router.message(F.text == '👀 Мій обід')
async def my_lunch(message: Message):
    user = message.from_user
    booking = find_user_booking(date.today(), user.id)
    if not booking:
        await message.answer('У вас немає активного обіду на сьогодні.')
        return
    await message.answer(f"Ваш обід сьогодні: {booking.get('start_time')}–{booking.get('end_time')}")
