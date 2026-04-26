from config import settings
from services.storage_service import load_json, save_json
from services import google_sheet_service as sheets

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


def _sheet_user(user_id: int) -> dict | None:
    try:
        return sheets.get_sheet_user(user_id)
    except Exception:
        return None


def is_admin(user_id: int) -> bool:
    if user_id in settings.admin_ids:
        return True
    users = _load()
    if str(user_id) in users.get('admins', {}):
        return True
    sheet_user = _sheet_user(user_id)
    return bool(sheet_user and sheet_user.get('role') == 'admin')


def is_operator(user_id: int) -> bool:
    users = _load()
    if str(user_id) in users.get('operators', {}) or is_admin(user_id):
        return True
    sheet_user = _sheet_user(user_id)
    return bool(sheet_user and sheet_user.get('role') in ('operator', 'admin'))


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
    sheet_user = _sheet_user(user_id)
    if sheet_user:
        return {
            'full_name': sheet_user.get('name', ''),
            'name': sheet_user.get('name', ''),
            'role': sheet_user.get('role', 'operator'),
            'status': sheet_user.get('status', 'active'),
        }
    if uid in users['pending']:
        return users['pending'][uid] | {'role': 'pending'}
    return None


def display_name(user_id: int, telegram_full_name: str = '') -> str:
    user = get_user(user_id) or {}
    return (user.get('full_name') or user.get('name') or telegram_full_name or '').strip()


def add_pending(user_id: int, full_name: str, username: str | None = None) -> None:
    users = _load()
    uid = str(user_id)
    if uid in users['admins'] or uid in users['operators']:
        return
    if _sheet_user(user_id):
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
    try:
        sheets.append_or_update_user(user_id, pending.get('full_name', ''), 'operator', 'active')
    except Exception:
        pass
    return pending


def reject_pending(user_id: int) -> dict | None:
    users = _load()
    pending = users['pending'].pop(str(user_id), None)
    _save(users)
    return pending


def list_users() -> dict:
    users = _load()
    merged = _base()
    merged["admins"].update(users.get("admins", {}))
    merged["operators"].update(users.get("operators", {}))
    merged["pending"].update(users.get("pending", {}))
    try:
        for row in sheets.get_all_sheet_users(include_inactive=False):
            uid = str(row.get("user_id", "")).strip()
            if not uid:
                continue
            item = {"full_name": row.get("name", ""), "name": row.get("name", ""), "status": row.get("status", "active")}
            role = str(row.get("role", "")).strip().lower()
            if role == "admin":
                merged["admins"][uid] = item
                merged["operators"].pop(uid, None)
            elif role == "operator":
                if uid not in merged["admins"]:
                    merged["operators"][uid] = item
    except Exception:
        pass
    return merged
