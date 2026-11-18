"""候选词筛选（独立模块）。

只负责统计和过滤，不调用 AI、不写正式词库。
"""
import json
import os
import re

_BASE_DIR = "."

STOP_WORDS = {
    "你好", "什么", "这个", "那个", "可以", "怎么", "为什么", "这样", "那样",
    "不是", "就是", "真的", "一下", "东西", "同学", "老师", "学校", "宿舍",
    "失物", "招领", "爱心", "求助", "捐赠", "手机", "电话", "图片", "消息",
}


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


def _records():
    rows = []
    for name in ("moderation_reports.json", "chat_guard_alerts.json"):
        for item in _load(name):
            ai = item.get("ai") or {}
            text = " ".join(str(x) for x in (
                item.get("reason"), item.get("detail"), ai.get("reason"),
                item.get("text"), " ".join(item.get("localHits") or [])
            ) if x)
            rows.append({
                "text": text,
                "owner": item.get("senderOwner") or item.get("targetOwner") or item.get("reporter") or "",
                "chat": item.get("targetId") or item.get("alertId") or item.get("id") or "",
            })
    return rows


def rank(high, mid):
    records = _records()
    existing = set()
    try:
        with open(_path("chat_lexicon.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
            existing = set(data.get("high") or []) | set(data.get("mid") or [])
    except Exception:
        pass

    result = {"high": [], "mid": [], "rejected": []}
    for level, words in (("high", high), ("mid", mid)):
        for raw in words:
            word = str(raw or "").strip()
            if len(word) < 2 or len(word) > 8 or word in STOP_WORDS or word in existing:
                result["rejected"].append({"word": word, "reason": "长度/停用词/已存在"})
                continue
            if re.fullmatch(r"[\W_]+", word) or word.isdigit():
                result["rejected"].append({"word": word, "reason": "非文字"})
                continue
            hits = [r for r in records if word in r["text"]]
            owners = {r["owner"] for r in hits if r["owner"]}
            chats = {r["chat"] for r in hits if r["chat"]}
            need = 1 if level == "high" else 2
            if len(hits) < need or len(owners) < need:
                result["rejected"].append({
                    "word": word,
                    "reason": "频次不足：%d 次 / %d 用户 / %d 聊天" % (len(hits), len(owners), len(chats))
                })
                continue
            result[level].append({
                "word": word,
                "count": len(hits),
                "owners": len(owners),
                "chats": len(chats),
            })
    result["high"] = result["high"][:12]
    result["mid"] = result["mid"][:12]
    return result
