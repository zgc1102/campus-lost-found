"""独立申诉模块。

只负责申诉记录和处理，不负责审核、聊天、处罚执行。
"""
import json
import os
import time
import uuid

_BASE_DIR = "."
FILE = "appeals.json"


def init(base_dir):
    global _BASE_DIR
    _BASE_DIR = os.path.abspath(base_dir)


def _path():
    return os.path.join(_BASE_DIR, FILE)


def _load():
    try:
        with open(_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(rows):
    tmp = _path() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rows[-3000:], f, ensure_ascii=False, indent=2)
    os.replace(tmp, _path())


def _now():
    return int(time.time() * 1000)


def _clip(v, n):
    return str(v or "").strip()[:n]


def create(owner, report_id, alert_id, reason, kind="", target_id=""):
    rows = _load()
    owner = _clip(owner, 64)
    report_id = _clip(report_id, 64)
    alert_id = _clip(alert_id, 64)
    for row in rows:
        if (row.get("owner") == owner
                and row.get("reporterId") == report_id
                and row.get("alertId") == alert_id
                and row.get("status") == "pending"):
            return row, True
    row = {
        "id": "ap_" + uuid.uuid4().hex[:12],
        "owner": owner,
        "reporterId": report_id,
        "alertId": alert_id,
        "kind": _clip(kind, 20),
        "targetId": _clip(target_id, 64),
        "reason": _clip(reason, 1000),
        "status": "pending",
        "createdAt": _now(),
    }
    rows.append(row)
    _save(rows)
    return row, False


def mine(owner):
    rows = _load()
    return [r for r in rows if r.get("owner") == owner][-100:][::-1]


def admin_list():
    return _load()[-300:][::-1]


def admin_update(appeal_id, status, note="", actor=""):
    if status not in ("approved", "rejected"):
        return None
    rows = _load()
    row = next((r for r in rows if r.get("id") == appeal_id), None)
    if not row:
        return None
    row["status"] = status
    row["note"] = _clip(note, 500)
    row["handledAt"] = _now()
    row["handledBy"] = _clip(actor, 40)
    _save(rows)
    return row
