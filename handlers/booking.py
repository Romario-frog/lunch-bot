from datetime import date

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from handlers.register import request_access_keyboard
from keyboards.main_menu import admin_menu, operator_menu
from keyboards.slots_keyboard import lunch_slots_keyboard
from keyboards.duration_keyboard import duration_keyboard
from services.booking_service import create_booking, move_booking, cancel_booking, find_user_booking, validate_lunch_start, find_user_schedule_bookings, cancel_schedule_booking
from services.role_service import has_access, is_admin, display_name

router = Router()


class BookingStates(StatesGroup):
    waiting_book_time = State()
    waiting_book_duration = State()
    waiting_move_time = State()
    waiting_move_duration = State()
    waiting_cancel_choice = State()


def cancel_confirm_keyboard(bookings: list[dict]) -> ReplyKeyboardMarkup:
    keyboard = []
    for i, booking in enumerate(bookings, start=1):
        start = booking.get('start_time', '')
        end = booking.get('end_time', '')
        keyboard.append([KeyboardButton(text=f'✅ {i}) Скасувати {start}–{end}')])
    keyboard.append([KeyboardButton(text='⬅️ Назад')])
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder='Оберіть обід для скасування'
    )

def _menu_for(user_id: int):
    return admin_menu() if is_admin(user_id) else operator_menu()


async def _deny_if_no_access(message: Message) -> bool:
    if has_access(message.from_user.id):
        return False
    await message.answer('У вас поки немає доступу. Подайте заявку адміну.', reply_markup=request_access_keyboard())
    return True


def _parse_duration(text: str) -> int | None:
    clean = text.strip().lower().replace('хвилин', '').replace('хв', '').replace('мин', '').strip()
    if clean in {'15', '30', '45'}:
        return int(clean)
    return None


@router.message(F.text == '⬅️ Назад')
async def back_to_menu(message: Message, state: FSMContext):
    await state.clear()
    if await _deny_if_no_access(message):
        return
    await message.answer('Повернув у головне меню.', reply_markup=_menu_for(message.from_user.id))


@router.message(F.text == '🍽 Запланувати обід')
async def book_start(message: Message, state: FSMContext):
    if await _deny_if_no_access(message):
        return
    await state.set_state(BookingStates.waiting_book_time)
    await message.answer(
        'Спочатку оберіть час початку обіду кнопкою або напишіть вручну у форматі HH:MM.\n'
        'Після цього бот запропонує тривалість: 15 / 30 / 45 хв.\n'
        'Останній кінець обіду — 20:00.',
        reply_markup=lunch_slots_keyboard(),
    )


@router.message(BookingStates.waiting_book_time)
async def book_time(message: Message, state: FSMContext):
    if await _deny_if_no_access(message):
        await state.clear()
        return
    start_time = message.text.strip()
    valid, error = validate_lunch_start(date.today(), start_time, 15)
    if not valid:
        await message.answer(error, reply_markup=lunch_slots_keyboard())
        return
    await state.update_data(start_time=start_time)
    await state.set_state(BookingStates.waiting_book_duration)
    await message.answer(f'Час початку: {start_time}. Тепер оберіть тривалість обіду:', reply_markup=duration_keyboard())


@router.message(BookingStates.waiting_book_duration)
async def book_finish(message: Message, state: FSMContext):
    if await _deny_if_no_access(message):
        await state.clear()
        return
    duration = _parse_duration(message.text)
    if duration is None:
        await message.answer('Оберіть тривалість кнопкою: 15 хв, 30 хв або 45 хв.', reply_markup=duration_keyboard())
        return
    data = await state.get_data()
    start_time = data.get('start_time')
    valid, error = validate_lunch_start(date.today(), start_time, duration)
    if not valid:
        await state.set_state(BookingStates.waiting_book_time)
        await message.answer(error + '\nОберіть інший час початку.', reply_markup=lunch_slots_keyboard())
        return
    user = message.from_user
    ok, text = create_booking(
        day=date.today(),
        user_id=user.id,
        username=user.username or '',
        full_name=display_name(user.id, user.full_name),
        start_time=start_time,
        duration_minutes=duration,
        actor_id=user.id,
        actor_name=display_name(user.id, user.full_name),
    )
    await state.clear()
    await message.answer(text, reply_markup=_menu_for(user.id))


@router.message(F.text == '🔁 Перенести обід')
async def move_start(message: Message, state: FSMContext):
    if await _deny_if_no_access(message):
        return
    await state.set_state(BookingStates.waiting_move_time)
    await message.answer(
        'Оберіть новий час початку обіду кнопкою або напишіть вручну у форматі HH:MM.\n'
        'Після цього оберіть тривалість: 15 / 30 / 45 хв.',
        reply_markup=lunch_slots_keyboard(),
    )


@router.message(BookingStates.waiting_move_time)
async def move_time(message: Message, state: FSMContext):
    if await _deny_if_no_access(message):
        await state.clear()
        return
    start_time = message.text.strip()
    valid, error = validate_lunch_start(date.today(), start_time, 15)
    if not valid:
        await message.answer(error, reply_markup=lunch_slots_keyboard())
        return
    await state.update_data(start_time=start_time)
    await state.set_state(BookingStates.waiting_move_duration)
    await message.answer(f'Новий час початку: {start_time}. Тепер оберіть тривалість:', reply_markup=duration_keyboard())


@router.message(BookingStates.waiting_move_duration)
async def move_finish(message: Message, state: FSMContext):
    if await _deny_if_no_access(message):
        await state.clear()
        return
    duration = _parse_duration(message.text)
    if duration is None:
        await message.answer('Оберіть тривалість кнопкою: 15 хв, 30 хв або 45 хв.', reply_markup=duration_keyboard())
        return
    data = await state.get_data()
    start_time = data.get('start_time')
    valid, error = validate_lunch_start(date.today(), start_time, duration)
    if not valid:
        await state.set_state(BookingStates.waiting_move_time)
        await message.answer(error + '\nОберіть інший час початку.', reply_markup=lunch_slots_keyboard())
        return
    user = message.from_user
    ok, text = move_booking(
        day=date.today(),
        user_id=user.id,
        username=user.username or '',
        full_name=display_name(user.id, user.full_name),
        new_start_time=start_time,
        duration_minutes=duration,
        actor_id=user.id,
        actor_name=display_name(user.id, user.full_name),
    )
    await state.clear()
    await message.answer(text, reply_markup=_menu_for(user.id))


@router.message(F.text == '❌ Скасувати обід')
async def cancel_start(message: Message, state: FSMContext):
    if await _deny_if_no_access(message):
        return
    user = message.from_user
    full_name = display_name(user.id, user.full_name)
    bookings = find_user_schedule_bookings(full_name)
    if not bookings:
        await message.answer('У вас немає активного обіду на сьогодні у листі schedule.', reply_markup=_menu_for(user.id))
        return
    await state.set_state(BookingStates.waiting_cancel_choice)
    await state.update_data(cancel_bookings=bookings)
    lines = ['Який обід скасувати?']
    for i, b in enumerate(bookings, start=1):
        lines.append(f'{i}) {b.get("start_time")}–{b.get("end_time")}')
    await message.answer('\n'.join(lines), reply_markup=cancel_confirm_keyboard(bookings))


@router.message(BookingStates.waiting_cancel_choice)
async def cancel_finish(message: Message, state: FSMContext):
    if await _deny_if_no_access(message):
        await state.clear()
        return
    if not message.text.startswith('✅'):
        await message.answer('Оберіть обід для скасування кнопкою або натисніть «Назад».')
        return
    data = await state.get_data()
    bookings = data.get('cancel_bookings') or []
    import re
    m = re.search(r'✅\s*(\d+)\)', message.text)
    if not m:
        await message.answer('Не зрозумів вибір. Натисніть кнопку з номером обіду.')
        return
    idx = int(m.group(1)) - 1
    if idx < 0 or idx >= len(bookings):
        await message.answer('Такого обіду немає у списку.')
        return
    target = bookings[idx]
    user = message.from_user
    ok, text = cancel_schedule_booking(
        date.today(),
        user.id,
        display_name(user.id, user.full_name),
        str(target.get('start_time')),
        str(target.get('end_time')),
        user.id,
        display_name(user.id, user.full_name),
    )
    await state.clear()
    await message.answer(text, reply_markup=_menu_for(user.id))


@router.message(F.text == '👀 Мій обід')
async def my_lunch(message: Message):
    if await _deny_if_no_access(message):
        return
    user = message.from_user
    bookings = find_user_schedule_bookings(display_name(user.id, user.full_name))
    if not bookings:
        await message.answer('У вас немає обідів на сьогодні у листі schedule.')
        return
    parts = [f'{b.get("start_time")}–{b.get("end_time")}' for b in sorted(bookings, key=lambda x: x.get('start_time', ''))]
    await message.answer('Ваші обіди сьогодні: ' + ', '.join(parts))
