"""每月词库候选发现（独立模块）。

读取最近 30 天的违规记录，让 AI 只提取明确的违规词/短语，
写入 chat_lexicon_candidates.json，等待 chat_lexicon 的月度任务合并。
"""
import json
import os
import re
import threading
import time
import urllib.request
import lexicon_candidate
import lexicon_shadow

_BASE_DIR = "."
STATE_FILE = "lexicon_miner_state.json"
CANDIDATE_FILE = "chat_lexicon_candidates.json"


def init(base_dir):
    global _BASE_DIR
    _BASE_DIR = os.path.abspath(base_dir)
    lexicon_candidate.init(_BASE_DIR)
    lexicon_shadow.init(_BASE_DIR)


def _path(name):
    return os.path.join(_BASE_DIR, name)


def _load(name, default):
    try:
        with open(_path(name), "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, type(default)) else default
    except Exception:
        return default


def _save(name, data):
    tmp = _path(name) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, _path(name))


def _now():
    return int(time.time() * 1000)


def _config():
    return {
        "api_key": os.environ.get("REPORT_AI_API_KEY", "").strip(),
        "base_url": os.environ.get("REPORT_AI_BASE_URL", "https://api.deepseek.com").strip().rstrip("/"),
        "model": os.environ.get("REPORT_AI_MODEL", "deepseek-flash").strip(),
    }


def _samples():
    rows = []
    for name in ("moderation_reports.json", "chat_guard_alerts.json"):
        for item in _load(name, []):
            if _now() - int(item.get("createdAt") or 0) > 30 * 24 * 3600 * 1000:
                continue
            ai = item.get("ai") or {}
            text = " ".join(str(x) for x in (
                item.get("reason"), item.get("detail"), ai.get("reason"),
                item.get("text"), " ".join(item.get("localHits") or [])
            ) if x)
            if text:
                rows.append(text[:300])
    return rows[-60:]


def mine():
    samples = _samples()
    if not samples:
        return None
    cfg = _config()
    if not cfg["api_key"]:
        return None
    prompt = (
        "从下面的校园聊天违规记录中提取明确、可复用的违规词或短语。"
        "只提取真正有风险的词，不要把普通词、人名、物品名、地名放进去。"
        "最多 12 个，每个 2 到 8 个汉字。只输出 JSON："
        '{"high":["..."],"mid":["..."]}。\n\n'
        + "\n".join(samples)
    )
    payload = {
        "model": cfg["model"],
        "temperature": 0,
        "max_tokens": 300,
        "response_format": {"type": "json_object"},
        "thinking": {"type": "disabled"},
        "messages": [
            {"role": "system", "content": "你是词库维护员，只输出 JSON。"},
            {"role": "user", "content": prompt},
        ],
    }
    req = urllib.request.Request(
        cfg["base_url"] + "/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + cfg["api_key"]},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"] or ""
        m = re.search(r"\{[\s\S]*\}", content)
        obj = json.loads(m.group(0)) if m else {}
        high = [str(x).strip() for x in obj.get("high", []) if 2 <= len(str(x).strip()) <= 8]
        mid = [str(x).strip() for x in obj.get("mid", []) if 2 <= len(str(x).strip()) <= 8]
        if not high and not mid:
            return None
        ranked = lexicon_candidate.rank(high, mid)
        approved, shadow_rejected = lexicon_shadow.evaluate(ranked)
        approved["rejected"] = (ranked.get("rejected") or []) + shadow_rejected
        approved["at"] = _now()
        _save(CANDIDATE_FILE, approved)
        _save(STATE_FILE, {"lastAt": _now(),
                           "high": len(approved.get("high") or []),
                           "mid": len(approved.get("mid") or [])})
        return approved
    except Exception:
        return None


def _worker():
    while True:
        try:
            state = _load(STATE_FILE, {})
            if _now() - int(state.get("lastAt") or 0) > 30 * 24 * 3600 * 1000:
                mine()
        except Exception:
            pass
        time.sleep(6 * 3600)


def start_worker():
    threading.Thread(target=_worker, daemon=True).start()
