"""独立举报与安全审核模块。

这个模块只负责举报：
- 举报记录
- 聊天快照
- AI 调查
- 管理端处理记录

不负责物品审核、登录、通知列表或聊天发送。
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

REPORT_FILE = "moderation_reports.json"
AUDIT_FILE = "moderation_audit.json"


def init(base_dir):
    global _BASE_DIR
    _BASE_DIR = os.path.abspath(base_dir)


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


def _clip(v, n):
    return str(v or "").strip()[:n]


def _text_of(messages):
    rows = []
    for m in messages[-60:]:
        who = "发布者" if m.get("from") == "owner" else "申请人"
        rows.append("%s：%s" % (who, _clip(m.get("text"), 500)))
    return "\n".join(rows)


def _local_risk(report):
    text = _text_of(report.get("messages") or [])
    hits = []
    high = ("约炮", "裸照", "开房", "包养", "代考", "替考", "转账", "验证码", "二维码付款")
    mid = ("傻逼", "滚", "去死", "骚扰", "加微信", "私聊", "多少钱", "包夜")
    for w in high:
        if w in text:
            hits.append(w)
    for w in mid:
        if w in text:
            hits.append(w)
    score = min(95, 30 + len(hits) * 15) if hits else 5
    verdict = "violation" if score >= 70 else "suspicious" if score >= 40 else "safe"
    return {
        "ok": True,
        "source": "local",
        "verdict": verdict,
        "risk": score,
        "categories": ["言语骚扰"] if hits else [],
        "reason": ("命中本地规则：" + "、".join(hits[:8])) if hits else "本地规则未发现明显违规",
        "model": "",
        "at": _now()
    }


def _ai_config():
    return {
        "api_key": os.environ.get("REPORT_AI_API_KEY", "").strip(),
        "base_url": os.environ.get("REPORT_AI_BASE_URL", "https://api.deepseek.com").strip().rstrip("/"),
        "model": os.environ.get("REPORT_AI_MODEL", "deepseek-chat").strip(),
    }


def _call_ai(report):
    cfg = _ai_config()
    if not cfg["api_key"]:
        return None
    text = _text_of(report.get("messages") or [])
    prompt = (
        "你是校园失物招领平台的安全审核员。只根据下面这段匿名聊天判断是否存在"
        "言语骚扰、色情擦边、诈骗、广告刷屏、代考或其他违规。"
        "不要编造，不要处罚，只输出 JSON："
        '{"verdict":"safe|suspicious|violation","risk":0-100,'
        '"categories":["..."],"reason":"不超过80字"}\n\n'
        "举报分类：%s\n举报说明：%s\n聊天记录：\n%s"
        % (_clip(report.get("reason"), 60), _clip(report.get("detail"), 300), text)
    )
    payload = {
        "model": cfg["model"],
        "temperature": 0,
        "thinking": {"type": "disabled"},
        "messages": [
            {"role": "system", "content": "你是严格但克制的校园平台安全审核员，只输出 JSON。"},
            {"role": "user", "content": prompt},
        ],
    }
    req = urllib.request.Request(
        cfg["base_url"] + "/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + cfg["api_key"],
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"] or ""
        m = re.search(r"\{[\s\S]*\}", content)
        obj = json.loads(m.group(0)) if m else {}
        verdict = obj.get("verdict")
        if verdict not in ("safe", "suspicious", "violation"):
            verdict = "suspicious"
        try:
            risk = int(obj.get("risk") or 0)
        except Exception:
            risk = 0
        cats = obj.get("categories")
        return {
            "ok": True,
            "source": "ai",
            "verdict": verdict,
            "risk": max(0, min(100, risk)),
            "categories": [str(x)[:30] for x in cats[:8]] if isinstance(cats, list) else [],
            "reason": _clip(obj.get("reason"), 300),
            "model": cfg["model"],
            "at": _now(),
        }
    except Exception as e:
        return {
            "ok": False,
            "source": "ai-error",
            "verdict": "suspicious",
            "risk": 0,
            "categories": [],
            "reason": "AI 审核暂时不可用：" + str(e)[:80],
            "model": cfg["model"],
            "at": _now(),
        }


def _audit(report_id, action, detail="", actor=""):
    with _LOCK:
        rows = _load(AUDIT_FILE, [])
        rows.append({
            "id": "ma_" + uuid.uuid4().hex[:12],
            "reportId": report_id,
            "action": action,
            "detail": detail,
            "actor": actor,
            "at": _now(),
        })
        _save(AUDIT_FILE, rows[-5000:])


def _process(report_id):
    with _LOCK:
        rows = _load(REPORT_FILE, [])
        report = next((r for r in rows if r.get("id") == report_id), None)
        if not report:
            return
        report["status"] = "reviewing"
        report["reviewedAt"] = _now()
        _save(REPORT_FILE, rows)
    result = _call_ai(report)
    if not result:
        result = _local_risk(report)
    with _LOCK:
        rows = _load(REPORT_FILE, [])
        report = next((r for r in rows if r.get("id") == report_id), None)
        if not report:
            return
        report["ai"] = result
        report["reviewedAt"] = _now()
        history = risk_profile.get_level(report.get("targetOwner")).get("level", "normal")
        decision = moderation_policy.decide(result.get("verdict"), result.get("risk"),
                                            result.get("categories"), history,
                                            automatic=False)
        report["action"] = decision
        report["status"] = decision.get("status") or "auto_safe"
        if decision.get("mute_minutes"):
            try:
                scope = "module:" + str(report.get("kind") or "")
                enforcement.mute_chat(report.get("targetOwner"), decision.get("mute_minutes"),
                                       decision.get("reason"), report.get("id"), scope)
                report["mutedUntil"] = _now() + int(decision.get("mute_minutes")) * 60 * 1000
                report["muteScope"] = scope
            except Exception:
                pass
        if decision.get("action") in ("warn", "mute_chat"):
            report["warningFor"] = report.get("targetOwner") or ""
            report["warning"] = ("AI 检测到本次聊天内容存在违规风险，相关记录已保存。请立即停止不当言行。"
                                 if decision.get("action") == "warn"
                                 else "AI 检测到本次聊天内容存在严重违规风险，聊天已被暂停。相关记录已保存。")
            report["warningAt"] = _now()
        if result.get("verdict") == "violation" and int(result.get("risk") or 0) >= 70:
            try:
                risk_profile.note_violation(report.get("targetOwner"), "report",
                                            result.get("reason"), result.get("risk"), report.get("id"),
                                            str(report.get("kind") or "") + ":" + str(report.get("targetId") or ""))
            except Exception:
                pass
        _save(REPORT_FILE, rows)
    _audit(report_id, "ai_review", (result.get("reason") or "") + " / " + (decision.get("status") or ""))


def _worker():
    while True:
        report_id = _QUEUE.get()
        try:
            _process(report_id)
        except Exception as e:
            _audit(report_id, "worker_error", str(e)[:200])
        finally:
            _QUEUE.task_done()


def start_worker():
    global _STARTED
    if _STARTED:
        return
    _STARTED = True
    threading.Thread(target=_worker, daemon=True).start()


def create(report):
    report_id = "mr_" + uuid.uuid4().hex[:12]
    row = {
        "id": report_id,
        "reporter": _clip(report.get("reporter"), 64),
        "targetOwner": _clip(report.get("targetOwner"), 64),
        "kind": _clip(report.get("kind"), 20),
        "targetId": _clip(report.get("targetId"), 64),
        "itemId": _clip(report.get("itemId"), 64),
        "claimId": _clip(report.get("claimId"), 64),
        "itemTitle": _clip(report.get("itemTitle"), 120),
        "reason": _clip(report.get("reason"), 40),
        "detail": _clip(report.get("detail"), 500),
        "scope": "message" if report.get("scope") == "message" else "chat",
        "messageId": _clip(report.get("messageId"), 64),
        "messages": (report.get("messages") or [])[-60:],
        "status": "pending",
        "createdAt": _now(),
    }
    with _LOCK:
        rows = _load(REPORT_FILE, [])
        rows.append(row)
        _save(REPORT_FILE, rows[-5000:])
    _audit(report_id, "created", row.get("reason") or "", row.get("reporter") or "")
    _QUEUE.put(report_id)
    return row


def mine(owner):
    with _LOCK:
        rows = _load(REPORT_FILE, [])
    return [r for r in rows if r.get("reporter") == owner][-100:][::-1]


def status(kind, target_id, owner):
    with _LOCK:
        rows = _load(REPORT_FILE, [])
    target_id = _clip(target_id, 64)
    matches = [r for r in rows if r.get("kind") == kind and r.get("targetId") == target_id]
    if not matches:
        return {"active": False, "status": "", "warning": "", "reportId": ""}
    report = matches[-1]
    warning = ""
    if (report.get("warningFor") == owner
            and report.get("warning")
            and report.get("status") not in ("dismissed", "resolved")):
        warning = report.get("warning")
    return {
        "active": report.get("status") in ("pending", "reviewing", "reviewed",
                                            "auto_warned", "auto_limited"),
        "status": report.get("status") or "",
        "warning": warning,
        "reportId": report.get("id") or "",
    }


def admin_list():
    with _LOCK:
        rows = _load(REPORT_FILE, [])
    return rows[-300:][::-1]


def get(report_id):
    with _LOCK:
        rows = _load(REPORT_FILE, [])
    return next((r for r in rows if r.get("id") == report_id), None)


def admin_update(report_id, status, note="", actor=""):
    if status not in ("resolved", "dismissed", "reviewing"):
        return None
    with _LOCK:
        rows = _load(REPORT_FILE, [])
        report = next((r for r in rows if r.get("id") == report_id), None)
        if not report:
            return None
        report["status"] = status
        report["adminNote"] = _clip(note, 500)
        report["handledAt"] = _now()
        _save(REPORT_FILE, rows)
    _audit(report_id, "admin_" + status, note, actor)
    return report


def summary():
    with _LOCK:
        rows = _load(REPORT_FILE, [])
    return {
        "total": len(rows),
        "pending": sum(1 for r in rows if r.get("status") in ("pending", "reviewing")),
        "resolved": sum(1 for r in rows if r.get("status") == "resolved"),
        "dismissed": sum(1 for r in rows if r.get("status") == "dismissed"),
    }
