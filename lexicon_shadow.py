"""候选词影子测试（独立模块）。

只做误伤评估，不写正式词库、不触发处罚。
"""
import json
import os

_BASE_DIR = "."


def init(base_dir):
    global _BASE_DIR
    _BASE_DIR = os.path.abspath(base_dir)


def _path(name):
    return os.path.join(_BASE_DIR, name)


def _load(name):
    try:
        with open(_path(name), "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def _normal_messages():
    """取最近聊天里没有被标记违规的消息，做影子样本。"""
    bad = set()
    for name in ("moderation_reports.json", "chat_guard_alerts.json"):
        for item in _load(name):
            bad.add(str(item.get("targetId") or ""))
            bad.add(str(item.get("alertId") or ""))
            bad.add(str(item.get("id") or ""))
    rows = []
    for name in ("claims.json", "help_tasks.json", "tag_reports.json"):
        for item in _load(name):
            if str(item.get("id")) in bad:
                continue
            for m in (item.get("messages") or []):
                text = str(m.get("text") or "")
                if text:
                    rows.append(text)
    return rows


def evaluate(candidates):
    total = _normal_messages()
    approved = {"high": [], "mid": []}
    rejected = []
    for level in ("high", "mid"):
        for item in candidates.get(level) or []:
            word = item.get("word") if isinstance(item, dict) else str(item)
            if not word:
                continue
            hit = sum(1 for text in total if word in text)
            limit = max(5, int(len(total) * 0.01))
            if hit > limit:
                rejected.append({"word": word, "reason": "正常消息误命中 %d 条" % hit})
                continue
            approved[level].append(item if isinstance(item, dict) else {"word": word})
    return approved, rejected
