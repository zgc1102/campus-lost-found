"""独立本地词库。

- 词库存放在 chat_lexicon.json
- 每月自动检查一次更新窗口
- 只负责词条匹配，不做 AI、不做处罚
"""
import json
import os
import threading
import time
import lexicon_lifecycle

_BASE_DIR = "."
FILE = "chat_lexicon.json"
CANDIDATE_FILE = "chat_lexicon_candidates.json"
_LOCK = threading.Lock()

DEFAULT_HIGH = [
    "傻逼", "煞笔", "去死", "弄死你", "杀了你", "约炮", "裸照", "裸聊", "开房",
    "包养", "代考", "替考", "代写", "卖答案", "扫码付款", "先转账", "验证码给我",
    "操你", "草泥马", "你妈死了", "陪睡",
]
DEFAULT_MID = [
    "滚", "废物", "脑残", "二百五", "贱", "恶心", "骚扰", "骂你",
    "加微信", "私聊", "包夜", "多少钱", "蠢货", "混蛋", "王八蛋",
    "神经病", "不要脸", "垃圾", "狗东西",
]


def init(base_dir):
    global _BASE_DIR
    _BASE_DIR = os.path.abspath(base_dir)
    _ensure()


def _path(name):
    return os.path.join(_BASE_DIR, name)


def _read(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, type(default)) else default
    except Exception:
        return default


def _write(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _ensure():
    with _LOCK:
        if not os.path.exists(_path(FILE)):
            _write(_path(FILE), {
                "version": 1,
                "updatedAt": int(time.time() * 1000),
                "high": DEFAULT_HIGH,
                "mid": DEFAULT_MID,
            })


def load():
    _ensure()
    return _read(_path(FILE), {})


def scan(text):
    data = load()
    t = str(text or "")
    high = [w for w in data.get("high", [])
            if w and w in t and not lexicon_lifecycle.is_suppressed(w)]
    mid = [w for w in data.get("mid", [])
           if w and w in t and not lexicon_lifecycle.is_suppressed(w)]
    return high + mid


def add_terms(high=None, mid=None, source="manual"):
    with _LOCK:
        data = _read(_path(FILE), {})
        data.setdefault("high", DEFAULT_HIGH)
        data.setdefault("mid", DEFAULT_MID)
        for w in high or []:
            w = str(w).strip()[:20]
            if w and w not in data["high"]:
                data["high"].append(w)
        for w in mid or []:
            w = str(w).strip()[:20]
            if w and w not in data["mid"]:
                data["mid"].append(w)
        data["version"] = int(data.get("version") or 1) + 1
        data["updatedAt"] = int(time.time() * 1000)
        data["lastSource"] = source
        _write(_path(FILE), data)
        return data


def _apply_candidates():
    rows = _read(_path(CANDIDATE_FILE), {})
    if not rows:
        return None
    high = [w for w in rows.get("high", []) if isinstance(w, str) and 2 <= len(w) <= 12]
    mid = [w for w in rows.get("mid", []) if isinstance(w, str) and 2 <= len(w) <= 12]
    data = add_terms(high, mid, "monthly")
    try:
        os.remove(_path(CANDIDATE_FILE))
    except Exception:
        pass
    return data


def monthly_check():
    data = load()
    last = int(data.get("updatedAt") or 0)
    changed = lexicon_lifecycle.review()
    if time.time() * 1000 - last > 30 * 24 * 3600 * 1000:
        return _apply_candidates() or add_terms([], [], "monthly-empty")
    return changed


def _worker():
    while True:
        try:
            monthly_check()
        except Exception:
            pass
        time.sleep(6 * 3600)


def start_worker():
    threading.Thread(target=_worker, daemon=True).start()
