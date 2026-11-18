"""词条生命周期（独立模块）。

只负责：
- 词条状态：active / watch / retired / allow
- 违规命中/正常命中记录
- 月度降级、退役、重新激活

不负责词库匹配、不负责 AI 审核、不负责处罚。
"""
import json
import os
import time

_BASE_DIR = "."
FILE = "lexicon_lifecycle.json"


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


def _word(word):
    return str(word or "").strip()[:20]


def get(word):
    return _load().get(_word(word)) or {"word": _word(word), "status": "active"}


def is_suppressed(word):
    row = _load().get(_word(word)) or {}
    return row.get("status") in ("retired", "allow")


def set_status(word, status, reason=""):
    if status not in ("active", "watch", "retired", "allow"):
        return None
    data = _load()
    w = _word(word)
    row = data.get(w) or {"word": w, "violations": 0, "normals": 0}
    row["status"] = status
    row["statusReason"] = str(reason or "")[:200]
    row["updatedAt"] = _now()
    data[w] = row
    _save(data)
    return row


def record_violation(word, source="", reason=""):
    data = _load()
    w = _word(word)
    row = data.get(w) or {"word": w, "violations": 0, "normals": 0}
    row["violations"] = int(row.get("violations") or 0) + 1
    row["lastViolationAt"] = _now()
    row["lastSource"] = str(source or "")[:40]
    row["lastReason"] = str(reason or "")[:200]
    # 退役后再次出现违规，自动重新激活
    if row.get("status") in ("retired", "allow"):
        row["status"] = "active"
        row["statusReason"] = "再次出现违规，自动重新激活"
    data[w] = row
    _save(data)
    return row


def record_normal(word, source="", reason=""):
    data = _load()
    w = _word(word)
    row = data.get(w) or {"word": w, "violations": 0, "normals": 0}
    row["normals"] = int(row.get("normals") or 0) + 1
    row["lastNormalAt"] = _now()
    row["lastSource"] = str(source or "")[:40]
    row["lastNormalReason"] = str(reason or "")[:200]
    data[w] = row
    _save(data)
    return row


def review():
    """月度老化：正常使用多、长期无违规的词自动降级/退役。"""
    data = _load()
    cutoff = _now() - 90 * 24 * 3600 * 1000
    changed = []
    for w, row in data.items():
        if row.get("status") in ("retired", "allow"):
            continue
        violations = int(row.get("violations") or 0)
        normals = int(row.get("normals") or 0)
        last_v = int(row.get("lastViolationAt") or 0)
        if normals >= 5 and normals > violations * 2 and last_v < cutoff:
            row["status"] = "retired"
            row["statusReason"] = "90 天无违规，且正常使用明显更多"
        elif normals >= 3 and normals > violations:
            row["status"] = "watch"
            row["statusReason"] = "正常使用增多，进入观察"
        else:
            continue
        row["updatedAt"] = _now()
        changed.append({"word": w, "status": row["status"]})
    if changed:
        _save(data)
        try:
            with open(os.path.join(_BASE_DIR, "lexicon_lifecycle_log.json"), "w", encoding="utf-8") as f:
                json.dump({"at": _now(), "changes": changed}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    return changed


def admin_list():
    rows = []
    for w, row in _load().items():
        rows.append({
            "word": w,
            "status": row.get("status") or "active",
            "violations": int(row.get("violations") or 0),
            "normals": int(row.get("normals") or 0),
            "lastViolationAt": int(row.get("lastViolationAt") or 0),
            "lastNormalAt": int(row.get("lastNormalAt") or 0),
            "reason": row.get("statusReason") or "",
        })
    rows.sort(key=lambda x: (x["status"] != "active", -x["violations"]))
    return rows[:300]
