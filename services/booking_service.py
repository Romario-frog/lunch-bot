from __future__ import annotations

from datetime import date, datetime, timedelta

import pytz

from config import settings
from services import google_sheet_service as sheets
from services import schedule_service as schedule
from services.log_service import add_log


def _dt(day: date, hhmm: str) -> datetime:
    tz = pytz.timezone(settings.timezone)
    naive = datetime.combine(day, sheets.parse_hhmm(hhmm))
    return tz.localize(naive)


def _end_time(day: date, start_time: str, duration_minutes: int | None = None) -> str:
    minutes = int(duration_minutes or settings.lunch_duration_minutes)
    return (_dt(day, start_time) + timedelta(minutes=minutes)).strftime('%H:%M')


def validate_lunch_start(day: date, start_time: str, duration_minutes: int | None = None) -> tuple[bool, str]:
    try:
        start = _dt(day, start_time)
    except Exception:
        return False, 'Неправильний час. Напишіть вручну у форматі HH:MM, наприклад 17:15.'

    if start.minute not in (0, 15, 30, 45):
        return False, 'Неправильний крок часу. Доступно тільки 00 / 15 / 30 / 45 хвилин.'

    work_start = _dt(day, settings.lunch_start_time)
    work_finish = _dt(day, settings.lunch_finish_time)
    minutes = int(duration_minutes or settings.lunch_duration_minutes)
    end = start + timedelta(minutes=minutes)

    if start < work_start:
        return False, f'Не можна ставити обід раніше {settings.lunch_start_time}.'
    if end > work_finish:
        last_start = (work_finish - timedelta(minutes=minutes)).strftime('%H:%M')
        return False, f'Не можна виходити за {settings.lunch_finish_time}. Останній старт для {minutes} хв: {last_start}.'
    return True, ''


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


def create_booking(day: date, user_id: int, username: str, full_name: str, start_time: str, actor_id: int, actor_name: str, force: bool = False, duration_minutes: int | None = None) -> tuple[bool, str]:
    valid, error = validate_lunch_start(day, start_time, duration_minutes)
    if not valid:
        return False, error

    duration_minutes = int(duration_minutes or settings.lunch_duration_minutes)
    end_time = _end_time(day, start_time, duration_minutes)
    ok_schedule, schedule_error, schedule_name = schedule.validate_schedule_place(full_name, start_time, duration_minutes)
    if not ok_schedule:
        return False, schedule_error
    final_name = schedule_name or full_name

    row = {
        'date': day.strftime('%d.%m.%Y'),
        'user_id': user_id,
        'username': username,
        'full_name': final_name,
        'start_time': start_time,
        'end_time': end_time,
        'duration_minutes': duration_minutes,
        'status': 'active',
        'created_by': actor_name,
        'updated_at': datetime.now().isoformat(timespec='seconds'),
    }
    sheets.append_booking(row)
    schedule.set_lunch_cells(final_name, start_time, duration_minutes=duration_minutes)
    add_log('book', actor_id, actor_name, final_name, row)
    sheets.append_sheet_log('book', actor_id, actor_name, final_name, f'{start_time}-{end_time}')
    return True, f'Обід заплановано: {start_time}–{end_time} ({duration_minutes} хв).'


def cancel_booking(day: date, user_id: int, actor_id: int, actor_name: str) -> tuple[bool, str]:
    booking = find_user_booking(day, user_id)
    if not booking:
        return False, 'Активний обід не знайдено.'
    ok = sheets.update_booking_status(day, user_id, 'cancelled')
    if ok:
        try:
            schedule.clear_lunch_cells(str(booking.get('full_name', '')), str(booking.get('start_time', '')), int(booking.get('duration_minutes') or settings.lunch_duration_minutes))
        except Exception as exc:
            return False, f'Обід у bot_data скасовано, але не вдалося очистити schedule: {exc}'
        add_log('cancel', actor_id, actor_name, str(booking.get('full_name', '')), booking)
        sheets.append_sheet_log('cancel', actor_id, actor_name, str(booking.get('full_name', '')), str(booking))
        return True, 'Обід скасовано.'
    return False, 'Не вдалося скасувати обід.'


def move_booking(day: date, user_id: int, username: str, full_name: str, new_start_time: str, actor_id: int, actor_name: str, force: bool = False, duration_minutes: int | None = None) -> tuple[bool, str]:
    duration_minutes = int(duration_minutes or settings.lunch_duration_minutes)
    valid, error = validate_lunch_start(day, new_start_time, duration_minutes)
    if not valid:
        return False, error

    old = find_user_booking(day, user_id)
    if not old:
        return False, 'Спочатку треба мати активний обід, щоб його перенести.'
    new_end = _end_time(day, new_start_time, duration_minutes)

    try:
        old_duration = int(old.get('duration_minutes') or settings.lunch_duration_minutes)
        schedule.clear_lunch_cells(str(old.get('full_name', full_name)), str(old.get('start_time')), old_duration)
        ok_schedule, schedule_error, schedule_name = schedule.validate_schedule_place(full_name, new_start_time, duration_minutes)
        if not ok_schedule:
            schedule.set_lunch_cells(str(old.get('full_name', full_name)), str(old.get('start_time')), duration_minutes=old_duration)
            return False, schedule_error
        full_name = schedule_name or full_name
    except Exception as exc:
        return False, f'Не вдалося оновити лист schedule: {exc}'

    sheets.update_booking_status(day, user_id, 'moved')
    ok, text = create_booking(day, user_id, username, full_name, new_start_time, actor_id, actor_name, force=True, duration_minutes=duration_minutes)
    if ok:
        return True, f'Обід перенесено: {new_start_time}–{new_end} ({duration_minutes} хв).'
    try:
        schedule.set_lunch_cells(str(old.get('full_name', full_name)), str(old.get('start_time')), duration_minutes=old_duration)
    except Exception:
        pass
    return ok, text


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
    return sorted(result, key=lambda x: str(x.get('end_time', '')))


def today_schedule() -> list[dict]:
    return sorted(active_bookings(date.today()), key=lambda x: (str(x.get('start_time', '')), str(x.get('full_name', ''))))


def today_statistics() -> dict:
    bookings = today_schedule()
    return {
        'total': len(bookings),
        'current': len(current_lunches()),
        'bookings': bookings,
        'users': sorted({str(b.get('full_name', '')) for b in bookings if b.get('full_name')}),
    }


def find_user_schedule_bookings(full_name: str) -> list[dict]:
    return schedule.find_schedule_entries_for_name(full_name)


def cancel_schedule_booking(day: date, user_id: int, full_name: str, start_time: str, end_time: str, actor_id: int, actor_name: str) -> tuple[bool, str]:
    entries = schedule.find_schedule_entries_for_name(full_name)
    target = None
    for item in entries:
        if str(item.get('start_time')) == str(start_time) and str(item.get('end_time')) == str(end_time):
            target = item
            break
    if not target:
        return False, 'Не знайшов такий обід у листі schedule. Оновіть розклад і спробуйте ще раз.'

    try:
        schedule.clear_lunch_interval(str(target.get('full_name')), start_time, end_time)
    except Exception as exc:
        return False, f'Не вдалося очистити schedule: {exc}'

    # If this interval was created by the bot, mark it cancelled in bot_data too.
    try:
        sheets.update_booking_status_by_start(day, user_id, start_time, 'cancelled')
    except Exception:
        pass

    add_log('cancel_schedule', actor_id, actor_name, str(target.get('full_name')), target)
    sheets.append_sheet_log('cancel_schedule', actor_id, actor_name, str(target.get('full_name')), f'{start_time}-{end_time}')
    return True, f'Обід скасовано: {start_time}–{end_time}.'
