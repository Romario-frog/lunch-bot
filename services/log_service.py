import json
from datetime import datetime
from pathlib import Path
from typing import Any

LOG_FILE = Path('data/logs.json')


def add_log(action: str, actor_id: int, actor_name: str, target_name: str = '', details: dict[str, Any] | None = None) -> None:
    LOG_FILE.parent.mkdir(exist_ok=True)
    logs = []
    if LOG_FILE.exists():
        try:
            logs = json.loads(LOG_FILE.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            logs = []
    logs.append({
        'created_at': datetime.now().isoformat(timespec='seconds'),
        'action': action,
        'actor_id': actor_id,
        'actor_name': actor_name,
        'target_name': target_name,
        'details': details or {},
    })
    LOG_FILE.write_text(json.dumps(logs[-1000:], ensure_ascii=False, indent=2), encoding='utf-8')


def get_last_logs(limit: int = 20) -> list[dict[str, Any]]:
    if not LOG_FILE.exists():
        return []
    try:
        logs = json.loads(LOG_FILE.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        return []
    return logs[-limit:]
