"""自动处置策略（独立模块）。

这里只决定“AI 结果对应什么动作”，不写审核、不写聊天、不写管理端。
"""

RISK_WARN = 40
RISK_MUTE = 85

SEVERE_CATEGORIES = ("色情", "色情擦边", "诈骗", "代考", "作弊", "威胁", "暴力")
SEVERE_HITS = ("去死", "杀了你", "弄死你", "约炮", "裸照", "开房", "代考", "代写", "卖答案")


def _has(categories, words):
    values = {str(x).strip() for x in (categories or [])}
    return any(w in values for w in words)


def _severe(categories, local_hits):
    return _has(categories, SEVERE_CATEGORIES) or any(w in (local_hits or []) for w in SEVERE_HITS)


def decide(verdict, risk, categories=None, history_level="normal", local_hits=None, automatic=True):
    risk = max(0, min(100, int(risk or 0)))
    severe = _severe(categories, local_hits)

    if verdict == "safe" and risk < RISK_WARN:
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

    if not automatic and history_level == "normal":
        return {
            "action": "warn",
            "status": "auto_warned",
            "reason": "举报由 AI 判定存在风险，第一次先警告，不直接暂停聊天",
            "mute_minutes": 0,
        }

    if history_level == "restricted":
        minutes = 24 * 60
    elif history_level == "high":
        minutes = 2 * 60
    else:
        minutes = 30
    return {
        "action": "mute_chat",
        "status": "auto_limited",
        "reason": "AI 判断本次内容涉及严重违规，自动暂停本次聊天 %d 分钟" % minutes,
        "mute_minutes": minutes,
    }
