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
    spreadsheet_id: str = os.getenv('SPREADSHEET_ID', '')
    google_credentials_file: str = os.getenv('GOOGLE_CREDENTIALS_FILE', 'service_account.json')
    timezone: str = os.getenv('TIMEZONE', 'Europe/Kyiv')
    admin_ids: list[int] = None
    lunch_duration_minutes: int = int(os.getenv('LUNCH_DURATION_MINUTES', '45'))
    slot_capacity: int = int(os.getenv('SLOT_CAPACITY', '2'))
    reminder_minutes: int = int(os.getenv('REMINDER_MINUTES', '15'))

    def __post_init__(self):
        object.__setattr__(self, 'admin_ids', _int_list(os.getenv('ADMIN_IDS', '')))


settings = Settings()
