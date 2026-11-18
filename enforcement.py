"""用户措施执行模块（独立模块）。

按“具体聊天”执行暂停，避免一个聊天的违规影响其他聊天。
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


def _scope(scope):
    return str(scope or "*")[:120]


def mute_chat(owner, minutes, reason="", source="", scope="*"):
    owner = str(owner or "").strip()[:64]
    if not owner:
        return None
    data = _load()
    row = data.get(owner) or {"owner": owner, "mutes": {}}
    row.setdefault("mutes", {})
    scope = _scope(scope)
    until = _now() + max(1, int(minutes)) * 60 * 1000
    row["mutes"][scope] = {
        "mutedUntil": until,
        "reason": str(reason or "")[:200],
        "source": str(source or "")[:80],
        "updatedAt": _now(),
    }
    data[owner] = row
    _save(data)
    return row


def clear_mute(owner, scope=None):
    owner = str(owner or "").strip()[:64]
    data = _load()
    row = data.get(owner)
    if not row:
        return None
    if scope is None:
        row["mutes"] = {}
    else:
        row.get("mutes", {}).pop(_scope(scope), None)
    _save(data)
    return row


def check(owner, scope="*"):
    owner = str(owner or "").strip()[:64]
    row = _load().get(owner) or {}
    mutes = row.get("mutes") or {}
    now = _now()
    legacy_until = int(row.get("mutedUntil") or 0)
    if legacy_until > now:
        return False, "本次聊天已被暂停，%s 后可继续" % time.strftime("%m-%d %H:%M", time.localtime(legacy_until / 1000)), legacy_until
    for key in (_scope(scope), "*"):
        item = mutes.get(key) or {}
        until = int(item.get("mutedUntil") or 0)
        if until > now:
            return False, "本次聊天已被暂停，%s 后可继续" % time.strftime("%m-%d %H:%M", time.localtime(until / 1000)), until
    return True, "", 0


def admin_list():
    data = _load()
    rows = []
    for owner, row in data.items():
        for scope, item in (row.get("mutes") or {}).items():
            rows.append({
                "owner": owner,
                "scope": scope,
                "mutedUntil": int(item.get("mutedUntil") or 0),
                "reason": item.get("reason") or "",
                "source": item.get("source") or "",
            })
    rows.sort(key=lambda x: -int(x.get("mutedUntil") or 0))
    return rows[:300]
