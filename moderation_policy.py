"""自动处置策略（独立模块）。

这里只决定“AI 结果对应什么动作”，不写审核、不写聊天、不写管理端。
"""

RISK_WARN = 40
RISK_MUTE = 85

SEVERE_CATEGORIES = ("色情", "色情擦边", "诈骗", "代考", "作弊", "威胁", "暴力")


def _has(categories, words):
    text = "".join(str(x) for x in (categories or []))
    return any(w in text for w in words)


def decide(verdict, risk, categories=None, history_level="normal", local_hits=None):
    risk = max(0, min(100, int(risk or 0)))
    hits = local_hits or []
    severe = _has(categories, SEVERE_CATEGORIES)

    if verdict == "safe" and risk < RISK_WARN and not hits:
        return {
            "action": "none",
            "status": "auto_safe",
            "reason": "AI 未发现违规，仅保留审核记录",
            "mute_minutes": 0,
        }

    if not severe or risk < RISK_MUTE:
        return {
            "action": "warn",
            "status": "auto_warned",
            "reason": "AI 判断存在风险，先警告，不限制账号",
            "mute_minutes": 0,
        }

    if history_level == "restricted":
        minutes = 7 * 24 * 60
    elif history_level == "high":
        minutes = 24 * 60
    else:
        minutes = 2 * 60
    return {
        "action": "mute_chat",
        "status": "auto_limited",
        "reason": "AI 判断本次内容涉及严重违规，自动暂停聊天 %d 分钟" % minutes,
        "mute_minutes": minutes,
    }
