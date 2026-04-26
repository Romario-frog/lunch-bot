from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import gspread
from gspread.utils import rowcol_to_a1

from config import settings
from services import google_sheet_service as sheets
from services.name_service import compact_name, name_variants, latin_to_ukrainian, ukrainian_to_latin

SCHEDULE_SHEET = getattr(settings, 'schedule_sheet_name', 'schedule')
TIME_ROW = 2
# У твоїй таблиці зверху написано: "Напиши - О щоб зайняти обід".
# Підтримуємо і кириличну О, і нуль 0, бо в чаті їх легко переплутати.
OCCUPIED_VALUE = 'О'
BUSY_MARKERS = {'0', 'о', 'o', 'обід', 'обед'}
STOP_MARKERS = ('ліміт', 'лимит', '#ref', '#n/a', 'правила', 'додаткові', '26.04.2026')


def _parse_time_value(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    for fmt in ('%H:%M', '%H:%M:%S'):
        try:
            return datetime.strptime(text, fmt).strftime('%H:%M')
        except ValueError:
            pass
    try:
        num = float(text.replace(',', '.'))
        if 0 <= num < 1:
            minutes = int(round(num * 24 * 60)) % (24 * 60)
            hh, mm = divmod(minutes, 60)
            return f'{hh:02d}:{mm:02d}'
    except ValueError:
        pass
    return None


def _schedule_ws():
    ss = sheets._spreadsheet()
    try:
        return ss.worksheet(SCHEDULE_SHEET)
    except gspread.WorksheetNotFound as exc:
        raise RuntimeError(f'Не знайдено лист "{SCHEDULE_SHEET}". Назви красивий лист саме schedule.') from exc


def _values() -> list[list[str]]:
    return _schedule_ws().get_all_values()


def _is_stop_name(name: str) -> bool:
    low = str(name).strip().casefold()
    if not low:
        return False
    if any(marker in low for marker in STOP_MARKERS):
        return True
    # дата або службова строка — не оператор
    try:
        datetime.strptime(low, '%d.%m.%Y')
        return True
    except ValueError:
        return False


def _schedule_rows(values: list[list[str]]) -> list[tuple[int, list[str]]]:
    result = []
    for idx, row in enumerate(values, start=1):
        if idx <= TIME_ROW:
            continue
        name = str(row[0]).strip() if row else ''
        if not name:
            continue
        if _is_stop_name(name):
            break
        low = name.casefold()
        if low.startswith('#'):
            continue
        result.append((idx, row))
    return result


def _token_variants(text: str) -> list[set[str]]:
    raw = [p for p in str(text).replace("'", ' ').replace('’', ' ').split() if p.strip()]
    result = []
    for part in raw:
        result.append(name_variants(part))
    return result


def _tokens_match(a: str, b: str) -> bool:
    if not a or not b:
        return False
    # Roma ↔ Roman, Serhii ↔ Сергій — достатньо префікса 4+ символи
    if a == b:
        return True
    if len(a) >= 4 and len(b) >= 4 and (a.startswith(b[:4]) or b.startswith(a[:4])):
        return True
    return False


def _name_match_score(query: str, candidate: str) -> int:
    q_variants = name_variants(query)
    c_variants = name_variants(candidate)
    if q_variants & c_variants:
        return 100

    # Повне входження після транслітерації/стиснення
    for q in q_variants:
        for c in c_variants:
            if len(q) >= 5 and len(c) >= 5 and (q in c or c in q):
                return 80

    q_tokens = _token_variants(query)
    c_tokens = _token_variants(candidate)
    matched = 0
    for q_set in q_tokens:
        ok = False
        for c_set in c_tokens:
            if q_set & c_set:
                ok = True
                break
            if any(_tokens_match(q, c) for q in q_set for c in c_set):
                ok = True
                break
        if ok:
            matched += 1

    if matched >= 2:
        return 70
    if matched == 1 and (len(q_tokens) == 1 or len(c_tokens) == 1):
        return 45
    return 0


def resolve_schedule_name(full_name: str) -> str | None:
    """Повертає реальне ПІБ з листа schedule.

    Приклади:
    - Roma Chobotar → Чоботар Роман
    - Fomichov Serhii → Фомічов Сергій / Fomichov Serhii
    """
    values = _values()
    best_name = None
    best_score = 0
    for _, row in _schedule_rows(values):
        candidate = str(row[0]).strip()
        score = _name_match_score(full_name, candidate)
        if score > best_score:
            best_name = candidate
            best_score = score
    return best_name if best_score >= 70 else None


def _find_name_row(values: list[list[str]], full_name: str) -> tuple[int | None, str | None]:
    best_row = None
    best_name = None
    best_score = 0
    for idx, row in _schedule_rows(values):
        candidate = str(row[0]).strip()
        score = _name_match_score(full_name, candidate)
        if score > best_score:
            best_row = idx
            best_name = candidate
            best_score = score
    if best_score >= 70:
        return best_row, best_name
    return None, None


def _time_columns(values: list[list[str]]) -> dict[str, int]:
    if len(values) < TIME_ROW:
        return {}
    result: dict[str, int] = {}
    for col, raw in enumerate(values[TIME_ROW - 1], start=1):
        hhmm = _parse_time_value(raw)
        if hhmm:
            result[hhmm] = col
    return result


def _needed_times(start_time: str, minutes: int | None = None) -> list[str]:
    minutes = int(minutes or settings.lunch_duration_minutes)
    start = datetime.strptime(start_time, '%H:%M')
    step = timedelta(minutes=15)
    count = max(1, minutes // 15)
    return [(start + i * step).strftime('%H:%M') for i in range(count)]


def _end_time(start_time: str, minutes: int | None = None) -> str:
    minutes = int(minutes or settings.lunch_duration_minutes)
    return (datetime.strptime(start_time, '%H:%M') + timedelta(minutes=minutes)).strftime('%H:%M')


def _cell_value(values: list[list[str]], row: int, col: int) -> str:
    try:
        return str(values[row - 1][col - 1]).strip()
    except IndexError:
        return ''


def _is_busy(value: str) -> bool:
    # Раніше будь-який непорожній текст рахувався як обід, через це #REF!/формули могли давати "3-тя людина".
    # Тепер зайнятим рахуємо тільки реальні позначки: О/o/0/обід.
    text = compact_name(str(value).strip())
    return text in BUSY_MARKERS


def validate_schedule_place(full_name: str, start_time: str, duration_minutes: int | None = None) -> tuple[bool, str, str | None]:
    values = _values()
    row, schedule_name = _find_name_row(values, full_name)
    if row is None or not schedule_name:
        return False, f'Не знайшов ПІБ "{full_name}" на листі {SCHEDULE_SHEET}. Перевір users або schedule.', None

    columns = _time_columns(values)
    needed = _needed_times(start_time, duration_minutes)
    missing = [t for t in needed if t not in columns]
    if missing:
        return False, f'У листі {SCHEDULE_SHEET} не знайдено час: {", ".join(missing)}.', schedule_name

    for t in needed:
        current = _cell_value(values, row, columns[t])
        if _is_busy(current):
            return False, f'У вашому рядку вже зайнято {t}. Спочатку перенесіть або скасуйте старий обід.', schedule_name

    busy_by_time: dict[str, int] = {}
    for t in needed:
        col = columns[t]
        busy = 0
        for r_idx, _ in _schedule_rows(values):
            if _is_busy(_cell_value(values, r_idx, col)):
                busy += 1
        busy_by_time[t] = busy

    # За твоєю логікою: можна, якщо хоча б один із вибраних 15-хв слотів ще має місце.
    if all(count >= settings.slot_capacity for count in busy_by_time.values()):
        details = ', '.join(f'{t}: {count}' for t, count in busy_by_time.items())
        return False, f'У цьому проміжку вже немає місця за лімітом ({details}). Оберіть інший час.', schedule_name

    return True, '', schedule_name


def set_lunch_cells(full_name: str, start_time: str, value: str = OCCUPIED_VALUE, duration_minutes: int | None = None) -> str:
    values = _values()
    row, schedule_name = _find_name_row(values, full_name)
    if row is None or not schedule_name:
        raise RuntimeError(f'Не знайшов ПІБ "{full_name}" на листі {SCHEDULE_SHEET}.')
    columns = _time_columns(values)
    updates = []
    for t in _needed_times(start_time, duration_minutes):
        col = columns.get(t)
        if not col:
            raise RuntimeError(f'У листі {SCHEDULE_SHEET} не знайдено колонку часу {t}.')
        updates.append({'range': rowcol_to_a1(row, col), 'values': [[value]]})
    _schedule_ws().batch_update(updates, value_input_option='USER_ENTERED')
    return schedule_name


def clear_lunch_cells(full_name: str, start_time: str, duration_minutes: int | None = None) -> None:
    set_lunch_cells(full_name, start_time, '', duration_minutes)


def read_schedule_entries() -> list[dict[str, str]]:
    values = _values()
    columns = _time_columns(values)
    if not columns:
        return []
    ordered = sorted(columns.items(), key=lambda x: datetime.strptime(x[0], '%H:%M'))
    entries: list[dict[str, str]] = []

    for _, row in _schedule_rows(values):
        full_name = str(row[0]).strip()
        active_start = None
        last_busy_time = None
        for hhmm, col in ordered:
            value = row[col - 1].strip() if len(row) >= col else ''
            if _is_busy(value):
                if active_start is None:
                    active_start = hhmm
                last_busy_time = hhmm
            else:
                if active_start and last_busy_time:
                    entries.append({'full_name': full_name, 'start_time': active_start, 'end_time': _end_time(last_busy_time, 15)})
                active_start = None
                last_busy_time = None
        if active_start and last_busy_time:
            entries.append({'full_name': full_name, 'start_time': active_start, 'end_time': _end_time(last_busy_time, 15)})
    return sorted(entries, key=lambda x: (x['start_time'], x['full_name']))


def _duration_minutes(start_time: str, end_time: str) -> int:
    start = datetime.strptime(start_time, '%H:%M')
    end = datetime.strptime(end_time, '%H:%M')
    return int((end - start).total_seconds() // 60)


def find_schedule_entries_for_name(full_name: str) -> list[dict[str, str]]:
    """Find all lunch intervals for a user on the visual schedule sheet.

    This sees both manual site/table entries and bot-created entries.
    """
    schedule_name = resolve_schedule_name(full_name)
    if not schedule_name:
        return []
    return [e for e in read_schedule_entries() if e.get('full_name') == schedule_name]


def clear_lunch_interval(full_name: str, start_time: str, end_time: str) -> None:
    minutes = _duration_minutes(start_time, end_time)
    clear_lunch_cells(full_name, start_time, minutes)


def group_entries_by_name(entries: list[dict[str, str]] | None = None) -> list[dict[str, object]]:
    """Group schedule intervals so one person is printed once with all intervals."""
    entries = entries if entries is not None else read_schedule_entries()
    grouped: dict[str, list[dict[str, str]]] = {}
    for entry in entries:
        grouped.setdefault(entry['full_name'], []).append(entry)
    result: list[dict[str, object]] = []
    for name, items in grouped.items():
        items = sorted(items, key=lambda x: x['start_time'])
        result.append({'full_name': name, 'entries': items})
    return sorted(result, key=lambda x: str(x['full_name']))
