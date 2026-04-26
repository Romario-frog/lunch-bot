from config import settings
from services.storage_service import load_json, save_json

USERS_FILE = 'data/users.json'


def is_admin(user_id: int) -> bool:
    users = load_json(USERS_FILE, {})
    return user_id in settings.admin_ids or str(user_id) in users.get('admins', [])


def role_name(user_id: int) -> str:
    return 'admin' if is_admin(user_id) else 'operator'


def remember_user(user_id: int, full_name: str, username: str | None = None) -> None:
    users = load_json(USERS_FILE, {})
    users.setdefault('operators', {})
    users['operators'][str(user_id)] = {
        'full_name': full_name,
        'username': username or '',
    }
    save_json(USERS_FILE, users)
