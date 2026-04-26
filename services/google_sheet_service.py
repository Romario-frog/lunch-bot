from __future__ import annotations

from datetime import date, datetime, time
from typing import Any

import gspread
from google.oauth2.service_account import Credentials

from config import settings

BOT_DATA_SHEET = 'bot_data'
LOG_SHEET = 'logs'

HEADERS = ['date', 'user_id', 'username', 'full_name', 'start_time', 'end_time', 'status', 'created_by', 'updated_at']
LOG_HEADERS = ['created_at', 'action', 'actor_id', 'actor_name', 'target_name', 'details']
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def _client() -> gspread.Client:
    creds = Credentials.from_service_account_file(settings.google_credentials_file, scopes=SCOPES)
    return gspread.authorize(creds)


def _spreadsheet():
    return _client().open_by_key(settings.spreadsheet_id)


def _worksheet(title: str, headers: list[str]):
    ss = _spreadsheet()
    try:
        ws = ss.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = ss.add_worksheet(title=title, rows=1000, cols=len(headers) + 2)
        ws.append_row(headers)
    current_headers = ws.row_values(1)
    if current_headers != headers:
        ws.update('A1', [headers])
    return ws


def ensure_sheets() -> None:
    _worksheet(BOT_DATA_SHEET, HEADERS)
    _worksheet(LOG_SHEET, LOG_HEADERS)


def get_bookings(day: date | None = None) -> list[dict[str, Any]]:
    ws = _worksheet(BOT_DATA_SHEET, HEADERS)
    rows = ws.get_all_records()
    if day is None:
        return rows
    day_str = day.strftime('%d.%m.%Y')
    return [r for r in rows if str(r.get('date')) == day_str and str(r.get('status', 'active')) == 'active']


def append_booking(row: dict[str, Any]) -> None:
    ws = _worksheet(BOT_DATA_SHEET, HEADERS)
    ws.append_row([row.get(h, '') for h in HEADERS], value_input_option='USER_ENTERED')


def update_booking_status(day: date, user_id: int, status: str) -> bool:
    ws = _worksheet(BOT_DATA_SHEET, HEADERS)
    rows = ws.get_all_records()
    day_str = day.strftime('%d.%m.%Y')
    for idx, row in enumerate(rows, start=2):
        if str(row.get('date')) == day_str and str(row.get('user_id')) == str(user_id) and row.get('status') == 'active':
            ws.update_cell(idx, HEADERS.index('status') + 1, status)
            ws.update_cell(idx, HEADERS.index('updated_at') + 1, datetime.now().isoformat(timespec='seconds'))
            return True
    return False


def append_sheet_log(action: str, actor_id: int, actor_name: str, target_name: str, details: str) -> None:
    ws = _worksheet(LOG_SHEET, LOG_HEADERS)
    ws.append_row([datetime.now().isoformat(timespec='seconds'), action, actor_id, actor_name, target_name, details], value_input_option='USER_ENTERED')


def parse_hhmm(value: str) -> time:
    return datetime.strptime(value.strip(), '%H:%M').time()
