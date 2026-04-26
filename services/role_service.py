from config import settings
from services.storage_service import load_json, save_json

USERS_FILE = 'data/users.json'


def _base() -> dict:
    return {'admins': {}, 'operators': {}, 'pending': {}}


def _load() -> dict:
    users = load_json(USERS_FILE, _base())
    users.setdefault('admins', {})
    users.setdefault('operators', {})
    users.setdefault('pending', {})
    return users


def _save(users: dict) -> None:
    save_json(USERS_FILE, users)


def is_admin(user_id: int) -> bool:
    users = _load()
    return user_id in settings.admin_ids or str(user_id) in users.get('admins', {})


def is_operator(user_id: int) -> bool:
    users = _load()
    return str(user_id) in users.get('operators', {}) or is_admin(user_id)


def has_access(user_id: int) -> bool:
    return is_operator(user_id) or is_admin(user_id)


def role_name(user_id: int) -> str:
    if is_admin(user_id):
        return 'admin'
    if is_operator(user_id):
        return 'operator'
    return 'guest'


def get_user(user_id: int) -> dict | None:
    users = _load()
    uid = str(user_id)
    if uid in users['admins']:
        return users['admins'][uid] | {'role': 'admin'}
    if uid in users['operators']:
        return users['operators'][uid] | {'role': 'operator'}
    if uid in users['pending']:
        return users['pending'][uid] | {'role': 'pending'}
    return None


def add_pending(user_id: int, full_name: str, username: str | None = None) -> None:
    users = _load()
    uid = str(user_id)
    if uid in users['admins'] or uid in users['operators']:
        return
    users['pending'][uid] = {'full_name': full_name, 'username': username or ''}
    _save(users)


def approve_operator(user_id: int) -> dict | None:
    users = _load()
    uid = str(user_id)
    pending = users['pending'].pop(uid, None)
    if not pending:
        return None
    users['operators'][uid] = pending
    _save(users)
    return pending


def reject_pending(user_id: int) -> dict | None:
    users = _load()
    pending = users['pending'].pop(str(user_id), None)
    _save(users)
    return pending


def list_users() -> dict:
    return _load()
