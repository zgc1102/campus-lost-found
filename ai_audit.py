"""AI 调用审计（只记录，不参与审核/限流）。

记录内容：
- 时间、接口、模型
- 用户问题预览（最多 200 字，脱敏）
- 输入/输出/总 tokens
- 耗时、状态

不记录：
- API Key
- 完整聊天记录
- 完整手机号

数据只写入 private/ai_audit.json，不进入静态目录。
"""
import json
import os
import re
import threading
import time
from urllib.parse import urlparse

FILE = "ai_audit.json"
_LOCK = threading.Lock()
_BASE_DIR = "."
_MAX_ROWS = 500
_RETENTION_MS = 7 * 24 * 60 * 60 * 1000

_PHONE = re.compile(r"1[3-9]\d{9}")
_TOKEN = re.compile(r"sk-[A-Za-z0-9_-]{8,}|Bearer\s+[A-Za-z0-9._-]+")


def init(base_dir):
    global _BASE_DIR
    _BASE_DIR = os.path.abspath(base_dir)
    os.makedirs(os.path.join(_BASE_DIR, "private"), exist_ok=True)


def _path():
    return os.path.join(_BASE_DIR, "private", FILE)


def _load():
    try:
        with open(_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(rows):
    os.makedirs(os.path.dirname(_path()), exist_ok=True)
    tmp = _path() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    os.replace(tmp, _path())


def _mask(text):
    text = _PHONE.sub(lambda m: m.group(0)[:3] + "****" + m.group(0)[-4:], text or "")
    text = _TOKEN.sub("***", text)
    return text


def _prompt_preview(payload):
    """只取最后一条 user 文本，不记录 system prompt 和图片 base64。"""
    try:
        messages = payload.get("messages") if isinstance(payload, dict) else None
        if not isinstance(messages, list):
            return ""
        for m in reversed(messages):
            if not isinstance(m, dict) or m.get("role") != "user":
                continue
            content = m.get("content")
            if isinstance(content, str):
                text = content.strip()
            elif isinstance(content, list):
                parts = []
                for x in content:
                    if isinstance(x, dict) and x.get("type") == "text":
                        parts.append(str(x.get("text") or ""))
                text = " ".join(parts).strip()
            else:
                continue
            # RAG 的 user 消息前面是资料，真正的提问在“问题：”后面。
            if "问题：" in text:
                text = text.rsplit("问题：", 1)[-1].strip()
            return _mask(text)[:200]
        return ""
    except Exception:
        return ""


def _endpoint_path(endpoint):
    try:
        p = urlparse(str(endpoint or ""))
        return (p.path or "")[:120]
    except Exception:
        return ""


def _source(payload):
    """根据 prompt 特征标出调用来源，避免所有记录都只显示 /chat/completions。"""
    try:
        messages = payload.get("messages") if isinstance(payload, dict) else []
        text = " ".join(str(m.get("content") or "") for m in messages if isinstance(m, dict))
    except Exception:
        text = ""
    if "资料：" in text and "问题：" in text:
        return "rag"
    if "信息整理助手" in text:
        return "format"
    if "寻物侦探" in text:
        return "detective"
    if "核验助手" in text or "核验" in text:
        return "claim_check"
    if "图片安全审核" in text or "图片识别" in text:
        return "vision"
    return "llm"


def record(endpoint, payload, response, started, status=200, error=""):
    """成功/失败都记录；失败时 response 可以为 None。"""
    try:
        usage = (response or {}).get("usage") if isinstance(response, dict) else {}
        usage = usage if isinstance(usage, dict) else {}
        model = ""
        if isinstance(payload, dict):
            model = str(payload.get("model") or "")[:80]
        row = {
            "at": int(time.time() * 1000),
            "endpoint": _endpoint_path(endpoint),
            "source": _source(payload),
            "model": model,
            "prompt": _prompt_preview(payload),
            "promptTokens": int(usage.get("prompt_tokens") or 0),
            "completionTokens": int(usage.get("completion_tokens") or 0),
            "totalTokens": int(usage.get("total_tokens") or 0),
            "ms": max(0, int((time.time() - float(started or time.time())) * 1000)),
            "status": int(status or 0),
            "error": _mask(str(error or ""))[:120],
        }
        cutoff = int(time.time() * 1000) - _RETENTION_MS
        with _LOCK:
            rows = [x for x in _load() if isinstance(x, dict) and int(x.get("at") or 0) >= cutoff]
            rows.append(row)
            _save(rows[-_MAX_ROWS:])
    except Exception:
        # 审计失败绝不能影响 AI 主流程
        pass


def recent(limit=100):
    try:
        rows = _load()
        return rows[-max(1, min(500, int(limit or 100))):]
    except Exception:
        return []
