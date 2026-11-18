"""用户措施执行模块（独立模块）。

按“具体聊天”执行暂停，避免一个聊天的违规影响其他聊天。
"""
import json
import os
import time

_BASE_DIR = "."
FILE = "enforcement.json"
NOTICE_FILE = "enforcement_notices.json"


def init(base_dir):
    global _BASE_DIR
    _BASE_DIR = os.path.abspath(base_dir)
    _migrate_legacy()


def _kind_of_source(source):
    for name in ("chat_guard_alerts.json", "moderation_reports.json"):
        try:
            with open(_path(name), "r", encoding="utf-8") as f:
                rows = json.load(f)
        except Exception:
            continue
        for row in rows:
            if row.get("id") == source:
                return row.get("kind") or ""
    return ""


def _migrate_legacy():
    data = _load()
    changed = False
    for owner, row in data.items():
        until = int(row.get("mutedUntil") or 0)
        if not until:
            continue
        source = row.get("source") or ""
        kind = _kind_of_source(source)
        scope = "module:" + kind if kind in ("claim", "report", "help") else "legacy"
        row.setdefault("mutes", {})[scope] = {
            "mutedUntil": until,
            "reason": row.get("reason") or "旧版全局暂停，已迁移",
            "source": source,
            "updatedAt": _now(),
        }
        row.pop("mutedUntil", None)
        changed = True
    if changed:
        _save(data)


def _path(name):
    return os.path.join(_BASE_DIR, name)


def _load():
    try:
        with open(_path(FILE), "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save(data):
    tmp = _path(FILE) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, _path(FILE))


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
    label = {"module:claim": "失物招领", "module:report": "拾光码", "module:help": "爱心求助"}.get(scope, "聊天")
    _queue_notice(owner, "你在%s的聊天因违规被暂停 %d 分钟；其他板块仍然可以使用。" % (label, int(minutes)))
    return row


def _queue_notice(owner, text):
    try:
        rows = _load_notices()
        rows.append({"owner": owner, "text": text, "at": _now()})
        _save_notices(rows[-1000:])
    except Exception:
        pass


def _load_notices():
    try:
        with open(_path(NOTICE_FILE), "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_notices(rows):
    tmp = _path(NOTICE_FILE) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    os.replace(tmp, _path(NOTICE_FILE))


def pop_notices(owner):
    owner = str(owner or "").strip()[:64]
    rows = _load_notices()
    mine = [r for r in rows if r.get("owner") == owner]
    if mine:
        _save_notices([r for r in rows if r.get("owner") != owner])
    return [str(r.get("text") or "") for r in mine if r.get("text")]


def clear_mute(owner, scope=None):
    owner = str(owner or "").strip()[:64]
    data = _load()
    row = data.get(owner)
    if not row:
        return None
    row.pop("mutedUntil", None)
    if scope is None:
        row["mutes"] = {}
    else:
        row.get("mutes", {}).pop(_scope(scope), None)
    _save(data)
    return row


def check(owner, scope="*", module_scope=""):
    owner = str(owner or "").strip()[:64]
    row = _load().get(owner) or {}
    mutes = row.get("mutes") or {}
    now = _now()
    legacy_until = int(row.get("mutedUntil") or 0)
    if legacy_until > now:
        return False, "本次聊天已被暂停，%s 后可继续" % time.strftime("%m-%d %H:%M", time.localtime(legacy_until / 1000)), legacy_until
    keys = [_scope(scope)]
    if module_scope:
        keys.append(_scope(module_scope))
    keys.append("*")
    for key in keys:
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
        if int(row.get("mutedUntil") or 0):
            rows.append({
                "owner": owner,
                "scope": "legacy",
                "mutedUntil": int(row.get("mutedUntil") or 0),
                "reason": row.get("reason") or "",
                "source": row.get("source") or "",
            })
    rows.sort(key=lambda x: -int(x.get("mutedUntil") or 0))
    return rows[:300]
