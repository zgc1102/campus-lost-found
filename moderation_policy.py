"""自动处置策略（独立模块）。

这里只决定“AI 结果对应什么动作”，不写审核、不写聊天、不写管理端。
"""

RISK_WARN = 40
RISK_MUTE = 70

HIGH_CATEGORIES = ("色情", "诈骗", "代考", "作弊", "威胁")


def decide(verdict, risk, local_hits=None, history_level="normal"):
    risk = max(0, min(100, int(risk or 0)))
    hits = local_hits or []
    if verdict == "safe" and risk < RISK_WARN and not hits:
        return {
            "action": "none",
            "status": "auto_safe",
            "reason": "AI 未发现违规，仅保留审核记录",
            "mute_minutes": 0,
        }
    if risk < RISK_MUTE and verdict != "violation":
        return {
            "action": "warn",
            "status": "auto_warned",
            "reason": "AI 判断存在风险，先警告，不限制账号",
            "mute_minutes": 0,
        }
    # 高风险的重复用户加重处理，但仍然保留申诉入口
    long_mute = history_level in ("high", "restricted")
    minutes = 7 * 24 * 60 if long_mute else 24 * 60
    return {
        "action": "mute_chat",
        "status": "auto_limited",
        "reason": "AI 判断本次聊天内容高危，自动暂停聊天 %d 天" % (minutes // (24 * 60)),
        "mute_minutes": minutes,
    }
