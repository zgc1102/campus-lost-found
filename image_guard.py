"""独立图片安全审核模块。

只处理图片安全，不处理聊天、举报记录或物品审核。
当前使用视觉模型，优先读 IMAGE_GUARD_*，没有时复用 VISION_*。
"""
import json
import os
import re
import urllib.error
import urllib.request


def _config():
    return {
        "api_key": os.environ.get("IMAGE_GUARD_API_KEY", "").strip()
        or os.environ.get("VISION_API_KEY", "").strip(),
        "base_url": (os.environ.get("IMAGE_GUARD_BASE_URL", "").strip()
                     or os.environ.get("VISION_BASE_URL", "https://open.bigmodel.cn/api/paas/v4").strip()).rstrip("/"),
        "model": (os.environ.get("IMAGE_GUARD_MODEL", "").strip()
                  or os.environ.get("VISION_MODEL", "glm-5.3-flash").strip()),
    }


def moderate(image_b64):
    """返回 {ok,safe,category,confidence,reason,model}。失败不阻断上传。"""
    cfg = _config()
    if not cfg["api_key"]:
        return {"ok": False, "safe": True, "category": "未配置", "confidence": 0,
                "reason": "未配置图片审核模型", "model": ""}
    image = str(image_b64 or "")
    if not image.startswith("data:"):
        image = "data:image/jpeg;base64," + image
    prompt = (
        "你是校园失物招领平台的图片安全审核器。判断这张图片是否适合公开展示。"
        "重点检查：色情裸露、性暗示、暴力血腥、毒品、赌博、武器、诈骗二维码/付款码、"
        "身份证/银行卡等敏感证件、代考/作弊/小抄/考试答案、其他违法内容。"
        "正常失物照片、物品特写、宿舍/教室背景都算安全。"
        "只输出 JSON，不要 markdown："
        '{"safe":true或false,"category":"无/色情/暴力/毒品/赌博/武器/诈骗/证件/代考/其他",'
        '"confidence":0到1,"reason":"不超过30字"}'
    )
    payload = {
        "model": cfg["model"],
        "temperature": 0,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image}},
        ]}],
    }
    req = urllib.request.Request(
        cfg["base_url"] + "/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + cfg["api_key"]},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"] or ""
        m = re.search(r"\{[\s\S]*\}", text)
        obj = json.loads(m.group(0)) if m else {}
        try:
            conf = float(obj.get("confidence") or 0)
        except Exception:
            conf = 0
        return {
            "ok": True,
            "safe": bool(obj.get("safe", True)),
            "category": str(obj.get("category") or "无")[:20],
            "confidence": max(0, min(1, conf)),
            "reason": str(obj.get("reason") or "")[:60],
            "model": cfg["model"],
        }
    except Exception as e:
        return {"ok": False, "safe": True, "category": "审核异常", "confidence": 0,
                "reason": "图片审核暂时不可用：" + str(e)[:80], "model": cfg["model"]}
