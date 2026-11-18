"""聊天内连续违规升级（独立模块）。

只决定：
- 本次是第几次提醒
- 是否暂停当前板块
- 是否升级为全平台暂停

不负责 AI、不负责发送、不负责页面。
"""
import json
import os
import time

_BASE_DIR = "."
FILE = "chat_escalation.json"
WINDOW_MS = 10 * 60 * 1000


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


def _key(owner, kind, target_id):
    return "%s|%s|%s" % (str(owner or "")[:64], str(kind or "")[:20], str(target_id or "")[:64])


def record(owner, kind, target_id):
    data = _load()
    key = _key(owner, kind, target_id)
    row = data.get(key) or {"owner": owner, "kind": kind, "targetId": target_id, "strikes": []}
    cutoff = _now() - WINDOW_MS
    row["strikes"] = [x for x in (row.get("strikes") or []) if int(x) >= cutoff]
    row["strikes"].append(_now())
    data[key] = row
    _save(data)
    count = len(row["strikes"])
    if count >= 4:
        return {"action": "platform", "strikes": count, "minutes": 120,
                "reason": "同一聊天 10 分钟内第 %d 次违规，升级为全平台暂停 2 小时" % count,
                "countAsTwo": True}
    if count >= 3:
        return {"action": "module", "strikes": count, "minutes": 30,
                "reason": "同一聊天 10 分钟内第 %d 次违规，暂停当前板块 30 分钟" % count,
                "countAsTwo": False}
    return {"action": "warn", "strikes": count, "minutes": 0,
            "reason": "本次是第 %d 次提醒；继续违规将升级" % count,
            "countAsTwo": False}
