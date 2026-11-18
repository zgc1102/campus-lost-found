"""独立用户风险档案。

只记录安全违规次数和风险等级，不负责审核、聊天、举报或管理端页面。
"""
import json
import os
import time

_BASE_DIR = "."
RISK_FILE = "risk_profiles.json"


def init(base_dir):
    global _BASE_DIR
    _BASE_DIR = os.path.abspath(base_dir)


def _path():
    return os.path.join(_BASE_DIR, RISK_FILE)


def _load():
    try:
        with open(_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save(data):
    tmp = _path() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, _path())


def _now():
    return int(time.time() * 1000)


def note_violation(owner, source, reason="", risk=0, report_id="", scope=""):
    owner = str(owner or "").strip()[:64]
    if not owner:
        return None
    data = _load()
    row = data.get(owner) or {"owner": owner, "events": []}
    row["events"].append({
        "at": _now(),
        "source": str(source or "")[:30],
        "reason": str(reason or "")[:200],
        "risk": max(0, min(100, int(risk or 0))),
        "reportId": str(report_id or "")[:64],
        "scope": str(scope or "")[:120],
    })
    row["events"] = row["events"][-100:]
    data[owner] = row
    _save(data)
    return row


def get_level(owner):
    owner = str(owner or "").strip()[:64]
    data = _load()
    row = data.get(owner) or {}
    cutoff = _now() - 30 * 24 * 3600 * 1000
    events = [e for e in (row.get("events") or []) if int(e.get("at") or 0) >= cutoff]
    high = [e for e in events if int(e.get("risk") or 0) >= 80]
    count = len(events)
    if count >= 5 or len(high) >= 3:
        level = "restricted"
    elif count >= 3 or len(high) >= 2:
        level = "high"
    elif count >= 1:
        level = "watch"
    else:
        level = "normal"
    return {"owner": owner, "level": level, "count": count, "highCount": len(high)}


def needs_full_scan(owner, scope=""):
    if is_watched(owner, scope):
        return True
    return get_level(owner).get("level") in ("high", "restricted")


def is_watched(owner, scope="", hours=24):
    owner = str(owner or "").strip()[:64]
    data = _load()
    row = data.get(owner) or {}
    cutoff = _now() - max(1, int(hours)) * 3600 * 1000
    return any(int(e.get("at") or 0) >= cutoff
               and int(e.get("risk") or 0) >= 70
               and (not scope or e.get("scope") == scope)
               for e in row.get("events") or [])


def admin_list():
    data = _load()
    rows = []
    for owner, row in data.items():
        info = get_level(owner)
        info["lastAt"] = max([int(e.get("at") or 0) for e in row.get("events") or []] or [0])
        rows.append(info)
    rows.sort(key=lambda x: (x.get("level") != "normal", -x.get("count", 0), -x.get("lastAt", 0)))
    return rows[:300]
