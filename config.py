import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _int_list(value: str) -> list[int]:
    if not value:
        return []
    return [int(x.strip()) for x in value.split(',') if x.strip()]


@dataclass(frozen=True)
class Settings:
    bot_token: str = os.getenv('BOT_TOKEN', '')
    # поддерживаем оба названия, чтобы не ловить ошибку из-за GOOGLE_SHEET_ID / SPREADSHEET_ID
    spreadsheet_id: str = os.getenv('SPREADSHEET_ID') or os.getenv('GOOGLE_SHEET_ID', '')
    google_credentials_file: str = os.getenv('GOOGLE_CREDENTIALS_FILE', 'service_account.json')
    google_service_account_json: str = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON', '')
    timezone: str = os.getenv('TIMEZONE', 'Europe/Kyiv')
    admin_ids: list[int] = None
    lunch_duration_minutes: int = int(os.getenv('LUNCH_DURATION_MINUTES', '45'))
    slot_capacity: int = int(os.getenv('SLOT_CAPACITY', '2'))
    reminder_minutes: int = int(os.getenv('REMINDER_MINUTES', '15'))
    lunch_start_time: str = os.getenv('LUNCH_START_TIME', '10:00')
    lunch_finish_time: str = os.getenv('LUNCH_FINISH_TIME', '20:00')
    schedule_sheet_name: str = os.getenv('SCHEDULE_SHEET_NAME', 'schedule')
    keep_alive_enabled: bool = os.getenv('KEEP_ALIVE_ENABLED', 'true').lower() in {'1', 'true', 'yes', 'on'}
    keep_alive_minutes: int = int(os.getenv('KEEP_ALIVE_MINUTES', '10'))
    keep_alive_sheet_name: str = os.getenv('KEEP_ALIVE_SHEET_NAME', 'keep_alive')

    def __post_init__(self):
        object.__setattr__(self, 'admin_ids', _int_list(os.getenv('ADMIN_IDS', '')))


settings = Settings()
