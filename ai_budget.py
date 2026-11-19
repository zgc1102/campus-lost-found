"""AI 调用预算与限流（独立模块）。

只负责：
- 全站每日 AI 调用上限
- 单 IP 每分钟/每天上限
- 单设备每天上限

不负责模型调用、不负责页面、不负责业务。
"""
import hashlib
import json
import os
import threading
import time
from collections import defaultdict

FILE = "ai_budget.json"
_LOCK = threading.Lock()
_BASE_DIR = "."

# 默认值故意保守：比赛演示够用，被刷时能快速止血。
GLOBAL_DAY = int(os.environ.get("AI_GLOBAL_DAY_LIMIT") or 300)
IP_MINUTE = int(os.environ.get("AI_IP_MINUTE_LIMIT") or 10)
IP_DAY = int(os.environ.get("AI_IP_DAY_LIMIT") or 100)
OWNER_DAY = int(os.environ.get("AI_OWNER_DAY_LIMIT") or 80)


def init(base_dir):
    global _BASE_DIR
    _BASE_DIR = os.path.abspath(base_dir)


def _path():
    return os.path.join(_BASE_DIR, FILE)


def _load():
    try:
        with open(_path(), "r", encoding="utf-8") as f:
            d = json.load(f)
            return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _save(d):
    tmp = _path() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.replace(tmp, _path())


def _today():
    return time.strftime("%Y-%m-%d", time.localtime())


def _hash(s):
    return hashlib.sha256(str(s or "").encode("utf-8")).hexdigest()[:24]


def _prune(d):
    today = _today()
    if d.get("date") != today:
        d["global"] = 0
    d["date"] = today
    for k in ("global",):
        d[k] = int(d.get(k) or 0)
    for k in ("ip_min", "ip_day", "owner_day"):
        src = d.get(k) or {}
        out = {}
        for key, row in src.items():
            if not isinstance(row, dict):
                continue
            if k == "ip_min":
                # 只保留最近 90 秒的计数
                if time.time() - float(row.get("at") or 0) < 90:
                    out[key] = row
            else:
                if row.get("date") == today:
                    out[key] = row
        d[k] = out
    return d


def allow(ip="", owner="", bucket="ask"):
    """在真正调用模型前预占一次额度。返回 (ok, message, retry_seconds)。"""
    with _LOCK:
        d = _prune(_load())
        today = _today()
        d["date"] = today
        if int(d.get("global") or 0) >= GLOBAL_DAY:
            return False, "今日 AI 总调用额度已用完，请明天再试", 3600
        ip_key = _hash(ip or "unknown")
        owner_key = _hash(owner or "anonymous")
        now = time.time()
        im = d["ip_min"].get(ip_key) or {"at": now, "n": 0}
        if now - float(im.get("at") or 0) >= 60:
            im = {"at": now, "n": 0}
        if int(im.get("n") or 0) >= IP_MINUTE:
            retry = max(1, int(60 - (now - float(im.get("at") or now))))
            return False, "请求太频繁，请 %d 秒后再试" % retry, retry
        iday = d["ip_day"].get(ip_key) or {"date": today, "n": 0}
        if iday.get("date") != today:
            iday = {"date": today, "n": 0}
        if int(iday.get("n") or 0) >= IP_DAY:
            return False, "该网络今日 AI 次数已用完", 3600
        oday = d["owner_day"].get(owner_key) or {"date": today, "n": 0}
        if oday.get("date") != today:
            oday = {"date": today, "n": 0}
        if int(oday.get("n") or 0) >= OWNER_DAY:
            return False, "该账号今日 AI 次数已用完", 3600
        # 预占
        d["global"] = int(d.get("global") or 0) + 1
        im["at"] = now
        im["n"] = int(im.get("n") or 0) + 1
        iday["n"] = int(iday.get("n") or 0) + 1
        oday["n"] = int(oday.get("n") or 0) + 1
        d["ip_min"][ip_key] = im
        d["ip_day"][ip_key] = iday
        d["owner_day"][owner_key] = oday
        _save(d)
        return True, "", 0


def stats():
    d = _prune(_load())
    return {
        "date": d.get("date"),
        "global": int(d.get("global") or 0),
        "globalLimit": GLOBAL_DAY,
        "ipMinuteLimit": IP_MINUTE,
        "ipDayLimit": IP_DAY,
        "ownerDayLimit": OWNER_DAY,
    }
