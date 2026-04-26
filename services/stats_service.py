from datetime import datetime

import pytz

from config import settings
from services import schedule_service


def _to_minutes(hhmm: str) -> int:
    h, m = map(int, hhmm.split(':'))
    return h * 60 + m


def _now_minutes() -> int:
    tz = pytz.timezone(settings.timezone)
    now = datetime.now(tz)
    return now.hour * 60 + now.minute


def format_current_lunches() -> str:
    now = _now_minutes()
    entries = schedule_service.read_schedule_entries()
    current = [e for e in entries if _to_minutes(e['start_time']) <= now < _to_minutes(e['end_time'])]
    if not current:
        return '📋 Зараз на обіді нікого немає.'
    lines = ['📋 Зараз на обіді:']
    for item in sorted(current, key=lambda x: (x['end_time'], x['full_name'])):
        lines.append(f'👤 {item["full_name"]} — до {item["end_time"]}')
    return '\n'.join(lines)


def format_today_stats() -> str:
    entries = schedule_service.read_schedule_entries()
    if not entries:
        return '🗓 Розклад обідів на сьогодні порожній.'

    now = _now_minutes()
    lines = ['🍽 Розклад обідів на сьогодні:']
    for group in schedule_service.group_entries_by_name(entries):
        intervals = []
        group_entries = group['entries']
        for item in group_entries:
            start = _to_minutes(item['start_time'])
            end = _to_minutes(item['end_time'])
            if start <= now < end:
                mark = '🟢'
            elif end <= now:
                mark = '⚪'
            else:
                mark = '🔵'
            intervals.append(f'{mark} {item["start_time"]}–{item["end_time"]}')
        lines.append(f'{group["full_name"]} — ' + ', '.join(intervals))

    current_count = sum(1 for e in entries if _to_minutes(e['start_time']) <= now < _to_minutes(e['end_time']))
    lines.append('')
    lines.append(f'Усього інтервалів: {len(entries)}')
    lines.append(f'Людей у розкладі: {len(schedule_service.group_entries_by_name(entries))}')
    lines.append(f'Зараз на обіді: {current_count}')
    lines.append('Позначки: 🟢 зараз, 🔵 буде, ⚪ вже був')
    return '\n'.join(lines)
