"""用户措施执行模块（独立模块）。

只负责执行“警告、暂停聊天、解除”等动作，并保存执行记录。
"""
import json
import os
import time

_BASE_DIR = "."
FILE = "enforcement.json"


def init(base_dir):
    global _BASE_DIR
    _BASE_DIR = os.path.abspath(base_dir)


def _path():
    return os.path.join(_BASE_DIR, FILE)


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


def mute_chat(owner, minutes, reason="", source=""):
    owner = str(owner or "").strip()[:64]
    if not owner:
        return None
    data = _load()
    until = _now() + max(1, int(minutes)) * 60 * 1000
    row = data.get(owner) or {"owner": owner, "actions": []}
    row["mutedUntil"] = until
    row["reason"] = str(reason or "")[:200]
    row["actions"] = (row.get("actions") or [])[-100:]
    row["actions"].append({"at": _now(), "action": "mute_chat",
                           "minutes": int(minutes), "reason": reason, "source": source})
    data[owner] = row
    _save(data)
    return row


def clear_mute(owner):
    owner = str(owner or "").strip()[:64]
    data = _load()
    if owner in data:
        data[owner]["mutedUntil"] = 0
        data[owner]["reason"] = ""
        _save(data)
    return data.get(owner)


def check(owner):
    owner = str(owner or "").strip()[:64]
    row = _load().get(owner) or {}
    until = int(row.get("mutedUntil") or 0)
    if until > _now():
        return False, "本次聊天已被暂停，%s 后可继续" % time.strftime("%m-%d %H:%M", time.localtime(until / 1000)), until
    return True, "", 0


def admin_list():
    data = _load()
    rows = []
    for owner, row in data.items():
        rows.append({
            "owner": owner,
            "mutedUntil": int(row.get("mutedUntil") or 0),
            "reason": row.get("reason") or "",
            "actions": (row.get("actions") or [])[-10:],
        })
    rows.sort(key=lambda x: -int(x.get("mutedUntil") or 0))
    return rows[:300]
