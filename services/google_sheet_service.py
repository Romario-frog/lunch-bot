from __future__ import annotations

import json
from datetime import date, datetime, time
from typing import Any

import gspread
from google.oauth2.service_account import Credentials

from config import settings

BOT_DATA_SHEET = 'bot_data'
USER_SHEET = 'users'
LOG_SHEET = 'logs'
HEADERS = ['date', 'user_id', 'username', 'full_name', 'start_time', 'end_time', 'duration_minutes', 'status', 'created_by', 'updated_at']
USER_HEADERS = ['user_id', 'name', 'role', 'status']
LOG_HEADERS = ['created_at', 'action', 'actor_id', 'actor_name', 'target_name', 'details']
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def _credentials() -> Credentials:
    if settings.google_service_account_json:
        data = json.loads(settings.google_service_account_json)
        return Credentials.from_service_account_info(data, scopes=SCOPES)
    return Credentials.from_service_account_file(settings.google_credentials_file, scopes=SCOPES)


def _client() -> gspread.Client:
    return gspread.authorize(_credentials())


def _spreadsheet():
    if not settings.spreadsheet_id:
        raise RuntimeError('SPREADSHEET_ID is empty')
    return _client().open_by_key(settings.spreadsheet_id)


def _worksheet(title: str, headers: list[str]):
    ss = _spreadsheet()
    try:
        ws = ss.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = ss.add_worksheet(title=title, rows=1000, cols=len(headers) + 2)
        ws.append_row(headers)
    current_headers = ws.row_values(1)
    if current_headers[:len(headers)] != headers:
        ws.update('A1', [headers])
    return ws


def ensure_sheets() -> None:
    _worksheet(BOT_DATA_SHEET, HEADERS)
    _worksheet(USER_SHEET, USER_HEADERS)
    _worksheet(LOG_SHEET, LOG_HEADERS)


def get_bookings(day: date | None = None) -> list[dict[str, Any]]:
    ws = _worksheet(BOT_DATA_SHEET, HEADERS)
    rows = ws.get_all_records()
    if day is None:
        return rows
    day_str = day.strftime('%d.%m.%Y')
    return [r for r in rows if str(r.get('date')) == day_str and str(r.get('status', 'active')).lower() == 'active']


def append_booking(row: dict[str, Any]) -> None:
    ws = _worksheet(BOT_DATA_SHEET, HEADERS)
    ws.append_row([row.get(h, '') for h in HEADERS], value_input_option='USER_ENTERED')


def update_booking_status(day: date, user_id: int, status: str) -> bool:
    ws = _worksheet(BOT_DATA_SHEET, HEADERS)
    rows = ws.get_all_records()
    day_str = day.strftime('%d.%m.%Y')
    for idx, row in enumerate(rows, start=2):
        if str(row.get('date')) == day_str and str(row.get('user_id')) == str(user_id) and str(row.get('status')) == 'active':
            ws.update_cell(idx, HEADERS.index('status') + 1, status)
            ws.update_cell(idx, HEADERS.index('updated_at') + 1, datetime.now().isoformat(timespec='seconds'))
            return True
    return False


def get_sheet_user(user_id: int) -> dict[str, str] | None:
    ws = _worksheet(USER_SHEET, USER_HEADERS)
    for row in ws.get_all_records():
        if str(row.get('user_id')) == str(user_id) and str(row.get('status', '')).lower() == 'active':
            return {
                'user_id': str(row.get('user_id', '')),
                'name': str(row.get('name', '')).strip(),
                'role': str(row.get('role', '')).strip().lower(),
                'status': str(row.get('status', '')).strip().lower(),
            }
    return None


def append_or_update_user(user_id: int, name: str, role: str = 'operator', status: str = 'active') -> None:
    ws = _worksheet(USER_SHEET, USER_HEADERS)
    rows = ws.get_all_records()
    for idx, row in enumerate(rows, start=2):
        if str(row.get('user_id')) == str(user_id):
            ws.update(f'A{idx}:D{idx}', [[user_id, name, role, status]])
            return
    ws.append_row([user_id, name, role, status], value_input_option='USER_ENTERED')


def append_sheet_log(action: str, actor_id: int, actor_name: str, target_name: str, details: str) -> None:
    ws = _worksheet(LOG_SHEET, LOG_HEADERS)
    ws.append_row([datetime.now().isoformat(timespec='seconds'), action, actor_id, actor_name, target_name, details], value_input_option='USER_ENTERED')


def parse_hhmm(value: str) -> time:
    return datetime.strptime(value.strip(), '%H:%M').time()


def get_all_sheet_users(include_inactive: bool = False) -> list[dict[str, str]]:
    ws = _worksheet(USER_SHEET, USER_HEADERS)
    result: list[dict[str, str]] = []
    for row in ws.get_all_records():
        user_id = str(row.get('user_id', '')).strip()
        name = str(row.get('name', '')).strip()
        role = str(row.get('role', '')).strip().lower()
        status = str(row.get('status', '')).strip().lower() or 'active'
        if not user_id and not name:
            continue
        if not include_inactive and status != 'active':
            continue
        result.append({'user_id': user_id, 'name': name, 'role': role, 'status': status})
    return result


def write_keep_alive_ping() -> None:
    """Write a small timestamp to a separate service sheet for Render keep-alive."""
    ss = _spreadsheet()
    title = settings.keep_alive_sheet_name
    try:
        ws = ss.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = ss.add_worksheet(title=title, rows=5, cols=3)
        ws.update('A1:C1', [['status', 'updated_at', 'note']])
    ws.update('A2:C2', [['ok', datetime.now().isoformat(timespec='seconds'), 'render keep alive ping']])


def update_booking_status_by_start(day: date, user_id: int, start_time: str, status: str) -> bool:
    ws = _worksheet(BOT_DATA_SHEET, HEADERS)
    rows = ws.get_all_records()
    day_str = day.strftime('%d.%m.%Y')
    for idx, row in enumerate(rows, start=2):
        if (str(row.get('date')) == day_str
                and str(row.get('user_id')) == str(user_id)
                and str(row.get('start_time')) == str(start_time)
                and str(row.get('status')) == 'active'):
            ws.update_cell(idx, HEADERS.index('status') + 1, status)
            ws.update_cell(idx, HEADERS.index('updated_at') + 1, datetime.now().isoformat(timespec='seconds'))
            return True
    return False
