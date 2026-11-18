"""独立申诉模块。

- 保存申诉
- AI 自动复核
- 通过后自动解除聊天暂停
- 不等待人工
"""
import json
import os
import queue
import re
import threading
import time
import uuid
import urllib.error
import urllib.request

import enforcement

_BASE_DIR = "."
FILE = "appeals.json"
_QUEUE = queue.Queue()
_STARTED = False


def init(base_dir):
    global _BASE_DIR
    _BASE_DIR = os.path.abspath(base_dir)


def _path():
    return os.path.join(_BASE_DIR, FILE)


def _load():
    try:
        with open(_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(rows):
    tmp = _path() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rows[-3000:], f, ensure_ascii=False, indent=2)
    os.replace(tmp, _path())


def _now():
    return int(time.time() * 1000)


def _clip(v, n):
    return str(v or "").strip()[:n]


def _config():
    return {
        "api_key": os.environ.get("REPORT_AI_API_KEY", "").strip(),
        "base_url": os.environ.get("REPORT_AI_BASE_URL", "https://api.deepseek.com").strip().rstrip("/"),
        "model": os.environ.get("REPORT_AI_MODEL", "deepseek-flash").strip(),
    }


def _ai_review(appeal):
    cfg = _config()
    if not cfg["api_key"]:
        return None
    evidence = appeal.get("evidence") or {}
    prompt = (
        "你是校园公益平台的申诉复核员。用户因聊天违规被 AI 自动处理，现在提出申诉。"
        "请判断原处理是否明显误判。只输出 JSON："
        '{"decision":"approved|rejected","reason":"不超过80字"}。\n\n'
        "申诉理由：%s\n原处理说明：%s\n聊天片段：%s"
        % (_clip(appeal.get("reason"), 800),
           _clip(evidence.get("reason"), 500),
           _clip(evidence.get("text"), 1200))
    )
    payload = {
        "model": cfg["model"],
        "temperature": 0,
        "max_tokens": 200,
        "response_format": {"type": "json_object"},
        "thinking": {"type": "disabled"},
        "messages": [
            {"role": "system", "content": "你是克制、公正的申诉复核员，只输出 JSON。"},
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
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"] or ""
        m = re.search(r"\{[\s\S]*\}", content)
        obj = json.loads(m.group(0)) if m else {}
        decision = obj.get("decision")
        if decision not in ("approved", "rejected"):
            decision = "rejected"
        return {"decision": decision, "reason": _clip(obj.get("reason"), 240),
                "model": cfg["model"], "source": "ai", "at": _now()}
    except Exception as e:
        return {"decision": "rejected", "reason": "AI 复核暂时不可用：" + str(e)[:80],
                "model": cfg["model"], "source": "ai-error", "at": _now()}


def _process(appeal_id):
    rows = _load()
    appeal = next((r for r in rows if r.get("id") == appeal_id), None)
    if not appeal:
        return
    result = _ai_review(appeal)
    if not result:
        result = {"decision": "approved", "reason": "未配置申诉 AI，自动解除本次暂停",
                  "source": "fallback", "at": _now()}
    rows = _load()
    appeal = next((r for r in rows if r.get("id") == appeal_id), None)
    if not appeal:
        return
    appeal["status"] = result.get("decision") or "rejected"
    appeal["ai"] = result
    appeal["handledAt"] = _now()
    _save(rows)
    if appeal.get("status") == "approved":
        try:
            enforcement.clear_mute(appeal.get("owner"))
        except Exception:
            pass


def _worker():
    while True:
        appeal_id = _QUEUE.get()
        try:
            _process(appeal_id)
        except Exception:
            pass
        finally:
            _QUEUE.task_done()


def start_worker():
    global _STARTED
    if _STARTED:
        return
    _STARTED = True
    threading.Thread(target=_worker, daemon=True).start()


def create(owner, report_id, alert_id, reason, kind="", target_id="", evidence=None):
    rows = _load()
    owner = _clip(owner, 64)
    report_id = _clip(report_id, 64)
    alert_id = _clip(alert_id, 64)
    for row in rows:
        if (row.get("owner") == owner
                and row.get("reporterId") == report_id
                and row.get("alertId") == alert_id
                and row.get("status") == "reviewing"):
            return row, True
    row = {
        "id": "ap_" + uuid.uuid4().hex[:12],
        "owner": owner,
        "reporterId": report_id,
        "alertId": alert_id,
        "kind": _clip(kind, 20),
        "targetId": _clip(target_id, 64),
        "reason": _clip(reason, 1000),
        "evidence": evidence or {},
        "status": "reviewing",
        "createdAt": _now(),
    }
    rows.append(row)
    _save(rows)
    _QUEUE.put(row["id"])
    return row, False


def mine(owner):
    rows = _load()
    return [r for r in rows if r.get("owner") == owner][-100:][::-1]


def admin_list():
    return _load()[-300:][::-1]


def admin_update(appeal_id, status, note="", actor=""):
    if status not in ("approved", "rejected"):
        return None
    rows = _load()
    row = next((r for r in rows if r.get("id") == appeal_id), None)
    if not row:
        return None
    row["status"] = status
    row["note"] = _clip(note, 500)
    row["handledAt"] = _now()
    row["handledBy"] = _clip(actor, 40)
    _save(rows)
    if status == "approved":
        try:
            enforcement.clear_mute(row.get("owner"))
        except Exception:
            pass
    return row
