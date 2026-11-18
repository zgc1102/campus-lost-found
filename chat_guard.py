"""聊天实时安全守卫（独立模块）。

只负责聊天消息的快速风险发现和 AI 复核：
- 本地规则先秒级命中
- 命中后异步调用 DeepSeek 复核
- 结果给聊天界面做提示/警告

不负责举报记录、聊天发送、管理端页面。
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
import risk_profile
import moderation_policy
import enforcement

_LOCK = threading.Lock()
_QUEUE = queue.Queue()
_STARTED = False
_BASE_DIR = "."
ALERT_FILE = "chat_guard_alerts.json"

_HIGH = (
    "傻逼", "煞笔", "去死", "弄死你", "杀了你", "约炮", "裸照", "裸聊", "开房",
    "包养", "代考", "替考", "代写", "卖答案", "扫码付款", "先转账", "验证码给我",
    "操你", "草泥马", "你妈死了", "陪睡",
)
_MID = (
    "滚", "废物", "脑残", "二百五", "贱", "恶心", "骚扰", "骂你",
    "加微信", "私聊", "包夜", "多少钱", "蠢货", "混蛋", "王八蛋",
    "神经病", "不要脸", "垃圾", "狗东西",
)


def init(base_dir):
    global _BASE_DIR
    _BASE_DIR = os.path.abspath(base_dir)


def _path():
    return os.path.join(_BASE_DIR, ALERT_FILE)


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
        json.dump(rows[-2000:], f, ensure_ascii=False, indent=2)
    os.replace(tmp, _path())


def _now():
    return int(time.time() * 1000)


def _clip(v, n):
    return str(v or "").strip()[:n]


def _context(messages):
    rows = []
    for m in (messages or [])[-12:]:
        who = "发布者" if m.get("from") == "owner" else "申请人"
        rows.append("%s：%s" % (who, _clip(m.get("text"), 300)))
    return "\n".join(rows)


def local_hits(text):
    t = str(text or "")
    hits = [w for w in _HIGH if w in t]
    hits += [w for w in _MID if w in t]
    return hits


def _last_alert(kind, target_id):
    rows = _load()
    matches = [r for r in rows if r.get("kind") == kind and r.get("targetId") == target_id]
    return matches[-1] if matches else None


def status(kind, target_id, owner):
    alert = _last_alert(kind, target_id)
    if not alert:
        return {"active": False, "status": "", "warning": "", "reportId": ""}
    warning = ""
    if (alert.get("warningFor") == owner
            and alert.get("warning")
            and alert.get("status") not in ("dismissed", "resolved")):
        warning = alert.get("warning")
    return {
        "active": alert.get("status") in ("reviewing", "reviewed",
                                          "auto_warned", "auto_limited"),
        "status": alert.get("status") or "",
        "warning": warning,
        "reportId": alert.get("id") or "",
    }


def admin_list():
    with _LOCK:
        rows = _load()
    return rows[-300:][::-1]


def _ai_config():
    return {
        "api_key": os.environ.get("REPORT_AI_API_KEY", "").strip(),
        "base_url": os.environ.get("REPORT_AI_BASE_URL", "https://api.deepseek.com").strip().rstrip("/"),
        "model": os.environ.get("REPORT_AI_MODEL", "deepseek-flash").strip(),
    }


def _ai_review(alert):
    cfg = _ai_config()
    if not cfg["api_key"]:
        return None
    prompt = (
        "你是校园失物招领平台的聊天安全审核员。判断下面聊天是否包含"
        "辱骂威胁、色情擦边、诈骗转账、广告刷屏、代考或其他违规。"
        "只输出 JSON，不要解释："
        '{"verdict":"safe|suspicious|violation","risk":0-100,'
        '"categories":["..."],"reason":"不超过60字"}\n\n'
        "当前消息：%s\n最近对话：\n%s"
        % (_clip(alert.get("text"), 400), _context(alert.get("messages")))
    )
    payload = {
        "model": cfg["model"],
        "temperature": 0,
        "max_tokens": 300,
        "response_format": {"type": "json_object"},
        "thinking": {"type": "disabled"},
        "messages": [
            {"role": "system", "content": "你是严格但克制的校园安全审核员，只输出 JSON。"},
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
        with urllib.request.urlopen(req, timeout=12) as r:
            data = json.loads(r.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"] or ""
        m = re.search(r"\{[\s\S]*\}", content)
        obj = json.loads(m.group(0)) if m else {}
        verdict = obj.get("verdict")
        if verdict not in ("safe", "suspicious", "violation"):
            verdict = "suspicious"
        try:
            risk = max(0, min(100, int(obj.get("risk") or 0)))
        except Exception:
            risk = 0
        cats = obj.get("categories")
        return {
            "ok": True,
            "source": "ai",
            "verdict": verdict,
            "risk": risk,
            "categories": [str(x)[:30] for x in cats[:8]] if isinstance(cats, list) else [],
            "reason": _clip(obj.get("reason"), 240),
            "model": cfg["model"],
            "at": _now(),
        }
    except Exception as e:
        return {"ok": False, "source": "ai-error", "verdict": "suspicious", "risk": 0,
                "categories": [], "reason": "AI 复核暂时不可用：" + str(e)[:60], "model": cfg["model"], "at": _now()}


def _process(alert_id):
    with _LOCK:
        rows = _load()
        alert = next((r for r in rows if r.get("id") == alert_id), None)
    if not alert:
        return
    result = _ai_review(alert)
    if not result:
        return
    if (not result.get("reason") or int(result.get("risk") or 0) == 0) and alert.get("localHits"):
        result = {
            "ok": True,
            "source": "local+ai-fallback",
            "verdict": "violation",
            "risk": 82,
            "categories": ["言语骚扰"],
            "reason": "AI 复核返回空结果，本地规则命中：" + "、".join(alert.get("localHits") or [])[:60],
            "model": result.get("model") or "",
            "at": _now(),
        }
    with _LOCK:
        rows = _load()
        alert = next((r for r in rows if r.get("id") == alert_id), None)
        if not alert:
            return
        alert["ai"] = result
        alert["ai"] = result
        alert["reviewedAt"] = _now()
        sender = alert.get("senderOwner") or ""
        history = risk_profile.get_level(sender).get("level", "normal")
        decision = moderation_policy.decide(result.get("verdict"), result.get("risk"),
                                            result.get("categories"), history)
        alert["action"] = decision
        alert["status"] = decision.get("status") or "auto_safe"
        if decision.get("mute_minutes"):
            try:
                enforcement.mute_chat(sender, decision.get("mute_minutes"),
                                      decision.get("reason"), alert.get("id"))
                alert["mutedUntil"] = _now() + int(decision.get("mute_minutes")) * 60 * 1000
            except Exception:
                pass
        if decision.get("action") in ("warn", "mute_chat"):
            alert["warningFor"] = sender
            alert["warning"] = ("AI 检测到本次聊天内容存在违规风险，相关记录已保存。请立即停止不当言行。"
                                if decision.get("action") == "warn"
                                else "AI 检测到本次聊天内容存在严重违规风险，聊天已被暂停。相关记录已保存。")
            alert["warningAt"] = _now()
        if result.get("verdict") == "violation" and int(result.get("risk") or 0) >= 70:
            try:
                risk_profile.note_violation(sender, "chat_guard",
                                            result.get("reason"), result.get("risk"), alert.get("id"))
            except Exception:
                pass
        _save(rows)


def _worker():
    while True:
        alert_id = _QUEUE.get()
        try:
            _process(alert_id)
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


def observe(kind, target_id, item_id, from_side, target_owner, text, messages, sender_owner=""):
    """每条聊天消息调用；本地命中或高风险用户才进入 AI 队列。"""
    hits = local_hits(text)
    forced = risk_profile.needs_full_scan(sender_owner)
    if not hits and not forced:
        return None
    alert_id = "cg_" + uuid.uuid4().hex[:12]
    row = {
        "id": alert_id,
        "kind": kind,
        "targetId": target_id,
        "itemId": item_id or "",
        "fromSide": from_side,
        "senderOwner": sender_owner or "",
        "targetOwner": target_owner or "",
        "text": _clip(text, 500),
        "messages": (messages or [])[-12:],
        "localHits": hits,
        "forced": forced,
        "status": "reviewing",
        "createdAt": _now(),
    }
    with _LOCK:
        rows = _load()
        rows.append(row)
        _save(rows)
    _QUEUE.put(alert_id)
    return row
