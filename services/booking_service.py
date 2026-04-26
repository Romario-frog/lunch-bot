from __future__ import annotations

from datetime import date, datetime, timedelta

import pytz

from config import settings
from services import google_sheet_service as sheets
from services.log_service import add_log


def _dt(day: date, hhmm: str) -> datetime:
    tz = pytz.timezone(settings.timezone)
    naive = datetime.combine(day, sheets.parse_hhmm(hhmm))
    return tz.localize(naive)


def _end_time(day: date, start_time: str) -> str:
    return (_dt(day, start_time) + timedelta(minutes=settings.lunch_duration_minutes)).strftime('%H:%M')


def _overlaps(day: date, start_a: str, end_a: str, start_b: str, end_b: str) -> bool:
    a1, a2 = _dt(day, start_a), _dt(day, end_a)
    b1, b2 = _dt(day, start_b), _dt(day, end_b)
    return a1 < b2 and b1 < a2


def active_bookings(day: date | None = None) -> list[dict]:
    return sheets.get_bookings(day or date.today())


def find_user_booking(day: date, user_id: int) -> dict | None:
    for booking in active_bookings(day):
        if str(booking.get('user_id')) == str(user_id):
            return booking
    return None


def count_overlaps(day: date, start_time: str, end_time: str) -> int:
    total = 0
    for booking in active_bookings(day):
        if _overlaps(day, start_time, end_time, str(booking['start_time']), str(booking['end_time'])):
            total += 1
    return total


def create_booking(day: date, user_id: int, username: str, full_name: str, start_time: str, actor_id: int, actor_name: str, force: bool = False) -> tuple[bool, str]:
    end_time = _end_time(day, start_time)
    if find_user_booking(day, user_id):
        return False, 'У користувача вже є активний обід на сьогодні. Спочатку перенесіть або скасуйте його.'
    if not force and count_overlaps(day, start_time, end_time) >= settings.slot_capacity:
        return False, f'На цей час вже зайнято {settings.slot_capacity} місця. Оберіть інший слот.'

    row = {
        'date': day.strftime('%d.%m.%Y'),
        'user_id': user_id,
        'username': username,
        'full_name': full_name,
        'start_time': start_time,
        'end_time': end_time,
        'status': 'active',
        'created_by': actor_name,
        'updated_at': datetime.now().isoformat(timespec='seconds'),
    }
    sheets.append_booking(row)
    add_log('book', actor_id, actor_name, full_name, row)
    sheets.append_sheet_log('book', actor_id, actor_name, full_name, f'{start_time}-{end_time}')
    return True, f'Обід заплановано: {start_time}–{end_time}.'


def cancel_booking(day: date, user_id: int, actor_id: int, actor_name: str) -> tuple[bool, str]:
    booking = find_user_booking(day, user_id)
    if not booking:
        return False, 'Активний обід не знайдено.'
    ok = sheets.update_booking_status(day, user_id, 'cancelled')
    if ok:
        add_log('cancel', actor_id, actor_name, str(booking.get('full_name', '')), booking)
        sheets.append_sheet_log('cancel', actor_id, actor_name, str(booking.get('full_name', '')), str(booking))
        return True, 'Обід скасовано.'
    return False, 'Не вдалося скасувати обід.'


def move_booking(day: date, user_id: int, username: str, full_name: str, new_start_time: str, actor_id: int, actor_name: str, force: bool = False) -> tuple[bool, str]:
    old = find_user_booking(day, user_id)
    if not old:
        return False, 'Спочатку треба мати активний обід, щоб його перенести.'
    new_end = _end_time(day, new_start_time)
    # тимчасово не рахуємо власний старий обід
    other_count = 0
    for booking in active_bookings(day):
        if str(booking.get('user_id')) == str(user_id):
            continue
        if _overlaps(day, new_start_time, new_end, str(booking['start_time']), str(booking['end_time'])):
            other_count += 1
    if not force and other_count >= settings.slot_capacity:
        return False, f'На цей час вже зайнято {settings.slot_capacity} місця. Оберіть інший слот.'
    sheets.update_booking_status(day, user_id, 'moved')
    return create_booking(day, user_id, username, full_name, new_start_time, actor_id, actor_name, force=True)


def current_lunches(now: datetime | None = None) -> list[dict]:
    tz = pytz.timezone(settings.timezone)
    now = now or datetime.now(tz)
    day = now.date()
    result = []
    for b in active_bookings(day):
        start = _dt(day, str(b['start_time']))
        end = _dt(day, str(b['end_time']))
        if start <= now < end:
            result.append(b)
    return result


def today_statistics() -> dict:
    bookings = active_bookings(date.today())
    return {
        'total': len(bookings),
        'current': len(current_lunches()),
        'users': sorted({str(b.get('full_name', '')) for b in bookings if b.get('full_name')}),
    }
