#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清华校园拾光里 · 服务端 v4
- 用户端：只看公开内容、只能管自己的帖子（凭本机令牌）
- 管理端：独立页面，密码登录后才能审核
- 数据文件：items.json；管理员密码：admin.json / 管理员密码.txt
"""

import hashlib
import base64
import json
import math
import os
import collections
import queue
import random
import re
import socket
import string
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse, parse_qs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_dotenv(path=None):
    """极简 .env 读取：KEY=VALUE，忽略注释与空行，不覆盖已有环境变量"""
    path = path or os.path.join(BASE_DIR, ".env")
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except Exception:
        pass


load_dotenv()
DATA_FILE = os.path.join(BASE_DIR, "items.json")
ADMIN_FILE = os.path.join(BASE_DIR, "admin.json")
PASSWORD_FILE = os.path.join(BASE_DIR, "管理员密码.txt")
LOCK = threading.Lock()
START_TS = time.time()
TOKENS = {}          # admin token -> expire ts
TOKEN_TTL = 8 * 3600

PUBLIC_STATUS = ("approved", "claimed", "closed")
ALLOWED_STATUS = ("pending", "approved", "rejected", "claimed", "closed", "removed", "hidden")
CLOSED_VISIBLE_MS = 24 * 3600 * 1000


def public_visible(it, now=None):
    """已闭环的内容在用户端只保留 24 小时，后台不受影响"""
    if it.get("status") != "closed":
        return True
    at = it.get("closedAt") or it.get("updatedAt") or it.get("createdAt") or 0
    return (now or now_ms()) - at < CLOSED_VISIBLE_MS


def now_ms():
    return int(time.time() * 1000)


# ---------------------------------------------------------------- 数据

def seed_items():
    lost = [
        ("l1", "bag", "黑色双肩书包（含课本）", "在六教课间丢失，内有《高等数学》等课本，急寻。", "第六教学楼 3 区"),
        ("l2", "card", "校园卡一张", "紫荆公寓附近捡到，姓名已遮挡，请失主认领。", "紫荆公寓 15 号楼"),
        ("l3", "watch", "银色手表", "操场跑步后遗落，卡西欧款式。", "东大操场"),
        ("l4", "electronics", "AirPods 耳机", "图书馆二层自习室遗失，白色。", "图书馆 2 层"),
        ("l5", "umbrella", "蓝色雨伞", "食堂门口遗留，长柄。", "观畴园食堂"),
        ("l6", "key", "钥匙串（含门禁卡）", "教学楼楼梯间捡到。", "第四教学楼"),
    ]
    found = [
        ("f1", "card", "求找：黑色钱包", "昨晚在食堂丢失，内有身份证和少量现金。", "桃李园食堂"),
        ("f2", "electronics", "求找：机械键盘", "机房使用后未带走，茶轴。", "东主楼机房"),
        ("f3", "sports", "求找：篮球", "篮球场上遗落，斯伯丁。", "北区篮球场"),
        ("f4", "book", "求找：课本《线性代数》", "图书馆借的书丢了。", "图书馆"),
        ("f5", "cup", "求找：保温杯", "体育馆更衣室遗留。", "综合体育馆"),
        ("f6", "charger", "求找：充电宝", "教室插座上忘拿。", "第五教学楼"),
    ]
    out = []
    for i, (pid, cat, title, desc, place) in enumerate(lost):
        out.append({
            "id": pid, "type": "found", "cat": cat, "title": title, "desc": desc,
            "place": place, "eventTime": "", "secret": "", "photo": None,
            "contact": {}, "status": "closed" if i in (3, 5) else "approved",
            "rejectReason": "", "ownerId": "seed", "ownerToken": "seed",
            "createdAt": now_ms() - 86400000 * 3, "updatedAt": now_ms(),
        })
    for i, (pid, cat, title, desc, place) in enumerate(found):
        out.append({
            "id": pid, "type": "lost", "cat": cat, "title": title, "desc": desc,
            "place": place, "eventTime": "", "secret": "", "photo": None,
            "contact": {}, "status": "closed" if i == 4 else "approved",
            "rejectReason": "", "ownerId": "seed", "ownerToken": "seed",
            "createdAt": now_ms() - 86400000 * 3, "updatedAt": now_ms(),
        })
    return out


def load_items():
    if not os.path.exists(DATA_FILE):
        items = seed_items()
        save_items(items)
        return items
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else seed_items()
    except Exception:
        return seed_items()


def save_items(items):
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    os.replace(tmp, DATA_FILE)




# ---------- 拾光码 ----------
TAGS_FILE = os.path.join(BASE_DIR, "tags.json")
TAG_QR_DIR = os.path.join(BASE_DIR, "tag_qr")


def load_tags():
    return _load_json(TAGS_FILE, [])


def save_tags(data):
    _save_json(TAGS_FILE, data)


def _tag_public(tag, base_url="", with_qr=False):
    # 契约冻结：二维码只允许使用 /?tag=CODE，不得改成带版本号或临时路径
    mode = tag.get("mode") or "notify"
    phone = str(tag.get("phone") or "")
    out = {
        "code": tag.get("code"),
        "itemName": tag.get("itemName"),
        "note": tag.get("note") or "",
        "mode": mode,
        "phoneMasked": re.sub(r"(\d{3})\d{4}(\d{4})", r"\1****\2", phone) if phone else "",
        "createdAt": tag.get("createdAt"),
        "notifyCount": tag.get("notifyCount") or 0,
        "deactivated": not tag.get("active", True),
        "createdAt": tag.get("createdAt"),
        "url": (base_url.rstrip("/") + "/?tag=" + str(tag.get("code") or "")) if base_url else "",
    }
    if out["deactivated"]:
        out["phoneMasked"] = ""
        out["url"] = ""
        out.pop("phoneFull", None)
    if mode == "phone":
        out["phoneFull"] = phone
    if with_qr and base_url:
        try:
            os.makedirs(TAG_QR_DIR, exist_ok=True)
            path = os.path.join(TAG_QR_DIR, str(tag.get("code")) + ".png")
            make_qr_png(out["url"], path, box=8, border=3)
            with open(path, "rb") as f:
                out["qrData"] = "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")
        except Exception as e:
            out["qrError"] = str(e)[:80]
    return out


# ---------------------------------------------------------------- 认领 / 通知 / 匹配

CLAIMS_FILE = os.path.join(BASE_DIR, "claims.json")
NOTICES_FILE = os.path.join(BASE_DIR, "notices.json")


def _load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, type(default)) else default
    except Exception:
        return default


def _save_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


SPECIAL_FILE = os.path.join(BASE_DIR, "special_numbers.json")


def load_special_numbers():
    data = _load_json(SPECIAL_FILE, [])
    return [str(x) for x in data] if isinstance(data, list) else []


def save_special_numbers(arr):
    _save_json(SPECIAL_FILE, arr)


ANNOUNCE_FILE = os.path.join(BASE_DIR, "announcements.json")


def load_announcements():
    return _load_json(ANNOUNCE_FILE, [])


def save_announcements(items):
    _save_json(ANNOUNCE_FILE, items)


ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")


def load_accounts():
    return _load_json(ACCOUNTS_FILE, [])


def save_accounts(accs):
    _save_json(ACCOUNTS_FILE, accs)


def load_claims():
    return _load_json(CLAIMS_FILE, [])


def save_claims(data):
    _save_json(CLAIMS_FILE, data)


def load_notices():
    return _load_json(NOTICES_FILE, [])


def save_notices(data):
    _save_json(NOTICES_FILE, data)


def add_notice(notices, owner, kind, text, item_id="", claim_id=""):
    notices.append({
        "id": "n_" + uuid.uuid4().hex[:10],
        "owner": owner,
        "type": kind,
        "text": text,
        "itemId": item_id,
        "claimId": claim_id,
        "read": False,
        "at": now_ms(),
    })
    return notices


def _bigrams(text):
    s = re.sub(r"\s+", "", (text or "").lower())
    return [s[i:i + 2] for i in range(len(s) - 1)] or ([s] if s else [])


def _cosine(a, b):
    from collections import Counter
    ca, cb = Counter(a), Counter(b)
    if not ca or not cb:
        return 0.0
    inter = sum((ca & cb).values())
    return 2.0 * inter / (sum(ca.values()) + sum(cb.values()))


def match_score(lost, found):
    """两件物品的相似度：标题权重最高，其次描述、地点、分类"""
    a = _bigrams((lost.get("title") or "") * 2 + (lost.get("desc") or "") + (lost.get("place") or ""))
    b = _bigrams((found.get("title") or "") * 2 + (found.get("desc") or "") + (found.get("place") or ""))
    score = _cosine(a, b)
    if lost.get("cat") and lost.get("cat") == found.get("cat"):
        score += 0.08
    return min(1.0, round(score, 3))


def run_matching(threshold=0.42):
    """把「寻物」和「招领」两两比对，命中就互相通知（少量数据下很快）"""
    with LOCK:
        items = load_items()
        notices = load_notices()
    losts = [x for x in items if x.get("type") == "lost" and x.get("status") in ("approved", "claimed")]
    founds = [x for x in items if x.get("type") == "found" and x.get("status") in ("approved", "claimed")]
    created = 0
    for l in losts:
        for f in founds:
            if l.get("ownerToken") == f.get("ownerToken"):
                continue
            score = match_score(l, f)
            if score < threshold:
                continue
            lmatches = l.setdefault("matches", [])
            if any(m.get("id") == f["id"] for m in lmatches):
                continue
            lmatches.append({"id": f["id"], "score": score, "at": now_ms()})
            f.setdefault("matches", []).append({"id": l["id"], "score": score, "at": now_ms()})
            pct = int(score * 100)
            add_notice(notices, l.get("ownerToken"), "match",
                       "发现一条相似度 %d%% 的招领：%s" % (pct, f.get("title") or ""), f["id"])
            add_notice(notices, f.get("ownerToken"), "match",
                       "发现一条相似度 %d%% 的寻物：%s" % (pct, l.get("title") or ""), l["id"])
            created += 1
    with LOCK:
        save_items(items)
        save_notices(notices)
    return created



def ensure_admin_password():
    if os.path.exists(ADMIN_FILE):
        try:
            with open(ADMIN_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            if isinstance(cfg, dict) and cfg.get("password"):
                return cfg["password"]
        except Exception:
            pass
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    pwd = "".join(random.choice(alphabet) for _ in range(8))
    with open(ADMIN_FILE, "w", encoding="utf-8") as f:
        json.dump({"password": pwd, "updated": now_ms()}, f, ensure_ascii=False, indent=1)
    try:
        with open(PASSWORD_FILE, "w", encoding="utf-8") as f:
            f.write("管理员密码：%s\n\n"
                    "管理端地址：https://你的公网地址/管理端.html\n"
                    "（本机也可用：http://127.0.0.1:8000/管理端.html）\n\n"
                    "改密码：编辑同目录的 admin.json，把 password 改成新的，然后重启服务。\n"
                    "别把这个文件发给别人。\n" % pwd)
    except Exception:
        pass
    return pwd


AI_FILE = os.path.join(BASE_DIR, "ai.json")

AI_DEFAULT = {
    "enabled": False,
    "base_url": "",
    "api_key": "",
    "model": "",
    "auto_review": True,
    "auto_approve": True,
    "approve_threshold": 20,
    "auto_reject": True,
    "reject_threshold": 80,
}

SEVERE_WORDS = [
    # 色情 / 招嫖
    "嫖娼", "招嫖", "援交", "外围女", "楼凤", "包夜", "约炮", "一夜情", "找女大",
    "学生妹", "陪睡", "陪侍", "特殊服务", "上门服务", "成人服务", "大保健", "开房",
    "裸聊", "色情", "黄片", "约p", "找小姐", "卖淫", "性服务",
    # 毒品 / 管制物品
    "冰毒", "大麻", "K粉", "摇头丸", "迷药", "春药", "催情", "枪支", "手枪",
    "仿真枪", "管制刀具",
    # 考试 / 证件作弊
    "代考", "替考", "代写论文", "办证", "假证", "刻章",
]
BANNED_WORDS = ["现金", "转账", "刷单", "贷款", "博彩", "赌博",
                "高利贷", "套现", "洗钱", "发票", "黄牛", "外挂", "代练",
                "网贷", "押金", "返利", "兼职刷", "跑分"]
AD_WORDS = ["出售", "转让", "低价", "批发", "代购", "促销", "秒杀", "包邮",
            "出租", "招租", "招聘", "兼职", "日结", "扫码领", "加微信", "加v"]
CONTACT_RE = re.compile(r"(1[3-9]\d{9}|微信|weixin|wechat|加v|加V|vx|VX|\bqq\b|QQ号)")

# 平台业务范围限制：标题里出现这些，直接判定「不是失物招领」
TITLE_BLOCK = ["找对象", "征婚", "相亲", "交友", "找搭子", "组局", "陪聊", "陪侍",
               "小妹妹", "小姐姐", "包夜"]


def scope_violation(it):
    title = it.get("title") or ""
    return [w for w in TITLE_BLOCK if w in title]


def load_ai_config():
    cfg = dict(AI_DEFAULT)
    try:
        with open(AI_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            cfg.update({k: data.get(k, cfg[k]) for k in cfg})
    except Exception:
        pass
    # 环境变量优先：公开仓库里不出现任何密钥
    for env_key, cfg_key in (("DEEPSEEK_API_KEY", "api_key"),
                             ("DEEPSEEK_BASE_URL", "base_url"),
                             ("DEEPSEEK_MODEL", "model")):
        v = os.environ.get(env_key)
        if v:
            cfg[cfg_key] = v
    if os.environ.get("AI_ENABLED"):
        cfg["enabled"] = os.environ.get("AI_ENABLED") == "1"
    return cfg


def save_ai_config(cfg):
    merged = dict(AI_DEFAULT)
    merged.update({k: cfg.get(k, merged[k]) for k in merged})
    with open(AI_FILE, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=1)
    return merged


def ai_rules(it):
    """本地规则预审：零成本、立即出结果"""
    text = "%s %s %s" % (it.get("title") or "", it.get("desc") or "", it.get("secret") or "")
    score = 0
    reasons = []

    severe = [w for w in SEVERE_WORDS if w in text]
    if severe:
        score += 90
        reasons.append("命中高危词（色情/毒品/作弊等）：" + "、".join(severe))

    banned = [w for w in BANNED_WORDS if w in text]
    if banned:
        score += 70
        reasons.append("命中违禁词：" + "、".join(banned))

    ads = [w for w in AD_WORDS if w in text]
    if ads:
        score += 25
        reasons.append("疑似商业推广：" + "、".join(ads))

    if CONTACT_RE.search(text):
        score += 10
        reasons.append("正文含联系方式，建议改为平台内联系")

    if len(it.get("desc") or "") < 10:
        score += 20
        reasons.append("描述过短，难以核对")

    title = it.get("title") or ""
    if re.search(r"(.)\1{4,}", title):
        score += 15
        reasons.append("标题含大量重复字符")
    if len(title) < 2:
        score += 20
        reasons.append("标题过短")

    score = min(score, 95)
    if score >= 60:
        decision = "reject"
    elif score >= 30:
        decision = "review"
    else:
        decision = "approve"

    return {
        "decision": decision,
        "score": score,
        "reason": "；".join(reasons) if reasons else "未发现明显问题",
        "source": "rule",
        "at": now_ms(),
    }


AI_SYSTEM_PROMPT = (
    "你是校园失物招领与爱心求助平台的内容审核员，负责判断一条信息能否公开展示。"
    "本平台接受三类内容：寻物启事（丢了东西）、招领启事（捡到东西）、"
    "爱心求助（同学之间无偿借用工具、代办跑腿、闲置捐赠、志愿帮忙）。\n"
    "第一步：判断是否属于本平台业务范围。"
    "以下都**不属于**，一律 reject（risk 85-100），"
    "理由写“不属于平台范围”："
    "找对象、征婚、相亲、交友、找搭子、组局、找人陪聊；"
    "招嫖或性暗示（找小妹妹、小姐姐、妹妹、包夜、上门、陪侍、服务）；"
    "招聘兼职、租房卖房、二手买卖、付费代购、商业跑腿、拼车、拉群、广告推广。"
    "注意：同学之间**无偿**借用、代办、捐赠、志愿帮忙属于允许范围，不要误判。"
    "但**借钱、垫付、转账、刷单、代考代写、投资理财**一律 reject。\n"
    "第二步：检查标题与正文是否一致。"
    "如果标题带有交友/招嫖暗示，而正文写的是正常寻物，"
    "这是**借寻物名义规避审核**，必须 reject（risk 85-100），"
    "理由写明“标题与内容不符，疑似借寻物发布交友/招嫖信息”。"
    "反过来，标题正常但正文夹带广告或联系方式营销，也要 reject。\n"
    "第三步：识别规避写法。用户可能用拼音（piaochang、daikao）、"
    "英文（escort、cheat exam）、谐音、缩写（PC、代K）、拆字、emoji、"
    "间隔符号、繁体字来隐藏违规含义，请先还原真实语义再判断。\n"
    "违法内容（色情招嫖、性服务、代考代写、毒品枪支、赌博贷款洗钱、"
    "买卖证件发票账号、诈骗引流）一律 reject。\n"
    "正常情况：真实的失物招领/寻物启事，哪怕描述很短、带了手机号，"
    "或提到悬赏酬谢，都算通过。\n"
    "只输出 JSON，不要输出任何其他文字。字段："
    "decision 取 approve/review/reject；"
    "risk 为风险分 0-100，approve 时 0-20，review 时 30-70，reject 时 80-100；"
    "guessType 取 lost 或 found：判断发布者是「丢东西的人」还是「捡到东西的人」。"
    "出现“我丢了/丢失/找不到/寻找”属于 lost；出现“我捡到/拾到/交到”属于 found，不要照抄用户选的类型；"
    "reason 不超过 40 字，要点出你识别到的真实含义或范围问题。"
    '格式：{"decision":"approve","risk":5,"reason":"...","guessType":"lost"}'
)


AI_ERROR_HINTS = {
    400: "请求格式不对（多半是模型名写错了）",
    401: "API Key 无效或还没开通",
    403: "这个 Key 没有该模型的权限",
    404: "接口地址不对（检查 base_url 有没有写错）",
    402: "账户余额不足，需要先充值",
    429: "请求太频繁或额度用完了，稍后再试",
    500: "模型服务内部错误，稍后再试",
    503: "模型服务繁忙，稍后再试",
}


def _endpoints(base):
    b = (base or "").strip().rstrip("/")
    if not b:
        return []
    if b.endswith("/chat/completions"):
        return [b]
    out = [b + "/chat/completions"]
    if not b.endswith("/v1") and not b.endswith("/v4"):
        out.append(b + "/v1/chat/completions")
    # 有些配置把 base_url 写成 .../v1，但 DeepSeek 的兼容接口在根路径
    if b.endswith("/v1") and not b.endswith("/api/paas/v4"):
        out.append(b[:-3].rstrip("/") + "/chat/completions")
    return out


def _post_chat(endpoint, payload, api_key, timeout=25):
    import urllib.error
    import urllib.request

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + (api_key or ""),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", "ignore")[:200]
        except Exception:
            pass
        hint = AI_ERROR_HINTS.get(e.code, "调用失败")
        raise RuntimeError("HTTP %s · %s %s" % (e.code, hint, detail))
    except Exception as e:
        raise RuntimeError("网络错误：%s" % str(e)[:120])


LOST_HINTS = ["我丢", "丢了", "丢失", "遗失", "不见了", "找不到", "寻找", "求找回",
              "谁捡到", "谁看到", "帮我找", "急寻"]
FOUND_HINTS = ["我捡", "捡到", "捡了", "拾到", "拾得", "发现一", "捡到一", "交到"]


def detect_lost_found(text):
    t = str(text or "")
    lost = sum(1 for w in LOST_HINTS if w in t)
    found = sum(1 for w in FOUND_HINTS if w in t)
    if lost > found:
        return "lost"
    if found > lost:
        return "found"
    return ""


def claim_ai_check(item, claim):
    """对多轮申请做一次总体一致性核验"""
    cfg = load_ai_config()
    if not (cfg.get("enabled") and cfg.get("api_key") and cfg.get("base_url")):
        return None
    rounds = claim.get("history") or [{"message": claim.get("message") or ""}]
    said = "\n".join("第%d次：%s" % (i + 1, r.get("message") or "") for i, r in enumerate(rounds))
    prompt = ("你是校园失物招领的核验助手。发布者描述：\n标题：%s\n描述：%s\n独有特征（申请人看不到）：%s\n"
              "申请人先后说：\n%s\n"
              "判断申请人说的与物品是否一致，是否有前后矛盾或明显编造。"
              '只输出 JSON：{"verdict":"match|unclear|mismatch","confidence":0-100,'
              '"reason":"30字以内","points":["逐条比对1","逐条比对2"]}；'
              "points 给 3 到 5 条逐条比对结果，每条 12 字以内，例如“颜色描述一致”“地点吻合”“第2次和第1次矛盾”。"
              % (item.get("title") or "", item.get("desc") or "", item.get("secret") or "", said))
    try:
        data = _post_chat(cfg.get("base_url").rstrip("/") + "/chat/completions",
                          {"model": cfg.get("model") or "deepseek-chat", "temperature": 0,
                           "messages": [{"role": "user", "content": prompt}]},
                          cfg.get("api_key"), timeout=25)
        text = data["choices"][0]["message"]["content"] or ""
        m = re.search(r"\{[\s\S]*\}", text)
        obj = json.loads(m.group(0)) if m else {}
        verdict = obj.get("verdict") if obj.get("verdict") in ("match", "unclear", "mismatch") else "unclear"
        try:
            conf = max(0, min(100, int(obj.get("confidence") or 0)))
        except Exception:
            conf = 0
        _pts = obj.get("points") or []
        if not isinstance(_pts, list):
            _pts = []
        _pts = [str(x).strip()[:24] for x in _pts if str(x).strip()][:5]
        return {"verdict": verdict, "confidence": conf,
                "reason": str(obj.get("reason") or "")[:60], "points": _pts, "at": now_ms()}
    except Exception:
        return None


def ai_llm(it, cfg, timeout=25):
    """调用 OpenAI 兼容接口做语义审核"""
    user_text = "标题：%s\n类型：%s\n地点：%s\n描述：%s\n核验特征：%s" % (
        it.get("title") or "",
        "爱心求助" if it.get("type") == "help" else ("寻物" if it.get("type") == "lost" else "招领"),
        it.get("place") or "", it.get("desc") or "", it.get("secret") or "",
    )
    if it.get("visionDesc"):
        user_text += "\n图片识别：%s" % it.get("visionDesc")
    payload = {
        "model": cfg.get("model") or "deepseek-flash",
        "temperature": 0,
        "messages": [
            {"role": "system", "content": AI_SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
    }

    data = None
    last_err = None
    for endpoint in _endpoints(cfg.get("base_url")):
        try:
            data = _post_chat(endpoint, payload, cfg.get("api_key"), timeout=timeout)
            break
        except RuntimeError as e:
            last_err = e
            if "HTTP 404" in str(e):
                continue          # 换一个候选地址再试
            raise
    if data is None:
        raise last_err or RuntimeError("没有可用的接口地址")

    content = ""
    try:
        content = data["choices"][0]["message"]["content"]
    except Exception:
        content = json.dumps(data, ensure_ascii=False)

    m = re.search(r"\{[\s\S]*\}", content)
    if not m:
        raise ValueError("模型没有返回 JSON，返回内容：" + content[:80])
    obj = json.loads(m.group(0))
    decision = str(obj.get("decision") or "review").lower()
    if decision not in ("approve", "review", "reject"):
        decision = "review"
    raw = obj.get("risk", obj.get("score", 50))
    try:
        score = int(float(raw))
    except Exception:
        score = 50
    score = max(0, min(100, score))
    # 关键：以模型的结论为准，把分数归一到该结论的区间
    # （不同模型对"分数"的含义理解不一致，直接拿去比阈值会误判）
    if decision == "approve":
        score = min(score, 20)
    elif decision == "reject":
        score = max(score, 80)
    else:
        score = max(30, min(70, score))
    return {
        "decision": decision,
        "score": score,
        "reason": str(obj.get("reason") or "")[:120],
        "guessType": str(obj.get("guessType") or "").lower() if str(obj.get("guessType") or "").lower() in ("lost", "found") else "",
        "source": "llm",
        "model": cfg.get("model") or "",
        "at": now_ms(),
    }


def ai_test(cfg):
    """测试连接：发一句最短的话，确认地址 / Key / 模型名都对"""
    import time as _t

    payload = {
        "model": cfg.get("model") or "deepseek-flash",
        "temperature": 0,
        "max_tokens": 16,
        "messages": [
            {"role": "system", "content": "只回复两个字：正常"},
            {"role": "user", "content": "连接测试"},
        ],
    }
    started = _t.time()
    last_err = None
    for endpoint in _endpoints(cfg.get("base_url")):
        try:
            data = _post_chat(endpoint, payload, cfg.get("api_key"), timeout=25)
            reply = ""
            try:
                reply = data["choices"][0]["message"]["content"]
            except Exception:
                reply = json.dumps(data, ensure_ascii=False)[:80]
            return {
                "ok": True,
                "endpoint": endpoint,
                "latency": round(_t.time() - started, 2),
                "reply": (reply or "").strip()[:60],
            }
        except RuntimeError as e:
            last_err = e
            if "HTTP 404" in str(e):
                continue
            return {"ok": False, "error": str(e)}
    return {"ok": False, "error": str(last_err or "没有可用的接口地址")}


AI_BINARY_PROMPT = (
    "你是校园失物招领平台的终审员。判断这条启事能不能直接公开给同学看。"
    "只回答 JSON：{\"publish\": true 或 false, \"reason\": \"不超过 30 字\"}。"
    "规则：真实的丢东西/捡到东西 = true；"
    "交友、找对象、招嫖、招聘、二手交易、广告、诈骗、违法 = false；"
    "拿不准时宁可 false。"
)


def ai_binary(it, cfg, timeout=12):
    """终审：把「需要复核」压成明确的 通过/不通过（无人工场景的关键）"""
    payload = {
        "model": cfg.get("model") or "deepseek-flash",
        "temperature": 0,
        "messages": [
            {"role": "system", "content": AI_BINARY_PROMPT},
            {"role": "user", "content": "标题：%s\n描述：%s\n地点：%s%s" % (
                it.get("title") or "", it.get("desc") or "", it.get("place") or "",
                ("\n图片识别：" + it["visionDesc"]) if it.get("visionDesc") else "")},
        ],
    }
    data = None
    last_err = None
    for endpoint in _endpoints(cfg.get("base_url")):
        try:
            data = _post_chat(endpoint, payload, cfg.get("api_key"), timeout=timeout)
            break
        except RuntimeError as e:
            last_err = e
            if "HTTP 404" in str(e):
                continue
            raise
    if data is None:
        raise last_err or RuntimeError("no endpoint")

    content = ""
    try:
        content = data["choices"][0]["message"]["content"]
    except Exception:
        content = json.dumps(data, ensure_ascii=False)
    m = re.search(r"\{[\s\S]*\}", content)
    if not m:
        raise ValueError("终审没有返回 JSON")
    obj = json.loads(m.group(0))
    return bool(obj.get("publish")), str(obj.get("reason") or "")[:120]


def ai_review(it, use_llm=True, timeout=25):
    cfg = load_ai_config()
    if use_llm and cfg.get("enabled") and cfg.get("api_key") and cfg.get("base_url"):
        try:
            return ai_llm(it, cfg, timeout=timeout)
        except Exception as e:
            result = ai_rules(it)
            result["reason"] = "（大模型调用失败，已用规则预审：%s）%s" % (str(e)[:60], result["reason"])
            result["source"] = "rule-fallback"
            return result
    return ai_rules(it)



# ================= 电话号码校验 =================
PHONE_PLACEHOLDERS = {"13800138000", "12345678901", "11111111111", "10086", "10010", "12345"}


def _phone_max_run(d):
    best = cur = 1
    for i in range(1, len(d)):
        cur = cur + 1 if d[i] == d[i - 1] else 1
        best = max(best, cur)
    return best


def _phone_max_seq(d):
    up = down = best = 1
    for i in range(1, len(d)):
        a, b = int(d[i - 1]), int(d[i])
        up = up + 1 if b == a + 1 else 1
        down = down + 1 if b == a - 1 else 1
        best = max(best, up, down)
    return best


def _phone_periodic(d):
    for p in (2, 3):
        if len(d) >= p * 4 and all(d[i] == d[i % p] for i in range(len(d))):
            return p
    return 0


def _phone_pattern(d):
    """对一段数字做豹子/顺子/循环判断，返回 (红色理由, 黄色理由)"""
    if len(set(d)) == 1:
        return ("全部数字相同，不是有效号码", "")
    run = _phone_max_run(d)
    if run >= 8:
        return ("连续 %d 位数字相同，不是有效号码" % run, "")
    seq = _phone_max_seq(d)
    if seq >= 8:
        return ("连续 %d 位数字递增/递减，不是有效号码" % seq, "")
    per = _phone_periodic(d)
    if (per == 2 and len(d) >= 8) or (per == 3 and len(d) >= 9):
        return ("数字循环重复，不是有效号码", "")
    if 6 <= run <= 7:
        return ("", "连续 %d 位数字相同，请确认是本人常用号码" % run)
    if 6 <= seq <= 7:
        return ("", "连续 %d 位数字递增/递减，请确认是本人常用号码" % seq)
    if per == 2 and len(d) >= 6:
        return ("", "数字循环重复，请确认是本人常用号码")
    if 4 <= run <= 5:
        return ("", "连续 %d 位相同，确认是本人常用号吗？" % run)
    if 4 <= seq <= 5:
        return ("", "连续 %d 位递增/递减，确认是本人常用号吗？" % seq)
    return ("", "")


def phone_check(raw):
    s0 = str(raw or "").strip()
    table = str.maketrans("０１２３４５６７８９", "0123456789")
    s0 = s0.translate(table)
    s0 = (s0.replace("幺", "1").replace("〇", "0").replace("零", "0")
             .replace("一", "1").replace("二", "2").replace("三", "3")
             .replace("四", "4").replace("五", "5").replace("六", "6")
             .replace("七", "7").replace("八", "8").replace("九", "9"))
    s0 = re.sub(r"[\s()（）.．]", "", s0).replace("－", "-").replace("—", "-")

    def red(reason):
        return {"status": "red", "type": "invalid", "normalized": "", "reason": reason}

    if not s0:
        return {"status": "none", "type": "none", "normalized": "", "reason": ""}
    if re.search(r"[A-Za-z]", s0):
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{5,19}", s0):
            return {"status": "green", "type": "wechat", "normalized": s0, "reason": ""}
        return red("包含字母")
    if re.search(r"[^\d+\-]", s0):
        return red("包含无法识别的字符")

    work = s0
    if work.startswith("+86"):
        work = work[3:]
    elif work.startswith("0086"):
        work = work[4:]
    elif work.startswith("86") and len(re.sub(r"\D", "", work)) == 13:
        work = work[2:]

    digits = re.sub(r"\D", "", work)
    if not digits:
        return red("没有数字")

    if digits in load_special_numbers():
        return {"status": "green", "type": "mobile", "normalized": digits, "reason": ""}
    if re.match(r"^(400|800)", digits) or re.match(r"^(95|96)\d{3,5}$", digits):
        return {"status": "red", "type": "service", "normalized": digits,
                "reason": "这是企业或服务号码，请留个人号码"}

    if s0.startswith("+") and not s0.startswith("+86") and 8 <= len(digits) <= 15:
        return {"status": "green", "type": "international", "normalized": "+" + digits, "reason": ""}

    # 座机：区号 + 本地号，本地号做豹子/顺子判断
    m = re.match(r"^(0\d{2,3})-?(\d{7,8})(?:-(\d{1,6}))?$", work)
    if m:
        local = m.group(2)
        bad, warn = _phone_pattern(local)
        if bad:
            return {"status": "red", "type": "landline", "normalized": work, "reason": "座机号码不真实（%s）" % bad}
        if warn:
            return {"status": "yellow", "type": "landline", "normalized": work, "reason": warn}
        return {"status": "green", "type": "landline", "normalized": work, "reason": ""}

    # 手机号
    if len(digits) == 11 and digits.startswith("1"):
        bad, warn = _phone_pattern(digits)
        if bad:
            return red(bad)
        if digits in PHONE_PLACEHOLDERS:
            return red("这是常见的测试号码")
        if not re.match(r"^1[3-9]\d{9}$", digits):
            return red("手机号应以 13–19 开头")
        if warn:
            return {"status": "yellow", "type": "mobile", "normalized": digits, "reason": warn}
        if re.match(r"^1(70|71|62|65|67)", digits):
            return {"status": "yellow", "type": "mobile", "normalized": digits,
                    "reason": "这是虚拟号段，建议留常用号码"}
        return {"status": "green", "type": "mobile", "normalized": digits, "reason": ""}

    if re.match(r"^\d{7,8}$", digits):
        bad, warn = _phone_pattern(digits)
        if bad:
            return red(bad)
        return {"status": "yellow", "type": "landline", "normalized": digits,
                "reason": "座机请带区号，例如 010-62785566"}

    if len(digits) != 11:
        return red("号码应为 11 位手机号，或带区号的座机")

    return red("号码格式不正确")



# ================= 发布侧稳定性 =================
AI_SEM = threading.BoundedSemaphore(8)
AI_STATS = {"reviews": 0, "fail": 0, "total_ms": 0}
INFLIGHT = {"n": 0}
INFLIGHT_LOCK = threading.Lock()
ARRIVALS = collections.deque()
ARRIVALS_LOCK = threading.Lock()


def note_arrival():
    now = time.time()
    with ARRIVALS_LOCK:
        ARRIVALS.append(now)
        while ARRIVALS and now - ARRIVALS[0] > 10:
            ARRIVALS.popleft()
        return len(ARRIVALS)


def should_queue():
    with QUEUE_LOCK:
        qlen = sum(1 for v in QUEUE_STATE.values() if v.get("state") in ("queued", "reviewing"))
    with INFLIGHT_LOCK:
        busy = INFLIGHT["n"]
    with ARRIVALS_LOCK:
        recent = len(ARRIVALS)
    return qlen >= 3 or busy >= 6 or recent >= 6
RATE = {}
RATE_LOCK = threading.Lock()


def rate_allow(owner):
    """每设备 3 条/分钟、10 条/小时"""
    now = time.time()
    with RATE_LOCK:
        arr = [t for t in RATE.get(owner, []) if now - t < 3600]
        if sum(1 for t in arr if now - t < 60) >= 20:
            return False, "你发得有点快，歇 1 分钟再试"
        if len(arr) >= 60:
            return False, "今天发得有点多，明天再来吧"
        arr.append(now)
        RATE[owner] = arr
    return True, ""


def guarded_review(item):
    """带并发上限、重试和计时的审核"""
    t0 = time.time()
    with INFLIGHT_LOCK:
        INFLIGHT["n"] += 1
    last = None
    try:
        for attempt in range(2):
            try:
                with AI_SEM:
                    ai = review_item(item)
                AI_STATS["reviews"] += 1
                AI_STATS["total_ms"] += int((time.time() - t0) * 1000)
                return ai
            except Exception as e:
                last = e
                time.sleep(0.8 + attempt * 1.2)
        AI_STATS["fail"] += 1
        AI_STATS["total_ms"] += int((time.time() - t0) * 1000)
        raise last if last else RuntimeError("review failed")
    finally:
        with INFLIGHT_LOCK:
            INFLIGHT["n"] -= 1



# ================= 审核队列 =================
REVIEW_QUEUE = queue.Queue()
QUEUE_STATE = {}
QUEUE_LOCK = threading.Lock()


def queue_add(item_id):
    with QUEUE_LOCK:
        QUEUE_STATE[item_id] = {"state": "queued", "at": time.time()}
    REVIEW_QUEUE.put(item_id)


def queue_position(item_id):
    with QUEUE_LOCK:
        order = list(QUEUE_STATE.keys())
        if item_id not in order:
            return 0
        idx = order.index(item_id)
        ahead = sum(1 for k in order[:idx]
                    if QUEUE_STATE.get(k, {}).get("state") in ("queued", "reviewing"))
    return ahead + 1


def apply_ai_decision(item, ai, cfg):
    try:
        approve_at = int(cfg.get("approve_threshold") or 0)
    except Exception:
        approve_at = 20
    try:
        reject_at = int(cfg.get("reject_threshold") or 80)
    except Exception:
        reject_at = 80
    item["ai"] = ai
    # 本项目是全自动 AI 审核，不设人工审核队列；规则兜底也视为自动审核
    ai_trusted = ai.get("source") in ("llm", "rule-fallback")
    scope_hits = scope_violation(item)
    if (ai_trusted and item.get("type") in ("lost", "found")
            and ai.get("guessType") and ai["guessType"] != item.get("type")):
        item["typeSuggestion"] = ai["guessType"]
    if scope_hits:
        item["status"] = "rejected"
        item["autoRejected"] = True
        item["rejectReason"] = "标题含交友/招嫖暗示（%s），不属于失物招领范围" % "、".join(scope_hits)
        item["ai"]["decision"] = "reject"
        item["ai"]["score"] = max(int(item["ai"].get("score") or 0), 85)
        item["ai"]["reason"] = ((item["ai"].get("reason") or "") + "；标题范围检查命中：" + "、".join(scope_hits)).strip("；")
        item["reviewedBy"] = "AI"
        item["reviewedAt"] = now_ms()
    elif (ai_trusted and cfg.get("auto_approve") and ai.get("decision") == "approve"
            and int(ai.get("score") or 0) <= approve_at):
        item["status"] = "approved"
        item["autoApproved"] = True
        item["reviewedBy"] = "AI"
        item["reviewedAt"] = now_ms()
    elif (ai_trusted and cfg.get("auto_reject") and ai.get("decision") == "reject"
            and int(ai.get("score") or 0) >= reject_at):
        item["status"] = "rejected"
        item["autoRejected"] = True
        item["rejectReason"] = "AI 自动拦截：" + (ai.get("reason") or "疑似违规内容")
        item["reviewedBy"] = "AI"
        item["reviewedAt"] = now_ms()
    elif not ai_trusted:
        # 极端情况下也保持全自动：按规则结果直接上架/拦截，不转人工
        if ai.get("decision") == "reject":
            item["status"] = "rejected"
            item["autoRejected"] = True
            item["rejectReason"] = "AI 自动拦截：" + (ai.get("reason") or "疑似违规内容")
        else:
            item["status"] = "approved"
            item["autoApproved"] = True
            item["reviewedBy"] = "AI-rule"
            item["reviewedAt"] = now_ms()
    return item


def review_worker():
    while True:
        item_id = REVIEW_QUEUE.get()
        try:
            with QUEUE_LOCK:
                if item_id in QUEUE_STATE:
                    QUEUE_STATE[item_id]["state"] = "reviewing"
            with LOCK:
                items = load_items()
                item = next((x for x in items if x.get("id") == item_id), None)
            if not item:
                continue
            cfg = load_ai_config()
            ai = guarded_review(item)
            item = apply_ai_decision(item, ai, cfg)
            with LOCK:
                items = load_items()
                for i, x in enumerate(items):
                    if x.get("id") == item_id:
                        items[i] = item
                        break
                save_items(items)
            try:
                run_matching()
            except Exception:
                pass
        except Exception:
            pass
        finally:
            with QUEUE_LOCK:
                QUEUE_STATE[item_id] = {"state": "done", "at": time.time()}
            REVIEW_QUEUE.task_done()


def start_review_workers(n=2):
    for _ in range(n):
        threading.Thread(target=review_worker, daemon=True).start()


def mask_contact(v):
    """未通过认领前，联系方式只给打码版本"""
    s = str(v or "")
    digits = re.sub(r"\D", "", s)
    if len(digits) >= 11:
        return re.sub(r"(\d{3})\d{4}(\d{4})", r"\1****\2", s)
    if len(s) <= 2:
        return s[:1] + "***"
    return s[:2] + "****" + s[-1:]


ITEMS_CACHE = {"key": "", "at": 0.0, "raw": b"", "etag": ""}
ITEMS_CACHE_LOCK = threading.Lock()

CHECK_CACHE = {}


def review_item(item):
    """跑一遍 AI 审核（含终审），发布和预检共用"""
    ai = ai_review(item, use_llm=True, timeout=12)
    cfg = load_ai_config()
    if ai.get("source") == "llm" and ai.get("decision") == "review":
        try:
            ok2, why2 = ai_binary(item, cfg, timeout=12)
        except Exception as e:
            ok2, why2 = False, "终审暂时不可用：" + str(e)[:30]
        ai["decision"] = "approve" if ok2 else "reject"
        ai["score"] = 15 if ok2 else 85
        ai["reason"] = ((ai.get("reason") or "") + "；终审：" + why2).strip("；")
        ai["second"] = True
    return ai


def moderate_tag(text):
    """拾光码标签是物品标签，不是公开帖子；只做内容安全审核，不按招领范围驳回"""
    text = str(text or "").strip()
    if not text:
        return True, ""
    bad = re.search(r"招嫖|包夜|性服务|赌博|毒品|代考|代写|刷单|诈骗|传销|枪支|迷药", text)
    if bad:
        return False, "内容包含违规词：" + bad.group(0)
    try:
        probe = {"type": "help", "cat": "help_borrow", "title": "拾光码物品标签",
                 "desc": text[:800], "place": "", "contact": {}}
        review_item(probe)
    except Exception:
        pass
    return True, ""


def moderate_text(text, title="用户输入", allow_help=False):
    """所有用户可输入文本的统一 AI 审核；审核服务异常时放行规则结果"""
    text = str(text or "").strip()
    if not text:
        return True, ""
    probe = {
        "type": "help" if allow_help else "found",
        "cat": "help_borrow" if allow_help else "other",
        "title": (title + "：" + text)[:80],
        "desc": text[:800], "place": "", "contact": {}
    }
    try:
        ai = review_item(probe)
    except Exception:
        return True, ""
    if (not allow_help and scope_violation(probe)) or ai.get("decision") == "reject":
        return False, (ai.get("reason") or "内容不符合校园互助规范")[:120]
    return True, ""


def public_item(it, owner=None):
    """用户端能看到的内容：不含核验特征、发布者令牌，电话脱敏"""
    out = {k: v for k, v in it.items()
           if k not in ("secret", "ownerToken", "ownerId")}
    phone = str((it.get("contact") or {}).get("phone") or "")
    if phone:
        out["contact"] = {"phone": re.sub(r"(\d{3})\d{4}(\d{4})", r"\1****\2", phone)}
    else:
        out["contact"] = {}
    # 告诉前端「这条是不是我自己发的」，避免让用户去认领自己的东西
    out["isMine"] = bool(owner and it.get("ownerToken") == owner)
    if it.get("photo"):
        out["photoUrl"] = "/api/photo/" + str(it.get("id"))
    out.pop("photo", None)
    return out


STARTUP_FILE = os.path.join(BASE_DIR, "启动密码.json")


def _machine_id():
    """本机指纹：换一台电脑就会变"""
    import platform
    import uuid as _uuid
    raw = "%s|%s|%s" % (platform.node(), _uuid.getnode(), os.environ.get("COMPUTERNAME", ""))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _hash_pwd(pwd, salt):
    return hashlib.pbkdf2_hmac("sha256", pwd.encode("utf-8"), salt.encode("utf-8"), 120000).hex()


def _ask(prompt):
    import getpass
    try:
        return getpass.getpass(prompt).strip()
    except Exception:
        return input(prompt).strip()


def _save_startup(cfg):
    with open(STARTUP_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=1)


def startup_gate():
    """启动前校验：本机指纹 + 启动密码。返回 True 才继续启动。"""
    if os.environ.get("SG_STARTUP_SKIP") == "1":
        return True
    cfg = None
    try:
        if os.path.exists(STARTUP_FILE):
            with open(STARTUP_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
    except Exception:
        cfg = None

    mid = _machine_id()
    print()
    print("=" * 60)
    if not cfg:
        print("  第一次启动：请设置「启动密码」")
        print("  （只用来启动程序，和后台管理密码不是一回事）")
        print("=" * 60)
        p1 = _ask("设置启动密码（至少 4 位）：")
        if len(p1) < 4:
            print("  密码太短，已取消。")
            return False
        p2 = _ask("再输一次：")
        if p1 != p2:
            print("  两次输入不一致，已取消。")
            return False
        salt = hashlib.sha256(os.urandom(32)).hexdigest()[:16]
        _save_startup({"salt": salt, "hash": _hash_pwd(p1, salt),
                       "machine": mid, "updated": now_ms()})
        print("  已设置，并绑定到这台电脑。")
        print("=" * 60)
        return True

    same = cfg.get("machine") == mid
    if not same:
        print("  [!] 这台电脑不是最初启动的那台。")
        print("      如果是你本人换了电脑，输入启动密码可以迁移；")
        print("      如果不是，请不要转发/使用这个程序。")
        print("=" * 60)
    else:
        print("  清华校园拾光里 · 启动验证")
        print("=" * 60)

    for _ in range(3):
        pwd = _ask("启动密码：" if same else "启动密码（迁移到本机）：")
        if _hash_pwd(pwd, cfg.get("salt") or "") == cfg.get("hash"):
            if not same:
                cfg["machine"] = mid
                cfg["updated"] = now_ms()
                _save_startup(cfg)
                print("  已绑定到这台电脑。")
            print("=" * 60)
            return True
        print("  密码不对，再试一次。")
    print("  连续 3 次错误，已退出。")
    return False



# ================= 扩展 AI：核验 Agent / RAG / 多模态 =================
KB_DIR = os.path.join(BASE_DIR, "data", "kb")
_KB_CACHE = {"at": 0.0, "chunks": []}


def _kb_chunks():
    chunks = []
    if not os.path.isdir(KB_DIR):
        return chunks
    for fn in sorted(os.listdir(KB_DIR)):
        if not fn.lower().endswith(".md"):
            continue
        try:
            with open(os.path.join(KB_DIR, fn), "r", encoding="utf-8") as f:
                text = f.read()
        except Exception:
            continue
        title = fn[:-3]
        for i, p in enumerate(re.split(r"\n\s*\n", text)):
            p = p.strip()
            if len(p) < 20:
                continue
            chunks.append({"id": "%s#%d" % (fn, i), "title": title, "text": p[:800]})
    return chunks


def kb_chunks():
    if time.time() - _KB_CACHE["at"] > 60:
        _KB_CACHE["chunks"] = _kb_chunks()
        _KB_CACHE["at"] = time.time()
    return _KB_CACHE["chunks"]


def kb_search(query, k=4):
    """本地 BM25 检索，零额外接口成本"""
    chunks = kb_chunks()
    if not chunks:
        return []
    q = list(_bigrams(query))
    if not q:
        return []
    docs, df = [], {}
    for c in chunks:
        toks = list(_bigrams(c["text"] + " " + c["title"]))
        docs.append(toks)
        for t in set(toks):
            df[t] = df.get(t, 0) + 1
    n = len(docs)
    avg = sum(len(d) for d in docs) / max(1, n)
    k1, b = 1.5, 0.75
    scored = []
    for c, toks in zip(chunks, docs):
        tf = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        s = 0.0
        for t in q:
            if t not in tf:
                continue
            idf = math.log(1 + (n - df.get(t, 0) + 0.5) / (df.get(t, 0) + 0.5))
            s += idf * (tf[t] * (k1 + 1)) / (tf[t] + k1 * (1 - b + b * len(toks) / avg))
        if s > 0:
            scored.append((s, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [{"score": round(s, 3), "title": c["title"], "text": c["text"]}
            for s, c in scored[:k]]


def _ask_llm(question, hits):
    cfg = load_ai_config()
    if not (cfg.get("enabled") and cfg.get("api_key") and cfg.get("base_url")):
        return ""
    context = "\n\n".join("[%d] %s：%s" % (i + 1, h["title"], h["text"]) for i, h in enumerate(hits))
    payload = {
        "model": cfg.get("model") or "deepseek-chat",
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": "你是校园失物招领平台的问答助手。只能依据给定资料回答，"
                                          "引用资料时用 [1][2] 标注；资料里没有的信息就直说不知道。"},
            {"role": "user", "content": "资料：\n%s\n\n问题：%s" % (context, question)},
        ],
    }
    try:
        data = _post_chat(cfg.get("base_url").rstrip("/") + "/chat/completions", payload,
                          cfg.get("api_key"), timeout=25)
        return (data["choices"][0]["message"]["content"] or "").strip()
    except Exception:
        return ""


def _ask_general(question):
    """知识库没命中时，用大模型做通用校园向导，并强制加免责说明"""
    cfg = load_ai_config()
    if not (cfg.get("enabled") and cfg.get("api_key") and cfg.get("base_url")):
        return ""
    payload = {
        "model": cfg.get("model") or "deepseek-chat",
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content":
                "你是清华校园向导，面向游客、新生和家长回答进校、交通、食堂、校园卡、参观、"
                "丢东西等常见问题。用 3 到 5 句话回答，口语化、可执行。"
                "不确定的政策、电话、价格、开放时间不要编造，要提醒“以学校最新公告为准”。"
                "不要回答与校园无关的闲聊。"},
            {"role": "user", "content": str(question)[:200]},
        ],
    }
    try:
        data = _post_chat(cfg.get("base_url").rstrip("/") + "/chat/completions", payload,
                          cfg.get("api_key"), timeout=25)
        return (data["choices"][0]["message"]["content"] or "").strip()
    except Exception:
        return ""


def ask_kb(question):
    hits = kb_search(question, 4)
    answer = _ask_llm(question, hits) if hits else ""
    if not answer and not hits:
        answer = _ask_general(question)
    if not answer:
        if not hits:
            answer = "知识库里暂时没有找到相关内容，可以换个说法，或直接发布一条启事。"
        else:
            answer = "根据资料：\n" + "\n".join(
                "[%d] %s" % (i + 1, h["text"][:160]) for i, h in enumerate(hits))
    return {"ok": True, "answer": answer,
            "sources": [{"title": h["title"], "text": h["text"][:200], "score": h["score"]} for h in hits]}


# ---------- 核验 Agent ----------
AGENT_TOOL_DEFS = [
    {"name": "get_item", "description": "读取物品详情与独有特征", "params": {"item_id": "string"}},
    {"name": "get_claim", "description": "读取申请内容与补充历史", "params": {"claim_id": "string"}},
    {"name": "search_similar", "description": "检索库内相似物品", "params": {"text": "string", "k": "int"}},
    {"name": "check_reports", "description": "查询举报记录", "params": {"item_id": "string"}},
    {"name": "policy_check", "description": "检查内容是否命中平台规则", "params": {"text": "string"}},
]


def _tool_get_item(item_id):
    with LOCK:
        items = load_items()
    it = next((x for x in items if x.get("id") == item_id), None)
    if not it:
        return {"error": "not found"}
    return {"id": it.get("id"), "title": it.get("title"), "desc": it.get("desc"),
            "place": it.get("place"), "cat": it.get("cat"), "status": it.get("status"),
            "secret": it.get("secret") or "", "reports": len(it.get("reports") or [])}


def _tool_get_claim(claim_id):
    with LOCK:
        claims = load_claims()
    c = next((x for x in claims if x.get("id") == claim_id), None)
    if not c:
        return {"error": "not found"}
    return {"id": c.get("id"), "status": c.get("status"), "kind": c.get("kind"),
            "message": c.get("message") or "", "updatedAt": c.get("updatedAt")}


def _tool_search_similar(text, k=5):
    with LOCK:
        items = load_items()
    probe = {"title": text, "desc": text, "place": "", "cat": ""}
    scored = []
    for it in items:
        if it.get("status") not in ("approved", "claimed", "closed"):
            continue
        sc = match_score(probe, it)
        if sc > 0.05:
            scored.append((sc, it))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [{"id": it.get("id"), "title": it.get("title"), "score": sc}
            for sc, it in scored[:k]]


def _tool_check_reports(item_id):
    with LOCK:
        items = load_items()
    it = next((x for x in items if x.get("id") == item_id), None)
    reps = (it or {}).get("reports") or []
    return {"count": len(reps), "reasons": [r.get("reason") for r in reps if r.get("reason")][:5]}


def _tool_policy_check(text):
    hits = scope_violation({"title": text, "desc": "", "secret": ""})
    blocked = [w for w in TITLE_BLOCK if w in (text or "")]
    return {"scope_hits": hits, "blocked_words": blocked}


TOOL_IMPL = {
    "get_item": _tool_get_item,
    "get_claim": _tool_get_claim,
    "search_similar": _tool_search_similar,
    "check_reports": _tool_check_reports,
    "policy_check": _tool_policy_check,
}


def _agent_synthesize(item, claim, evidence):
    cfg = load_ai_config()
    prompt = (
        "你是校园失物招领平台的核验助手。根据证据判断申请人是否是物品主人。\n"
        "规则：如果申请人描述的特征与物品独有特征吻合，倾向 accept；细节不足则 need_more；"
        "明显不符或举报过多则 reject。\n"
        "只输出 JSON：{\"decision\":\"accept|need_more|reject\",\"confidence\":0到1,"
        "\"reason\":\"不超过60字\",\"missing\":[\"还缺哪些细节\"]}\n"
        "证据：%s" % json.dumps(evidence, ensure_ascii=False)
    )
    if cfg.get("enabled") and cfg.get("api_key") and cfg.get("base_url"):
        try:
            data = _post_chat(cfg.get("base_url").rstrip("/") + "/chat/completions",
                              {"model": cfg.get("model") or "deepseek-chat", "temperature": 0.1,
                               "messages": [{"role": "user", "content": prompt}]},
                              cfg.get("api_key"), timeout=25)
            text = data["choices"][0]["message"]["content"] or ""
            m = re.search(r"\{[\s\S]*\}", text)
            if m:
                obj = json.loads(m.group(0))
                d = str(obj.get("decision") or "").strip()
                if d not in ("accept", "need_more", "reject"):
                    d = "need_more"
                try:
                    conf = float(obj.get("confidence"))
                except Exception:
                    conf = 0.5
                return {"decision": d, "confidence": max(0.0, min(1.0, conf)),
                        "reason": str(obj.get("reason") or "")[:120],
                        "missing": [str(x)[:40] for x in (obj.get("missing") or [])][:3],
                        "source": "llm"}
        except Exception:
            pass
    secret = (item.get("secret") or "").strip()
    msg = (claim.get("message") or "").strip()
    reports = len(item.get("reports") or [])
    overlap = _cosine(_bigrams(secret), _bigrams(msg)) if secret and msg else 0.0
    if reports >= 3:
        return {"decision": "reject", "confidence": 0.8,
                "reason": "该物品被多次举报，建议先核实发布内容", "missing": [], "source": "rule"}
    if secret and overlap >= 0.22:
        return {"decision": "accept", "confidence": round(min(0.9, 0.55 + overlap), 2),
                "reason": "申请中提到的细节与独有特征吻合（重合度 %d%%）" % int(overlap * 100),
                "missing": [], "source": "rule"}
    if secret:
        return {"decision": "need_more", "confidence": 0.55,
                "reason": "申请细节与独有特征重合度较低，建议请对方补充",
                "missing": ["物品上特有的标记", "丢失的具体位置或时间"], "source": "rule"}
    return {"decision": "need_more", "confidence": 0.5,
            "reason": "发布者没有填写独有特征，建议补充后再判断",
            "missing": ["独有特征"], "source": "rule"}


def agent_review(item, claim, on_step=None):
    steps, evidence = [], []

    def call(name, **args):
        try:
            out = TOOL_IMPL[name](**args)
        except Exception as e:
            out = {"error": str(e)[:80]}
        step = {"tool": name, "args": args, "result": out}
        steps.append(step)
        if on_step:
            try:
                on_step(step)
            except Exception:
                pass
        finding = ""
        if name == "get_item":
            finding = "物品：%s；独有特征：%s" % (out.get("title"), out.get("secret") or "（未填写）")
        elif name == "get_claim":
            finding = "申请内容：%s" % (out.get("message") or "")[:80]
        elif name == "search_similar":
            finding = "相似物品 %d 条；最高 %s" % (
                len(out), (out[0]["score"] if out else "无"))
        elif name == "check_reports":
            finding = "举报 %d 次" % out.get("count", 0)
        elif name == "policy_check":
            finding = "范围命中：%s；违禁词：%s" % (
                "、".join(out.get("scope_hits") or []) or "无",
                "、".join(out.get("blocked_words") or []) or "无")
        evidence.append({"tool": name, "finding": finding})

    call("get_item", item_id=item.get("id"))
    call("get_claim", claim_id=claim.get("id"))
    call("check_reports", item_id=item.get("id"))
    call("policy_check", text=(item.get("title") or "") + " " + (item.get("desc") or "") + " " + (claim.get("message") or ""))
    call("search_similar", text=(item.get("title") or "") + " " + (item.get("desc") or ""), k=5)

    verdict = _agent_synthesize(item, claim, evidence)
    return {"ok": True, "decision": verdict["decision"], "confidence": verdict["confidence"],
            "reason": verdict["reason"], "missing": verdict.get("missing") or [],
            "source": verdict.get("source"), "evidence": evidence, "steps": steps,
            "tools": [t["name"] for t in AGENT_TOOL_DEFS]}




# ---------- 寻物 Agent：雷达 + 侦探 ----------
PLACE_GROUPS = [
    ("图书馆", ("图书馆", "北馆", "李文正", "老馆", "library", "自习室", "借还")),
    ("食堂", ("食堂", "餐厅", "观畴", "清芬", "桃李", "紫荆园", "听涛", "万人", "canteen")),
    ("教学楼", ("教学楼", "二教", "三教", "四教", "五教", "六教", "教室", "学堂", "新水", "旧水", "建筑馆")),
    ("操场", ("操场", "紫操", "东操", "西操", "体育", "综体", "篮球", "网球", "游泳", "跑道", "球场")),
    ("宿舍", ("宿舍", "紫荆公寓", "公寓", "楼管", "寝室", "南区", "北区")),
    ("快递", ("快递", "驿站", "菜鸟", "取件")),
    ("湖/荷塘", ("湖", "荷塘", "近春园", "水木清华")),
    ("校门", ("校门", "门口", "东门", "西门", "南门", "二校门")),
]


def _place_group(place):
    p = str(place or "").strip()
    if not p:
        return "未填写地点"
    low = p.lower()
    for name, keys in PLACE_GROUPS:
        if any(k.lower() in low for k in keys):
            return name
    return p[:12]


def _hotspot_stats(items, limit=6):
    groups = {}
    for it in items:
        if it.get("status") not in ("approved", "claimed", "closed"):
            continue
        if it.get("type") not in ("lost", "found"):
            continue
        g = _place_group(it.get("place"))
        if g == "未填写地点":
            continue
        row = groups.setdefault(g, {"place": g, "count": 0, "lost": 0, "found": 0})
        row["count"] += 1
        row["lost" if it.get("type") == "lost" else "found"] += 1
    out = sorted(groups.values(), key=lambda x: (-x["count"], x["place"]))
    total = sum(x["count"] for x in out) or 1
    for x in out:
        x["share"] = int(round(x["count"] * 100.0 / total))
    return out[:limit]


def _radar_matches(item, items):
    """把一条寻物/招领与全站反向类型做匹配，返回可解释的候选。"""
    target = "found" if item.get("type") == "lost" else "lost"
    base_group = _place_group(item.get("place"))
    base_time = item.get("createdAt") or 0
    out = []
    for x in items:
        if x.get("id") == item.get("id"):
            continue
        if x.get("type") != target:
            continue
        if x.get("status") not in ("approved", "claimed"):
            continue
        text_probe = ((item.get("title") or "") * 2) + (item.get("desc") or "")
        text_cand = ((x.get("title") or "") * 2) + (x.get("desc") or "")
        text_score = _cosine(_bigrams(text_probe), _bigrams(text_cand))
        x_group = _place_group(x.get("place"))
        same_place = bool(base_group and base_group != "未填写地点" and base_group == x_group)
        same_cat = bool(item.get("cat") and item.get("cat") == x.get("cat"))
        gap_h = None
        if base_time and x.get("createdAt"):
            gap_h = abs(int(base_time) - int(x.get("createdAt"))) / 3600000.0
        time_close = gap_h is not None and gap_h <= 24 * 7
        # 文字必须有实质重合；地点/时间只能加分，不能单独造出匹配
        if text_score < 0.12:
            continue
        score = text_score * 0.72 + (0.10 if same_place else 0) + (0.08 if time_close else 0) + (0.10 if same_cat else 0)
        if score < 0.16:
            continue
        reasons = []
        if same_place:
            reasons.append("地点都在%s" % base_group)
        if time_close:
            reasons.append("发布时间接近")
        if same_cat:
            reasons.append("同类物品")
        if text_score >= 0.30:
            reasons.append("描述相似")
        if not reasons:
            reasons.append("标题/描述有重合")
        pct = max(1, min(99, int(round(score * 100))))
        out.append({
            "item": public_item(x, None),
            "score": pct,
            "textScore": int(round(text_score * 100)),
            "confidence": "高" if pct >= 68 else ("中" if pct >= 45 else "低"),
            "reasons": reasons[:3],
            "placeGroup": x_group,
            "gapHours": int(gap_h) if gap_h is not None else None,
        })
    out.sort(key=lambda x: (-x["score"], -(x["item"].get("createdAt") or 0)))
    return out[:5]


def agent_radar(item, items):
    matches = _radar_matches(item, items)
    hotspots = _hotspot_stats(items)
    scanned = len([x for x in items if x.get("status") in ("approved", "claimed", "closed")])
    steps = [
        {"tool": "scan_items", "finding": "扫描全站 %d 条公开信息" % scanned},
        {"tool": "match", "finding": "按地点、时间、描述比对，命中 %d 条" % len(matches)},
        {"tool": "hotspot", "finding": "最高频区域：%s" % (hotspots[0]["place"] if hotspots else "暂无数据")},
    ]
    return {
        "ok": True,
        "item": public_item(item, None),
        "matches": matches,
        "hotspots": hotspots,
        "scanned": scanned,
        "steps": steps,
        "summary": ("给你找到 %d 条可能相关的招领，先看置信度最高的那条。" % len(matches))
                   if matches else "暂时没有高置信度匹配，可以看下面的高频区域，或让侦探推理下一步。",
    }


def _place_tips(group):
    return {
        "图书馆": ["北馆（李文正馆）一层服务台", "老图书馆借还处", "自助借还机旁"],
        "食堂": ["观畴园（万人食堂）一层服务台", "清芬园入口失物箱", "桃李园前台"],
        "教学楼": ["六教 3 区物业值班室", "三教 / 四教楼管室", "教室讲台和后排"],
        "操场": ["紫操器材室", "综体前台", "看台入口和跑道边"],
        "宿舍": ["紫荆公寓楼管值班室", "一楼公告栏", "洗衣房"],
        "快递": ["快递驿站取件台", "驿站门口货架", "宿舍楼下快递点"],
        "湖/荷塘": ["近春园荷塘边座椅", "水木清华附近长椅", "湖边步道"],
        "校门": ["东门 / 二校门门卫", "校门附近保安亭", "进校闸机旁"],
    }.get(group, ["校方失物招领点", "就近的楼管 / 前台"])


def agent_detective(item, items):
    matches = _radar_matches(item, items)
    hotspots = _hotspot_stats(items)
    group = _place_group(item.get("place"))
    tips = _place_tips(group)
    actions = []
    if matches:
        top = matches[0]
        actions.append({
            "title": "先联系这条招领",
            "detail": "%s（置信度 %d%%）——%s" % (
                top["item"].get("title") or "招领", top["score"], "、".join(top["reasons"])),
            "itemId": top["item"].get("id"),
        })
    for t in tips[:3]:
        actions.append({"title": "去%s找找" % t, "detail": "按丢失地点推断，这里最可能先被送到。", "itemId": ""})
    for h in hotspots[:2]:
        if h["place"] == group:
            continue
        actions.append({
            "title": "顺路看一眼%s" % h["place"],
            "detail": "全站 %d 条失物里，%s 是高频区域（%d 条）。" % (
                sum(x["count"] for x in hotspots), h["place"], h["count"]),
            "itemId": "",
        })
    actions.append({"title": "在校园地图里看路线", "detail": "打开「初入清华」里的校园地图，按顺序走一遍。", "itemId": ""})

    timeline = []
    if item.get("eventTime"):
        timeline.append({"time": str(item.get("eventTime")), "label": "你填的丢失时间"})
    elif item.get("createdAt"):
        timeline.append({"time": time.strftime("%m-%d %H:%M", time.localtime(int(item["createdAt"]) / 1000)), "label": "你发布寻物的时间"})
    for m in matches[:2]:
        timeline.append({
            "time": time.strftime("%m-%d %H:%M", time.localtime(int((m["item"].get("createdAt") or now_ms()) / 1000))),
            "label": "招领：%s" % (m["item"].get("title") or "未命名"),
        })
    if hotspots:
        timeline.append({"time": "统计", "label": "高频区域：%s" % "、".join(h["place"] for h in hotspots[:3])})

    top_score = matches[0]["score"] if matches else 0
    return {
        "ok": True,
        "item": public_item(item, None),
        "matches": matches,
        "hotspots": hotspots,
        "timeline": timeline,
        "actions": actions[:6],
        "steps": [
            {"tool": "read_item", "finding": "读取丢失地点：%s" % (item.get("place") or "未填写")},
            {"tool": "match", "finding": "比对 %d 条反向信息，命中 %d 条" % (len(items), len(matches))},
            {"tool": "hotspot", "finding": "计算校园高频区域"},
            {"tool": "plan", "finding": "生成 %d 条行动建议" % len(actions[:6])},
        ],
        "confidence": "高" if top_score >= 68 else ("中" if top_score >= 45 else "低"),
        "summary": "按你给的地点和时间，先看匹配到的招领，再按下面的顺序找。",
        "disclaimer": "以上是线索建议，不保证物品一定在这些位置；找到后请当面核对特征。",
    }





# ---------- 寻物侦探：路线推理 ----------
def _parse_route(route):
    raw = str(route or "").strip()
    if not raw:
        return []
    parts = re.split(r"[→>\-、,，;；\n]+", raw)
    out = []

    def push(x):
        x = str(x or "").strip()
        if x and x not in out:
            out.append(x[:16])

    for part in parts:
        p = part.strip()
        if not p:
            continue
        # 允许用户直接叙述一整天：从长句里按地图地点顺序抽取
        found = []
        low = p.lower()
        for name, keys in PLACE_GROUPS:
            pos = -1
            for k in keys:
                q = low.find(k.lower())
                if q >= 0 and (pos < 0 or q < pos):
                    pos = q
            if pos >= 0:
                found.append((pos, name))
        found.sort()
        if found and (len(p) > 8 or "→" not in raw):
            for _, name in found:
                push(name)
        else:
            push(p)
    return out[:8]


def _item_kind(item):
    text = (item.get("title") or "") + (item.get("desc") or "") + (item.get("summary") or "")
    if any(k in text for k in ("校园卡", "身份证", "银行卡", "钱包", "卡套")):
        return "card"
    if any(k in text for k in ("钥匙", "钥匙扣")):
        return "keys"
    if any(k in text for k in ("伞", "雨伞")):
        return "umbrella"
    if any(k in text for k in ("电脑", "键盘", "手机", "耳机", "充电宝", "平板")):
        return "electronics"
    if any(k in text for k in ("杯", "水壶", "保温杯")):
        return "bottle"
    return "other"


RISK = {
    "card": {"食堂": .94, "宿舍": .90, "快递": .80, "图书馆": .58, "教学楼": .54, "操场": .35, "湖/荷塘": .16, "校门": .24},
    "keys": {"操场": .92, "食堂": .82, "宿舍": .78, "快递": .70, "教学楼": .46, "图书馆": .40, "湖/荷塘": .26, "校门": .32},
    "umbrella": {"图书馆": .90, "食堂": .84, "教学楼": .78, "宿舍": .45, "快递": .38, "湖/荷塘": .52, "校门": .70},
    "electronics": {"教学楼": .90, "图书馆": .86, "宿舍": .55, "食堂": .35, "湖/荷塘": .20, "校门": .30},
    "bottle": {"教学楼": .86, "图书馆": .82, "食堂": .62, "操场": .55, "湖/荷塘": .35, "校门": .30},
    "other": {"图书馆": .70, "教学楼": .66, "食堂": .62, "宿舍": .58, "操场": .50, "快递": .48, "湖/荷塘": .30, "校门": .34},
}

RISK_REASON = {
    ("card", "食堂"): "食堂付款、坐下吃饭时，卡最容易从口袋滑到座位或桌边。",
    ("card", "宿舍"): "回宿舍躺下、换衣服时，卡容易从口袋掉到床上或地上。",
    ("card", "快递"): "取快递蹲下、签字时，口袋里的卡容易滑出来。",
    ("card", "图书馆"): "在图书馆落座、刷卡进馆时，卡可能落在闸机或座位旁。",
    ("card", "教学楼"): "教室坐下、掏东西时，卡可能从口袋滑到课桌抽屉。",
    ("keys", "操场"): "跑步、运动时钥匙最容易从口袋甩出，先看跑道边和器材室。",
    ("keys", "食堂"): "在食堂坐下时，钥匙串容易从口袋滑到座椅缝。",
    ("keys", "宿舍"): "回宿舍换衣服、放包时，钥匙容易落在桌边或床上。",
    ("umbrella", "图书馆"): "雨伞最容易落在图书馆门口伞架、座位旁或借还机边。",
    ("umbrella", "食堂"): "进食堂时伞通常放在门口伞架，先看入口和座位旁。",
    ("umbrella", "教学楼"): "教学楼门口伞架、教室后排是雨伞最常被忘的地方。",
    ("electronics", "教学楼"): "键盘、电脑通常落在教室座位、讲台或机房桌下。",
    ("electronics", "图书馆"): "图书馆插座旁、自习座位是电子设备最常被忘的位置。",
    ("bottle", "教学楼"): "水杯常落在教室桌角、饮水机旁或窗台。",
    ("bottle", "图书馆"): "水杯常落在自习桌、借还机旁或窗台。",
}


def _probe_item(body):
    title = str(body.get("title") or "").strip()
    if not title and isinstance(body.get("query"), dict):
        title = str(body["query"].get("title") or "").strip()
    if not title:
        return None
    return {
        "id": "q_" + uuid.uuid4().hex[:8],
        "type": str(body.get("type") or "lost"),
        "cat": str(body.get("cat") or "other"),
        "title": title[:40],
        "desc": str(body.get("desc") or "")[:200],
        "place": str(body.get("place") or "")[:40],
        "eventTime": "", "status": "approved", "createdAt": now_ms(),
    }


def _route_group(stop):
    g = _place_group(stop)
    if "快递" in stop:
        return "快递"
    return g


def agent_detective_route(item, items, route, carry="", last_seen=""):
    data = agent_detective(item, items)
    stops = _parse_route(route)
    data["routeStops"] = stops
    kind = _item_kind(item)
    ranked = []
    carry_bonus = {"口袋": .06, "背包": -.02, "手持": .02}.get(carry, 0)
    for i, stop in enumerate(stops):
        g = _route_group(stop)
        risk = RISK.get(kind, RISK["other"]).get(g, 0.42)
        if carry == "口袋" and g in ("食堂", "宿舍", "快递"):
            risk += carry_bonus
        if carry == "背包" and g in ("图书馆", "教学楼"):
            risk += .04
        if carry == "手持" and g in ("图书馆", "食堂"):
            risk += .03
        risk = min(0.98, risk)
        reason = RISK_REASON.get((kind, g)) or ("你经过%s，%s最可能在这里被放下或滑出口袋。" % (stop, "物品"))
        if carry:
            reason += " 你补充：平时放在%s。" % carry
        ranked.append((risk, i, stop, g, reason))
    ranked.sort(key=lambda x: (-x[0], -x[1]))
    route_actions = []
    for risk, i, stop, g, reason in ranked[:4]:
        route_actions.append({
            "title": "回%s找找" % stop,
            "detail": reason + "（路径风险 %d%%）" % int(risk * 100),
            "itemId": "",
        })
    existing = data.get("actions") or []
    data["actions"] = (route_actions + existing)[:6]
    data["routeKind"] = kind
    top = ranked[0] if ranked else None
    if top:
        data["summary"] = "按你今天的路线：%s。结合「%s」这类物品，优先回%s找，原因：%s" % (
            " → ".join(stops), item.get("title") or "失物", top[2], top[4])
    if last_seen:
        data["summary"] = "最后确认还在：%s。%s" % (last_seen, data.get("summary") or "")
    tl = data.get("timeline") or []
    route_tl = []
    if stops:
        route_tl.append({"time": "路线", "label": " → ".join(stops)})
    if carry:
        route_tl.append({"time": "携带", "label": carry})
    if last_seen:
        route_tl.append({"time": "最后确认", "label": last_seen})
    data["timeline"] = route_tl + tl
    data["disclaimer"] = "路线推测只根据你提供的地点、时间和物品类型，不保证一定找到；找到后请当面核对特征。"
    ai = _llm_detective(item, data, stops, carry, last_seen)
    if ai:
        data["summary"] = ai.get("summary") or data.get("summary")
        data["actions"] = ai.get("actions") or data.get("actions")
        data["confidence"] = ai.get("confidence") or data.get("confidence")
        data["source"] = "llm"
    else:
        data["source"] = "rule"
    return data




def _llm_detective(item, data, stops, carry, last_seen):
    """用大模型把规则结果改写成更像侦探的推理；失败时回退规则。"""
    cfg = load_ai_config()
    if not (cfg.get("enabled") and cfg.get("api_key") and cfg.get("base_url")):
        return None
    evidence = {
        "物品": item.get("title") or "",
        "描述": (item.get("desc") or "")[:160],
        "丢失地点": item.get("place") or "",
        "路线": stops,
        "携带方式": carry,
        "最后确认": last_seen,
        "招领候选": [{"标题": m.get("item", {}).get("title"), "分数": m.get("score"), "理由": m.get("reasons")}
                   for m in (data.get("matches") or [])[:4]],
        "高频区域": [{"地点": h.get("place"), "数量": h.get("count")} for h in (data.get("hotspots") or [])[:5]],
        "规则建议": [a.get("title") for a in (data.get("actions") or [])[:6]],
    }
    prompt = (
        "你是清华校园的寻物侦探。根据给定证据，推测物品最可能在哪里，并给出可执行的寻找顺序。\n"
        "要求：1) 必须结合物品类型、路线、携带方式、最后确认地点；2) 不能断言一定找到；"
        "3) 建议要具体到地点/窗口/动作；4) 只输出 JSON，不要 markdown。\n"
        "JSON 格式：{\"summary\":\"不超过80字\",\"confidence\":\"高|中|低\","
        "\"actions\":[{\"title\":\"不超过18字\",\"detail\":\"不超过60字\"}]}，actions 3到6条。\n"
        "证据：%s" % json.dumps(evidence, ensure_ascii=False)
    )
    try:
        out = _post_chat(cfg.get("base_url").rstrip("/") + "/chat/completions",
                         {"model": cfg.get("model") or "deepseek-chat", "temperature": 0.2,
                          "messages": [{"role": "user", "content": prompt}]},
                         cfg.get("api_key"), timeout=25)
        text = out["choices"][0]["message"]["content"] or ""
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            return None
        obj = json.loads(m.group(0))
        actions = []
        for a in (obj.get("actions") or [])[:6]:
            title = str(a.get("title") or "").strip()
            detail = str(a.get("detail") or "").strip()
            if title:
                actions.append({"title": title[:24], "detail": detail[:120], "itemId": ""})
        if not actions:
            return None
        conf = str(obj.get("confidence") or "中").strip()
        if conf not in ("高", "中", "低"):
            conf = "中"
        return {"summary": str(obj.get("summary") or "").strip()[:120],
                "actions": actions, "confidence": conf}
    except Exception:
        return None


# ---------- 多模态 ----------
def vision_config():
    return {
        "api_key": os.environ.get("VISION_API_KEY", ""),
        "base_url": os.environ.get("VISION_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
        "model": os.environ.get("VISION_MODEL", "glm-4v-flash"),
    }


def vision_moderate(image_b64, mime="image/jpeg"):
    """专用于审核：把图中文字抄出来，并判断是否有违规内容"""
    cfg = vision_config()
    if not cfg["api_key"]:
        return ""
    endpoint = cfg["base_url"].rstrip("/") + "/chat/completions"
    payload = {
        "model": cfg["model"],
        "temperature": 0,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": "你是内容审核助手。看这张图，只输出 JSON："
                                     "{\"text\":\"图中所有文字，原样抄写，没有就空\","
                                     "\"risk\":\"是否含代考代课、色情、诈骗、赌博、广告引流等违规内容，没有就写无\"}"},
            {"type": "image_url", "image_url": {"url": "data:%s;base64,%s" % (mime, image_b64)}},
        ]}],
    }
    try:
        data = _post_chat(endpoint, payload, cfg["api_key"], timeout=35)
        text = data["choices"][0]["message"]["content"] or ""
        m = re.search(r"\{[\s\S]*\}", text)
        obj = json.loads(m.group(0)) if m else {}
        parts = []
        if obj.get("text"):
            parts.append("图中文字：" + str(obj.get("text"))[:200])
        risk = str(obj.get("risk") or "").strip()
        if risk and risk not in ("无", "没有", "none"):
            parts.append("图片风险：" + risk[:100])
        return "；".join(parts)[:300]
    except Exception:
        return ""


def vision_analyze(image_b64, mime="image/jpeg"):
    cfg = vision_config()
    if not cfg["api_key"]:
        return {"ok": False, "reason": "未配置视觉模型（VISION_API_KEY），可先手动选择分类"}
    endpoint = cfg["base_url"].rstrip("/") + "/chat/completions"
    prompts = [
        "你是校园失物识别器。看这张照片，只输出 JSON，不要解释、不要 markdown："
        "{\"category\":\"具体物品，如雨伞/校园卡/钥匙/耳机/水杯/书包/充电宝/其他\","
        "\"color\":\"主色，如黑色/蓝色/白色\","
        "\"brand\":\"能看到的品牌、文字或图案，没有就写无\","
        "\"features\":\"2 到 3 个能核对的显著特征，如划痕、贴纸、挂件\","
        "\"desc\":\"20 到 40 字的一句话描述\"}。"
        "即使模糊也要给出最可能的判断，不要留空。",
        "只输出一个 JSON 对象，字段 category/color/brand/features/desc。"
        "category 必须写出物品名称，color 必须写颜色。不要输出任何其他文字。",
    ]
    last = {}
    for prompt in prompts:
        payload = {
            "model": cfg["model"],
            "temperature": 0.1,
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": "data:%s;base64,%s" % (mime, image_b64)}},
            ]}],
        }
        try:
            data = _post_chat(endpoint, payload, cfg["api_key"], timeout=35)
            text = data["choices"][0]["message"]["content"] or ""
            m = re.search(r"\{[\s\S]*\}", text)
            obj = json.loads(m.group(0)) if m else {}
        except Exception as e:
            last = {"ok": False, "reason": str(e)[:120]}
            continue
        cat = str(obj.get("category") or "").strip()
        color = str(obj.get("color") or "").strip()
        feats = str(obj.get("features") or "").strip()
        desc = str(obj.get("desc") or "").strip()
        if cat and cat not in ("无法识别", "未知", "其他"):
            return {"ok": True, "category": cat[:20], "color": color[:20],
                    "brand": str(obj.get("brand") or "")[:40], "features": feats[:80],
                    "desc": desc[:120], "model": cfg["model"]}
        last = {"ok": True, "category": cat[:20], "color": color[:20],
                "brand": str(obj.get("brand") or "")[:40], "features": feats[:80],
                "desc": desc[:120], "model": cfg["model"]}
    return last if last.get("ok") else {"ok": False, "reason": last.get("reason") or "AI 没看清，请手动填写"}




# ================= 信息整理（AI 规范化） =================
FILLER_WORDS = ["大概", "好像", "似乎", "可能", "非常", "特别", "真的", "就是", "然后",
                "那个", "这个", "一下", "有点", "比较", "挺", "应该是", "反正", "其实"]
COLOR_WORDS = ["黑色", "白色", "蓝色", "红色", "绿色", "黄色", "紫色", "灰色", "粉色",
               "棕色", "银色", "金色", "橙色", "透明", "深蓝", "浅蓝", "米色", "卡其"]
COND_WORDS = ["全新", "九成新", "八成新", "七成新", "六成新", "五成新", "有磨损",
              "轻微磨损", "破损", "划痕", "掉漆", "断裂"]


def _format_fallback(title, desc, place=""):
    t = desc or ""
    for w in FILLER_WORDS:
        t = t.replace(w, "")
    t = re.sub(r"\s+", " ", t).strip("，。 ；;,.!")
    title = (title or "").strip()
    color = next((c for c in COLOR_WORDS if c in (title + t)), "")
    cond = next((c for c in COND_WORDS if c in (t + title)), "")
    desc_out = t[:60]
    summary = title or t[:16]
    if color and not summary.startswith(color):
        summary = color + " " + summary
    if place and place not in summary and place != "未填写地点":
        summary += " · " + place
    summary = summary[:30]
    return {
        "summary": summary,
        "desc": desc_out,
        "fields": {"color": color, "condition": cond, "brand": "", "feature": "", "contents": ""},
        "source": "rule",
    }


def format_item(title, desc):
    cfg = load_ai_config()
    prompt = (
        "你是校园失物招领的信息整理助手。把用户写的内容压缩成固定结构，"
        "只能使用原文已有的事实，绝对不要编造颜色、品牌、地点。\n"
        "要求：\n"
        "1) summary：不超过 30 字，格式「颜色 物品 · 一个最显著特征 · 地点」；\n"
        "2) desc：不超过 60 字，去掉形容堆砌和口头语，只保留事实；\n"
        "3) fields：从原文提取 color / brand / condition / feature / contents，没有就留空。\n"
        '只输出 JSON：{"summary":"","desc":"","fields":{"color":"","brand":"","condition":"","feature":"","contents":""}}\n'
        "标题：%s\n描述：%s" % (title, desc)
    )
    if cfg.get("enabled") and cfg.get("api_key") and cfg.get("base_url"):
        try:
            data = _post_chat(cfg.get("base_url").rstrip("/") + "/chat/completions",
                              {"model": cfg.get("model") or "deepseek-chat", "temperature": 0.1,
                               "messages": [{"role": "user", "content": prompt}]},
                              cfg.get("api_key"), timeout=20)
            text = data["choices"][0]["message"]["content"] or ""
            m = re.search(r"\{[\s\S]*\}", text)
            if m:
                obj = json.loads(m.group(0))
                out = {
                    "summary": str(obj.get("summary") or "")[:40],
                    "desc": str(obj.get("desc") or "")[:120],
                    "fields": {k: str((obj.get("fields") or {}).get(k) or "")[:30]
                               for k in ("color", "brand", "condition", "feature", "contents")},
                    "source": "llm",
                }
                if out["summary"] and out["desc"]:
                    return out
        except Exception:
            pass
    return _format_fallback(title, desc)


class Handler(BaseHTTPRequestHandler):
    server_version = "Shiguangli/4.0"

    def log_message(self, fmt, *args):
        try:
            sys.stdout.write("  · " + (fmt % args) + "\n")
            sys.stdout.flush()
        except Exception:
            pass

    # ---------- 基础 ----------
    def _send(self, code, body=b"", ctype="application/json; charset=utf-8", extra=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        headers = dict(extra or {})
        # 文本类内容做 gzip：首屏 88KB -> 约 18KB，跨国线路差别很大
        if body and len(body) > 800 and ("text/" in ctype or "json" in ctype or "javascript" in ctype):
            if "gzip" in (self.headers.get("Accept-Encoding") or "").lower():
                import gzip
                body = gzip.compress(body, 6)
                headers["Content-Encoding"] = "gzip"
                headers["Vary"] = "Accept-Encoding"
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", headers.pop("Cache-Control", "no-store"))
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            pass

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def _read_body(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(n) if n else b""
            return json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            return {}

    def _owner(self):
        return (self.headers.get("X-Owner") or "").strip()[:64]

    def _is_admin(self):
        tok = (self.headers.get("X-Admin-Token") or "").strip()
        exp = TOKENS.get(tok)
        if not exp:
            return False
        if exp < time.time():
            TOKENS.pop(tok, None)
            return False
        return True

    def _need_admin(self):
        if self._is_admin():
            return True
        self._json({"error": "unauthorized"}, 401)
        return False

    # ---------- 路由 ----------
    def do_GET(self):
        path = unquote(urlparse(self.path).path)

        if path in ("/", "/index.html"):
            return self._serve_file("web/dist/index.html")
        # Vue 预览别名与静态资源
        if path in ("/web", "/web/"):
            return self._serve_file("web/dist/index.html")
        if path.startswith("/web/assets/"):
            rel = path[len("/web/"):]
            target = os.path.abspath(os.path.join(BASE_DIR, "web", "dist", rel))
            if target.startswith(os.path.join(BASE_DIR, "web", "dist") + os.sep) and os.path.isfile(target):
                return self._serve_path(target)
            return self._send(404, "not found", "text/plain; charset=utf-8")
        if path == "/admin" or path == "/admin/":
            return self._serve_file("web/dist/index.html")
        if path == "/api/ping":
            with LOCK:
                return self._json({"ok": True, "items": len(load_items()),
                                   "uptime": int(time.time() - START_TS)})

        if path == "/api/health":
            with LOCK:
                n = len(load_items())
            avg = (AI_STATS["total_ms"] / AI_STATS["reviews"]) if AI_STATS["reviews"] else 0
            return self._json({"ok": True, "items": n, "ts": now_ms(),
                               "ai": {"reviews": AI_STATS["reviews"],
                                      "fail": AI_STATS["fail"],
                                      "avgMs": int(avg)}})

        if path.startswith("/api/items/") and path.endswith("/status"):
            owner = self._owner()
            item_id = path[len("/api/items/"):-len("/status")]
            with LOCK:
                items = load_items()
                item = next((x for x in items if x.get("id") == item_id), None)
            if not item or (item.get("ownerToken") != owner):
                return self._json({"error": "not found"}, 404)
            with QUEUE_LOCK:
                st = dict(QUEUE_STATE.get(item_id) or {})
            pos = queue_position(item_id) if st.get("state") in ("queued", "reviewing") else 0
            return self._json({"id": item_id, "status": item.get("status"),
                               "queue": st.get("state") or "", "position": pos,
                               "item": item if item.get("status") != "pending" else None})

        if path.startswith("/api/photo/"):
            item_id = path[len("/api/photo/"):]
            with LOCK:
                items = load_items()
            it = next((x for x in items if x.get("id") == item_id), None)
            if not it:
                return self._send(404, b"not found", "text/plain; charset=utf-8")
            if it.get("status") not in PUBLIC_STATUS and not self._is_admin():
                _tok = (parse_qs(urlparse(self.path).query).get("token") or [""])[0]
                _exp = TOKENS.get(_tok) if _tok else None
                if not _exp or _exp < time.time():
                    return self._send(403, b"forbidden", "text/plain; charset=utf-8")
            photo = str(it.get("photo") or "")
            if not photo:
                return self._send(404, b"no photo", "text/plain; charset=utf-8")
            try:
                raw = base64.b64decode(photo.split(",", 1)[-1])
            except Exception:
                return self._send(404, b"bad photo", "text/plain; charset=utf-8")
            etag = '"' + hashlib.md5(raw).hexdigest() + '"'
            if self.headers.get("If-None-Match") == etag:
                self.send_response(304)
                self.send_header("ETag", etag)
                self.end_headers()
                return
            return self._send(200, raw, "image/jpeg",
                              {"ETag": etag, "Cache-Control": "public, max-age=31536000"})

        if path.startswith("/api/items/") and path.endswith("/similar"):
            item_id = path[len("/api/items/"):-len("/similar")]
            with LOCK:
                all_items = load_items()
            it = next((x for x in all_items if x.get("id") == item_id), None)
            if not it:
                return self._json([])
            base_text = (it.get("title") or "") + " " + (it.get("desc") or "")

            def grams(t):
                t = re.sub(r"\s+", "", str(t or ""))
                return {t[i:i + 2] for i in range(max(0, len(t) - 1))}

            bg = grams(base_text)
            cands = []
            for x in all_items:
                if x.get("id") == item_id or x.get("status") != "approved":
                    continue
                if x.get("type") == it.get("type"):
                    continue
                score = 0
                if x.get("cat") == it.get("cat"):
                    score += 3
                if it.get("place") and x.get("place") and str(it["place"]) in str(x["place"]):
                    score += 2
                score += len(bg & grams((x.get("title") or "") + " " + (x.get("desc") or ""))) * 0.12
                if score >= 2.4:
                    cands.append((score, x))
            cands.sort(key=lambda p: p[0], reverse=True)
            return self._json([public_item(x, None) for _, x in cands[:3]])

        if path == "/api/tags/mine":
            owner = self._owner()
            if not owner:
                return self._json([])
            with LOCK:
                tags = [x for x in load_tags() if x.get("owner") == owner and x.get("active", True)]
            tags.sort(key=lambda x: x.get("createdAt") or 0, reverse=True)
            host = self.headers.get("Host") or "127.0.0.1:8000"
            scheme = "https" if self.headers.get("X-Forwarded-Proto") == "https" else "http"
            base = scheme + "://" + host
            return self._json([_tag_public(x, base, with_qr=True) for x in tags])

        if path.startswith("/api/tags/") and len(path) > len("/api/tags/"):
            code = path[len("/api/tags/"):].strip("/")
            with LOCK:
                tag = next((x for x in load_tags() if x.get("code") == code), None)
            if not tag:
                return self._json({"error": "拾光码不存在"}, 404)
            host = self.headers.get("Host") or "127.0.0.1:8000"
            scheme = "https" if self.headers.get("X-Forwarded-Proto") == "https" else "http"
            return self._json(_tag_public(tag, scheme + "://" + host, with_qr=False))

        if path == "/api/items":
            owner = self._owner()
            try:
                _qs0 = parse_qs(urlparse(self.path).query)
                _limit0 = int((_qs0.get("limit") or ["0"])[0] or 0)
            except Exception:
                _limit0 = 0
            _ckey = (owner or "") + "|" + str(_limit0)
            with ITEMS_CACHE_LOCK:
                _hit = (ITEMS_CACHE["key"] == _ckey and time.time() - ITEMS_CACHE["at"] < 10)
                _craw, _cetag = ITEMS_CACHE["raw"], ITEMS_CACHE["etag"]
            if _hit:
                if self.headers.get("If-None-Match") == _cetag:
                    self.send_response(304)
                    self.send_header("ETag", _cetag)
                    self.send_header("Cache-Control", "private, max-age=3")
                    self.send_header("Vary", "X-Owner")
                    self.end_headers()
                    return
                return self._send(200, _craw, "application/json; charset=utf-8",
                                  {"ETag": _cetag, "Cache-Control": "private, max-age=3",
                                   "Vary": "X-Owner"})
            with LOCK:
                items = [public_item(x, owner) for x in load_items()
                         if x.get("status") in PUBLIC_STATUS and public_visible(x)]
                _claims = load_claims()
            _my_claims = {c.get("itemId"): c for c in _claims if c.get("from") == owner}
            for _x in items:
                _c = _my_claims.get(_x.get("id"))
                if _c:
                    _x["myClaim"] = _c.get("status")
                    _x["myClaimId"] = _c.get("id")
            items.sort(key=lambda x: x.get("createdAt") or 0, reverse=True)
            try:
                qs = parse_qs(urlparse(self.path).query)
                limit = int((qs.get("limit") or ["0"])[0] or 0)
                if 0 < limit < len(items):
                    items = items[:limit]
            except Exception:
                pass
            raw = json.dumps(items, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            etag = '"' + hashlib.md5(raw + (owner or "").encode("utf-8")).hexdigest() + '"'
            with ITEMS_CACHE_LOCK:
                ITEMS_CACHE.update({"key": _ckey, "at": time.time(), "raw": raw, "etag": etag})
            if self.headers.get("If-None-Match") == etag:
                self.send_response(304)
                self.send_header("ETag", etag)
                self.send_header("Cache-Control", "public, max-age=5")
                self.send_header("Vary", "X-Owner")
                self.end_headers()
                return
            return self._send(200, raw, "application/json; charset=utf-8",
                              {"ETag": etag, "Cache-Control": "private, max-age=3",
                               "Vary": "X-Owner"})

        if path == "/api/sync":
            # 一次请求同时拿公开列表 + 我的发布，省掉一个往返（跨国线路很值钱）
            owner = self._owner()
            with LOCK:
                all_items = load_items()
            pub = [public_item(x, owner) for x in all_items
                   if x.get("status") in PUBLIC_STATUS and public_visible(x)]
            with LOCK:
                _claims = load_claims()
            _my_claims = {c.get("itemId"): c for c in _claims if c.get("from") == owner}
            for _x in pub:
                _c = _my_claims.get(_x.get("id"))
                if _c:
                    _x["myClaim"] = _c.get("status")
                    _x["myClaimId"] = _c.get("id")
            mine = [x for x in all_items if owner and x.get("ownerToken") == owner]
            pub.sort(key=lambda x: x.get("createdAt") or 0, reverse=True)
            mine.sort(key=lambda x: x.get("createdAt") or 0, reverse=True)
            with LOCK:
                notices = load_notices()
                claims_all = load_claims()
            mine_ids = {x.get("id") for x in mine}
            unread = sum(1 for n in notices if n.get("owner") == owner and not n.get("read"))
            pending_claims = sum(1 for c in claims_all
                                 if c.get("itemId") in mine_ids and c.get("status") == "pending")
            return self._json({"items": pub, "mine": mine, "serverTime": now_ms(),
                               "unread": unread, "claims": pending_claims})

        if path == "/api/mine":
            owner = self._owner()
            if not owner:
                return self._json([])
            with LOCK:
                items = [x for x in load_items() if x.get("ownerToken") == owner]
            items.sort(key=lambda x: x.get("createdAt") or 0, reverse=True)
            return self._json(items)

        if path == "/api/claims":
            owner = self._owner()
            if not owner:
                return self._json({"received": [], "sent": []})
            with LOCK:
                items = {x.get("id"): x for x in load_items()}
                claims = load_claims()

            def pack(c, side):
                it = items.get(c.get("itemId"), {})
                out = {
                    "id": c.get("id"), "itemId": c.get("itemId"),
                    "kind": c.get("kind") or "claim",
                    "itemTitle": it.get("title") or "",
                    "itemType": it.get("type") or "",
                    "itemStatus": it.get("status") or "",
                    "message": c.get("message") or "",
                    "history": c.get("history") or [],
                    "aiCheck": c.get("aiCheck") or None,
                    "status": c.get("status") or "pending",
                    "createdAt": c.get("createdAt") or 0,
                }
                # 只有发布者能看到自己这条的完整细节（含独有特征），用来和申请人核对
                if side == "received":
                    out["itemDesc"] = it.get("desc") or ""
                    out["itemPlace"] = it.get("place") or ""
                    out["itemSecret"] = it.get("secret") or ""
                    out["itemCat"] = it.get("cat") or ""
                    out["itemPhoto"] = it.get("photo") or ""
                    # 联系方式：没通过之前只给打码版本
                    if c.get("contact"):
                        out["claimContact"] = (
                            c.get("contact") if c.get("status") in ("accepted", "completed")
                            else mask_contact(c.get("contact"))
                        )
                if c.get("status") in ("accepted", "completed"):
                    out["ownerContact"] = (it.get("contact") or {}).get("phone") or ""
                    out["claimContact"] = c.get("contact") or ""
                if c.get("status") == "accepted" and c.get("returnCode"):
                    if c.get("returnCodeFor") == owner:
                        out["returnCode"] = c.get("returnCode")
                    if c.get("holder") == owner:
                        out["canConfirm"] = True
                if c.get("status") == "completed":
                    out["completedAt"] = c.get("completedAt") or c.get("updatedAt") or 0
                return out

            received = [pack(c, "received") for c in claims
                        if (items.get(c.get("itemId")) or {}).get("ownerToken") == owner]
            sent = [pack(c, "sent") for c in claims if c.get("from") == owner]
            received.sort(key=lambda x: x["createdAt"], reverse=True)
            sent.sort(key=lambda x: x["createdAt"], reverse=True)
            return self._json({"received": received, "sent": sent})

        if path == "/api/notices":
            owner = self._owner()
            with LOCK:
                notices = load_notices()
            mine = [n for n in notices if n.get("owner") == owner]
            mine.sort(key=lambda x: x.get("at") or 0, reverse=True)
            unread = sum(1 for n in mine if not n.get("read"))
            return self._json({"items": mine[:50], "unread": unread})

        if path == "/api/admin/accounts":
            if not self._need_admin():
                return
            with LOCK:
                accs = load_accounts()
                items = load_items()
            counts = {}
            for x in items:
                t = x.get("ownerToken") or ""
                counts[t] = counts.get(t, 0) + 1
            out = []
            for a in accs:
                out.append({"id": a.get("id"), "phone": a.get("phone") or "",
                            "createdAt": a.get("createdAt") or 0,
                            "lastLoginAt": a.get("lastLoginAt") or 0,
                            "banned": bool(a.get("banned")),
                            "posts": counts.get(a.get("id"), 0)})
            out.sort(key=lambda x: x.get("createdAt") or 0, reverse=True)
            return self._json(out)

        if path == "/api/announcements":
            with LOCK:
                arr = load_announcements()
            pub = [a for a in arr if a.get("status") == "published"]
            pub.sort(key=lambda x: (not x.get("pinned"), -(x.get("publishedAt") or 0)))
            return self._json([{"id": a.get("id"), "title": a.get("title"),
                                "body": a.get("body"), "pinned": bool(a.get("pinned")),
                                "publishedAt": a.get("publishedAt") or 0} for a in pub])

        if path == "/api/admin/special-numbers":
            if not self._need_admin():
                return
            return self._json(load_special_numbers())

        if path == "/api/admin/deploy-log":
            if not self._need_admin():
                return
            try:
                with open("/opt/lostfound/deploy.log", "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()[-1200:]
            except Exception:
                text = ""
            return self._json({"ok": True, "log": text})

        if path == "/api/admin/stats":
            if not self._need_admin():
                return
            with LOCK:
                items = load_items()
                accounts = load_accounts()
                claims = load_claims()
                anns = load_announcements()
            by_status = {}
            for x in items:
                st = x.get("status") or "unknown"
                by_status[st] = by_status.get(st, 0) + 1
            now = time.time()
            days = []
            for i in range(6, -1, -1):
                day = time.strftime("%m-%d", time.localtime(now - i * 86400))
                start = (int(now) // 86400 - i) * 86400 * 1000
                end = start + 86400 * 1000
                n = sum(1 for x in items if start <= (x.get("createdAt") or 0) < end)
                days.append({"day": day, "count": n})
            c_status = {}
            for c in claims:
                c_status[c.get("status") or "pending"] = c_status.get(c.get("status") or "pending", 0) + 1
            return self._json({
                "items": len(items),
                "byStatus": by_status,
                "lost": sum(1 for x in items if x.get("type") == "lost"),
                "found": sum(1 for x in items if x.get("type") == "found"),
                "help": sum(1 for x in items if x.get("type") == "help"),
                "accounts": len(accounts),
                "banned": sum(1 for a in accounts if a.get("banned")),
                "announcements": len([a for a in anns if a.get("status") == "published"]),
                "claims": len(claims),
                "claimsByStatus": c_status,
                "days": days,
            })

        if path == "/api/admin/announcements":
            if not self._need_admin():
                return
            with LOCK:
                arr = load_announcements()
            arr.sort(key=lambda x: (not x.get("pinned"), -(x.get("updatedAt") or 0)))
            return self._json(arr)

        if path == "/api/admin/items":
            if not self._need_admin():
                return
            with LOCK:
                items = load_items()
            for x in items:
                _p = (x.get("contact") or {}).get("phone") or ""
                _c = phone_check(_p)
                x["phoneStatus"] = _c["status"]
                x["phoneType"] = _c["type"]
                x["phoneReason"] = _c["reason"]
                if x.get("photo"):
                    x["photoUrl"] = "/api/photo/" + str(x.get("id"))
                    x["photo"] = None
            items.sort(key=lambda x: x.get("createdAt") or 0, reverse=True)
            return self._json(items)

        if path == "/api/admin/stats":
            if not self._need_admin():
                return
            with LOCK:
                items = load_items()
            counts = {}
            for x in items:
                counts[x.get("status", "?")] = counts.get(x.get("status", "?"), 0) + 1
            return self._json({"total": len(items), "byStatus": counts})

        if path == "/api/admin/ai/config":
            if not self._need_admin():
                return
            cfg = load_ai_config()
            return self._json({
                "enabled": bool(cfg.get("enabled")),
                "base_url": cfg.get("base_url") or "",
                "model": cfg.get("model") or "",
                "has_key": bool(cfg.get("api_key")),
                "auto_review": bool(cfg.get("auto_review")),
                "auto_approve": bool(cfg.get("auto_approve")),
                "approve_threshold": int(cfg.get("approve_threshold") or 0),
                "auto_reject": bool(cfg.get("auto_reject")),
                "reject_threshold": int(cfg.get("reject_threshold") or 0),
            })

        # 静态文件
        rel = path.lstrip("/")
        target = os.path.abspath(os.path.join(BASE_DIR, rel))
        if rel and target.startswith(BASE_DIR + os.sep) and os.path.isfile(target):
            return self._serve_path(target)
        if path == "/favicon.ico":
            return self._send(204)
        return self._send(404, "not found", "text/plain; charset=utf-8")

    def do_POST(self):
        path = unquote(urlparse(self.path).path)

        if path == "/api/admin/deploy":
            if not self._need_admin():
                return
            try:
                subprocess.run(["git", "-C", "/opt/lostfound", "fetch", "origin", "main", "--quiet"], timeout=25)
                local = subprocess.check_output(["git", "-C", "/opt/lostfound", "rev-parse", "HEAD"]).decode().strip()
                remote = subprocess.check_output(["git", "-C", "/opt/lostfound", "rev-parse", "origin/main"]).decode().strip()
                if local == remote:
                    return self._json({"ok": True, "hasUpdate": False, "msg": "暂无要更新的代码"})
                script = "/tmp/sg_deploy.sh"
                with open(script, "w", encoding="utf-8") as f:
                    f.write("#!/bin/bash\nsleep 2\ncd /opt/lostfound\n"
                            "{\n"
                            "echo \"[$(date '+%F %T')] deploy start\"\n"
                            "cd /opt/lostfound\n"
                            "cp tags.json tags.json.bak.$(date +%Y%m%d%H%M%S) 2>/dev/null || true\n"
                            "cp items.json items.json.bak.$(date +%Y%m%d%H%M%S) 2>/dev/null || true\n"
                            "git fetch origin main\n"
                            "git reset --hard origin/main\n"
                            "git log --oneline -1\n"
                            "systemctl restart lostfound\n"
                            "echo \"[$(date '+%F %T')] done\"\n"
                            "} > /opt/lostfound/deploy.log 2>&1\n")
                os.chmod(script, 0o755)
                subprocess.Popen(
                    ["systemd-run", "--collect", "--unit=sg-deploy-%d" % int(time.time()),
                     "--on-active=3", "/bin/bash", script],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                return self._json({"error": str(e)[:120]}, 500)
            return self._json({"ok": True, "hasUpdate": True,
                               "msg": "发现新版本，正在更新，约 10 秒后自动刷新"})

        if path.startswith("/api/admin/items/") and path.endswith("/type"):
            if not self._need_admin():
                return
            item_id = path[len("/api/admin/items/"):-len("/type")]
            body = self._read_body()
            new_type = body.get("type")
            if new_type not in ("lost", "found"):
                return self._json({"error": "type must be lost/found"}, 400)
            with LOCK:
                items = load_items()
                it = next((x for x in items if x.get("id") == item_id), None)
                if not it:
                    return self._json({"error": "not found"}, 404)
                it["type"] = new_type
                it["typeAutoFixed"] = True
                it["updatedAt"] = now_ms()
                save_items(items)
            return self._json({"ok": True, "type": new_type})

        if path.startswith("/api/admin/items/") and path.endswith("/phone-approve"):
            if not self._need_admin():
                return
            item_id = path[len("/api/admin/items/"):-len("/phone-approve")]
            with LOCK:
                items = load_items()
                it = next((x for x in items if x.get("id") == item_id), None)
                if not it:
                    return self._json({"error": "not found"}, 404)
                _ph = re.sub(r"\D", "", str((it.get("contact") or {}).get("phone") or ""))
                if re.match(r"^1[3-9]\d{9}$", _ph):
                    _arr = load_special_numbers()
                    if _ph not in _arr:
                        _arr.append(_ph)
                        save_special_numbers(_arr)
                it["phoneStatus"] = "green"
                it["phoneVerified"] = True
                it["phoneReviewRequested"] = False
                it["updatedAt"] = now_ms()
                save_items(items)
            return self._json({"ok": True})

        if path == "/api/admin/special-numbers":
            if not self._need_admin():
                return
            body = self._read_body()
            phone = re.sub(r"\D", "", str(body.get("phone") or ""))
            if not re.match(r"^1[3-9]\d{9}$", phone):
                return self._json({"error": "请输入 11 位手机号"}, 400)
            with LOCK:
                arr = load_special_numbers()
                if body.get("remove"):
                    arr = [x for x in arr if x != phone]
                elif phone not in arr:
                    arr.append(phone)
                save_special_numbers(arr)
            return self._json({"ok": True, "numbers": arr})

        if path == "/api/admin/recheck-images":
            if not self._need_admin():
                return
            body = self._read_body()
            try:
                limit = max(1, min(5, int(body.get("limit") or 3)))
            except Exception:
                limit = 3
            with LOCK:
                items = load_items()
            checked = 0
            rejected = 0
            for it in items:
                if (it.get("status") in ("approved", "claimed") and it.get("photo")
                        and not it.get("visionDesc") and checked < limit):
                    try:
                        raw = str(it["photo"]).split(",")[-1]
                        v = vision_moderate(raw, "image/jpeg")
                        if not v:
                            a = vision_analyze(raw, "image/jpeg")
                            if a.get("ok"):
                                v = "；".join([str(x) for x in (a.get("category"), a.get("color"),
                                                               a.get("features"), a.get("desc")) if x])[:300]
                        it["visionDesc"] = v or ""
                        cfg = load_ai_config()
                        ai = review_item(it)
                        it = apply_ai_decision(it, ai, cfg)
                        checked += 1
                        if it.get("status") == "rejected":
                            rejected += 1
                    except Exception:
                        pass
            with LOCK:
                save_items(items)
            return self._json({"ok": True, "checked": checked, "rejected": rejected})

        if path == "/api/admin/import":
            if not self._need_admin():
                return
            body = self._read_body()
            result = {}
            with LOCK:
                if isinstance(body.get("items"), list):
                    save_items(body["items"])
                    result["items"] = len(body["items"])
                if isinstance(body.get("claims"), list):
                    save_claims(body["claims"])
                    result["claims"] = len(body["claims"])
                if isinstance(body.get("notices"), list):
                    save_notices(body["notices"])
                    result["notices"] = len(body["notices"])
                if isinstance(body.get("accounts"), list):
                    save_accounts(body["accounts"])
                    result["accounts"] = len(body["accounts"])
                if isinstance(body.get("announcements"), list):
                    save_announcements(body["announcements"])
                    result["announcements"] = len(body["announcements"])
            return self._json({"ok": True, "imported": result})


        if path == "/api/phone/check":
            body = self._read_body()
            return self._json(phone_check(body.get("phone")))

        if path.startswith("/api/admin/accounts/") and path.endswith("/ban"):
            if not self._need_admin():
                return
            aid = path[len("/api/admin/accounts/"):-len("/ban")]
            body = self._read_body()
            banned = bool(body.get("banned"))
            with LOCK:
                accs = load_accounts()
                acc = next((a for a in accs if a.get("id") == aid), None)
                if not acc:
                    return self._json({"error": "not found"}, 404)
                acc["banned"] = banned
                save_accounts(accs)
                items = load_items()
                changed = 0
                for x in items:
                    if x.get("ownerToken") == aid:
                        x["status"] = "hidden" if banned else "approved"
                        x["updatedAt"] = now_ms()
                        changed += 1
                if changed:
                    save_items(items)
            return self._json({"ok": True, "banned": banned, "items": changed})

        if path == "/api/admin/announcements":
            if not self._need_admin():
                return
            body = self._read_body()
            title = str(body.get("title") or "").strip()[:60]
            text = str(body.get("body") or "").strip()[:2000]
            if len(title) < 2 or len(text) < 5:
                return self._json({"error": "标题或正文太短"}, 400)
            _ok, _why = moderate_text(title + " " + text, "公告")
            if not _ok:
                return self._json({"error": "公告未通过审核：" + _why}, 400)
            now = now_ms()
            item = {"id": "a_" + uuid.uuid4().hex[:10], "title": title, "body": text,
                    "pinned": bool(body.get("pinned")), "status": "draft",
                    "createdAt": now, "updatedAt": now, "publishedAt": 0}
            if body.get("publish"):
                item["status"] = "published"
                item["publishedAt"] = now
            with LOCK:
                arr = load_announcements()
                arr.append(item)
                save_announcements(arr)
            return self._json(item, 201)


        if path == "/api/format":
            body = self._read_body()
            title = str(body.get("title") or "")[:40]
            desc = str(body.get("desc") or "")[:400]
            if len(desc) < 5:
                return self._json({"error": "描述太短，不需要整理"}, 400)
            out = format_item(title, desc)
            out["originalLen"] = len(desc)
            out["newLen"] = len(out["desc"])
            return self._json(out)


        if path == "/api/tags":
            owner = self._owner()
            if not owner:
                return self._json({"error": "请先登录后再申请拾光码"}, 401)
            body = self._read_body()
            item_name = str(body.get("itemName") or "我的物品").strip()[:30]
            phone = str(body.get("phone") or "").strip()[:20]
            mode = "phone" if body.get("mode") == "phone" else "notify"
            note = str(body.get("note") or "").strip()[:80]
            if mode == "phone" and not phone:
                return self._json({"error": "选择展示电话时，需要填写手机号"}, 400)
            _ok, _why = moderate_tag(item_name + " " + note)
            if not _ok:
                return self._json({"error": "内容未通过审核：" + _why}, 400)
            with LOCK:
                tags = load_tags()
                tag = next((x for x in tags if x.get("owner") == owner and x.get("active", True)), None)
                if tag:
                    tag.update({"itemName": item_name, "phone": phone,
                                "mode": mode, "note": note, "updatedAt": now_ms()})
                else:
                    code = "SG" + uuid.uuid4().hex[:6].upper()
                    while any(x.get("code") == code for x in tags):
                        code = "SG" + uuid.uuid4().hex[:6].upper()
                    tag = {
                        "code": code, "owner": owner, "itemName": item_name,
                        "phone": phone, "mode": mode, "note": note,
                        "createdAt": now_ms(), "notifyCount": 0,
                    }
                    tags.append(tag)
                save_tags(tags)
            host = self.headers.get("Host") or "127.0.0.1:8000"
            scheme = "https" if self.headers.get("X-Forwarded-Proto") == "https" else "http"
            out = _tag_public(tag, scheme + "://" + host, with_qr=True)
            out["reused"] = True
            return self._json(out)

        if path == "/api/tags/mine/delete":
            owner = self._owner()
            if not owner:
                return self._json({"error": "请先登录"}, 401)
            with LOCK:
                tags = load_tags()
                tag = next((x for x in tags if x.get("owner") == owner and x.get("active", True)), None)
                if not tag:
                    return self._json({"error": "没有可注销的拾光码"}, 404)
                tag["active"] = False
                tag["deactivatedAt"] = now_ms()
                save_tags(tags)
            return self._json({"ok": True})

        if path.startswith("/api/tags/") and path.endswith("/notify"):
            code = path[len("/api/tags/"):-len("/notify")].strip("/")
            body = self._read_body()
            message = str(body.get("message") or "").strip()[:160]
            contact = str(body.get("contact") or "").strip()[:40]
            found_item = str(body.get("itemName") or "").strip()[:40]
            with LOCK:
                tags = load_tags()
                tag = next((x for x in tags if x.get("code") == code), None)
            if not tag:
                return self._json({"error": "拾光码不存在"}, 404)
            if not tag.get("active", True):
                return self._json({"error": "此码已注销，感谢您的一份好意"}, 410)
            _ok, _why = moderate_text(found_item + " " + message + " " + contact, "扫码上报")
            if not _ok:
                return self._json({"error": "内容未通过审核：" + _why}, 400)
            with LOCK:
                if not tag.get("active", True):
                    return self._json({"error": "此码已注销，感谢您的一份好意"}, 410)
                tag["notifyCount"] = int(tag.get("notifyCount") or 0) + 1
                save_tags(tags)
                scan_id = ""
                # 捡到上报同步生成一条招领信息，进入正常失物招领流
                if found_item or message:
                    items = load_items()
                    scan_item = {
                        "id": "p_" + uuid.uuid4().hex[:12],
                        "type": "found",
                        "cat": "other",
                        "title": ("扫码上报：" + (found_item or "捡到物品"))[:60],
                        "desc": (message or "扫码上报捡到物品")[:400],
                        "place": "扫码上报 · " + (tag.get("itemName") or "拾光码"),
                        "eventTime": "",
                        "secret": "",
                        "photo": None,
                        "contact": {"phone": contact[:20]} if contact else {},
                        "ownerToken": self._owner() or ("scan_" + code),
                        "source": "tag_scan",
                        "tagCode": code,
                        "tagOwner": tag.get("owner"),
                        "status": "approved",
                        "autoApproved": True,
                        "reviewedBy": "AI",
                        "createdAt": now_ms(),
                        "updatedAt": now_ms(),
                    }
                    items.append(scan_item)
                    save_items(items)
                    scan_id = scan_item["id"]
                notices = load_notices()
                text = "有人扫了你的拾光码"
                if found_item:
                    text += "，捡到：%s" % found_item
                text += "：%s" % (message or "我捡到了，请联系我")
                add_notice(notices, tag.get("owner"), "pickup", text, scan_id, "")
                save_notices(notices)
            return self._json({"ok": True})

        if path == "/api/agent/radar":
            body = self._read_body()
            item_id = str(body.get("itemId") or "")
            with LOCK:
                items = load_items()
            item = next((x for x in items if x.get("id") == item_id), None)
            if not item:
                item = _probe_item(body)
            if not item:
                return self._json({"error": "not found"}, 404)
            return self._json(agent_radar(item, items))

        if path == "/api/agent/detective":
            body = self._read_body()
            item_id = str(body.get("itemId") or "")
            route = str(body.get("route") or "")
            carry = str(body.get("carry") or "")
            last_seen = str(body.get("lastSeen") or "")
            with LOCK:
                items = load_items()
            item = next((x for x in items if x.get("id") == item_id), None)
            if not item:
                item = _probe_item(body)
            if not item:
                return self._json({"error": "not found"}, 404)
            return self._json(agent_detective_route(item, items, route, carry, last_seen))

        if path == "/api/agent/review":
            owner = self._owner()
            body = self._read_body()
            item_id = str(body.get("itemId") or "")
            claim_id = str(body.get("claimId") or "")
            with LOCK:
                items = load_items()
                claims = load_claims()
            item = next((x for x in items if x.get("id") == item_id), None)
            claim = next((c for c in claims if c.get("id") == claim_id), None)
            if not item or not claim:
                return self._json({"error": "not found"}, 404)
            if item.get("ownerToken") != owner:
                return self._json({"error": "只有发布者能核验"}, 403)
            return self._json(agent_review(item, claim))

        if path == "/api/agent/review/stream":
            owner = self._owner()
            body = self._read_body()
            item_id = str(body.get("itemId") or "")
            claim_id = str(body.get("claimId") or "")
            with LOCK:
                items = load_items()
                claims = load_claims()
            item = next((x for x in items if x.get("id") == item_id), None)
            claim = next((c for c in claims if c.get("id") == claim_id), None)
            if not item or not claim:
                return self._json({"error": "not found"}, 404)
            if item.get("ownerToken") != owner:
                return self._json({"error": "只有发布者能核验"}, 403)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()

            def sse(event, data):
                chunk = "event: %s\ndata: %s\n\n" % (event, json.dumps(data, ensure_ascii=False))
                self.wfile.write(chunk.encode("utf-8"))
                self.wfile.flush()

            result = agent_review(item, claim, on_step=lambda st: sse("step", {
                "tool": st["tool"], "finding": (st.get("result") or {})}))
            reason = result.get("reason") or ""
            for i in range(0, len(reason), 10):
                sse("delta", {"text": reason[i:i + 10]})
            sse("done", result)
            self.close_connection = True
            return

        if path == "/api/ask/stream":
            body = self._read_body()
            q = str(body.get("question") or "").strip()
            if len(q) < 2:
                return self._json({"error": "请输入问题"}, 400)
            result = ask_kb(q)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()

            def sse(event, data):
                self.wfile.write(("event: %s\ndata: %s\n\n" % (
                    event, json.dumps(data, ensure_ascii=False))).encode("utf-8"))
                self.wfile.flush()

            text = result.get("answer") or ""
            for i in range(0, len(text), 12):
                sse("delta", {"text": text[i:i + 12]})
                time.sleep(0.015)
            sse("done", result)
            self.close_connection = True
            return

        if path == "/api/ask":
            body = self._read_body()
            q = str(body.get("question") or "").strip()
            if len(q) < 2:
                return self._json({"error": "请输入问题"}, 400)
            return self._json(ask_kb(q))

        if path == "/api/vision/analyze":
            body = self._read_body()
            img = str(body.get("image") or "")
            mime = str(body.get("mime") or "image/jpeg")
            if len(img) < 20:
                return self._json({"error": "缺少图片"}, 400)
            return self._json(vision_analyze(img, mime))


        if path == "/api/account/login":
            body = self._read_body()
            phone = re.sub(r"\D", "", str(body.get("phone") or ""))
            pwd = str(body.get("password") or "")
            _chk = phone_check(phone)
            if _chk["status"] == "red" or _chk["type"] != "mobile":
                return self._json({"error": "请用 11 位手机号注册/登录"}, 400)
            if len(phone) < 5:
                return self._json({"error": "请输入手机号"}, 400)
            if len(pwd) < 4:
                return self._json({"error": "密码至少 4 位"}, 400)
            with LOCK:
                accs = load_accounts()
                acc = next((a for a in accs if a.get("phone") == phone), None)
                created = False
                if not acc:
                    salt = uuid.uuid4().hex[:16]
                    acc = {"id": "acc_" + uuid.uuid4().hex[:10], "phone": phone,
                           "salt": salt,
                           "hash": hashlib.pbkdf2_hmac("sha256", pwd.encode("utf-8"),
                                                       salt.encode("utf-8"), 120000).hex(),
                           "createdAt": now_ms()}
                    accs.append(acc)
                    save_accounts(accs)
                    created = True
                else:
                    if acc.get("banned"):
                        return self._json({"error": "账号已被停用，请联系管理员"}, 403)
                    if hashlib.pbkdf2_hmac("sha256", pwd.encode("utf-8"),
                                           (acc.get("salt") or "").encode("utf-8"), 120000).hex() != acc.get("hash"):
                        return self._json({"error": "密码不对"}, 401)
                acc["lastLoginAt"] = now_ms()
                save_accounts(accs)
            adopted = 0
            guest_owner = self._owner()
            with LOCK:
                items = load_items()
                for x in items:
                    _ph = re.sub(r"\D", "", str((x.get("contact") or {}).get("phone") or ""))
                    _owned_by_device = (guest_owner and not guest_owner.startswith("acc_")
                                        and x.get("ownerToken") == guest_owner)
                    if ((_ph == phone or _owned_by_device) and x.get("ownerToken") != acc["id"]):
                        x["ownerToken"] = acc["id"]
                        x["ownerId"] = acc["id"]
                        x["updatedAt"] = now_ms()
                        adopted += 1
                if adopted:
                    save_items(items)
                # 拾光码也跟随账号，避免先生成码再登录就丢失
                tags = load_tags()
                tag_changed = False
                for t in tags:
                    _tph = re.sub(r"\D", "", str(t.get("phone") or ""))
                    _owned_by_device = (guest_owner and not guest_owner.startswith("acc_")
                                        and t.get("owner") == guest_owner)
                    if ((_tph == phone or _owned_by_device) and t.get("owner") != acc["id"]):
                        t["owner"] = acc["id"]
                        t["updatedAt"] = now_ms()
                        tag_changed = True
                if tag_changed:
                    save_tags(tags)
            return self._json({"ok": True, "accountId": acc["id"], "phone": phone,
                               "created": created, "adopted": adopted})

        if path == "/api/recover":
            owner = self._owner()
            if not owner:
                return self._json({"error": "缺少设备标识"}, 400)
            body = self._read_body()
            phone = re.sub(r"\D", "", str(body.get("phone") or ""))
            if len(phone) < 5:
                return self._json({"error": "请输入发布时留的手机号"}, 400)
            confirm = bool(body.get("confirm"))
            with LOCK:
                items = load_items()
                hits = [x for x in items
                        if re.sub(r"\D", "", str((x.get("contact") or {}).get("phone") or "")) == phone]
            if not hits:
                return self._json({"ok": True, "count": 0, "titles": []})
            if not confirm:
                return self._json({"ok": True, "count": len(hits),
                                   "titles": [x.get("title") or "" for x in hits][:10]})
            with LOCK:
                items = load_items()
                n = 0
                for x in items:
                    if (re.sub(r"\D", "", str((x.get("contact") or {}).get("phone") or "")) == phone
                            and x.get("ownerToken") != owner):
                        x["ownerToken"] = owner
                        x["ownerId"] = owner
                        x["updatedAt"] = now_ms()
                        n += 1
                save_items(items)
            return self._json({"ok": True, "count": n})


        if path == "/api/login":
            body = self._read_body()
            pwd = str(body.get("password") or "")
            if pwd and pwd == ensure_admin_password():
                tok = uuid.uuid4().hex
                TOKENS[tok] = time.time() + TOKEN_TTL
                return self._json({"token": tok, "ttl": TOKEN_TTL})
            time.sleep(0.8)
            return self._json({"error": "密码不对"}, 401)

        if path == "/api/precheck":
            owner = self._owner()
            if not owner:
                return self._json({"error": "缺少设备标识"}, 400)
            body = self._read_body()
            item = self._clean(body)
            item["type"] = body.get("type") if body.get("type") in ("lost", "found") else "lost"
            if not item.get("title"):
                return self._json({"error": "title required"}, 400)
            ai = review_item(item)
            suggestion = ""
            if (item["type"] in ("lost", "found") and ai.get("guessType")
                    and ai["guessType"] != item["type"]):
                suggestion = ai["guessType"]
            cid = "k_" + uuid.uuid4().hex[:10]
            CHECK_CACHE[cid] = {"owner": owner, "ai": ai, "at": time.time(), "type": item["type"]}
            # 清掉过期的
            for k in [k for k, v in CHECK_CACHE.items() if time.time() - v.get("at", 0) > 900]:
                CHECK_CACHE.pop(k, None)
            return self._json({"checkId": cid, "ai": ai, "suggestion": suggestion,
                               "type": item["type"]})

        if path.startswith("/api/items/") and path.endswith("/claims"):
            owner = self._owner()
            if not owner:
                return self._json({"error": "缺少设备标识"}, 400)
            item_id = path[len("/api/items/"):-len("/claims")]
            body = self._read_body()
            message = str(body.get("message") or "").strip()[:200]
            contact = str(body.get("contact") or "").strip()[:30]
            _ok, _why = moderate_text(message + " " + contact, "认领申请", allow_help=True)
            if not _ok:
                return self._json({"error": "内容未通过审核：" + _why}, 400)
            _chk = phone_check(contact)
            if contact and _chk["status"] == "red":
                return self._json({"error": "电话号码不正确：" + _chk["reason"]}, 400)
            if _chk.get("normalized"):
                contact = _chk["normalized"]
            if len(message) < 2:
                return self._json({"error": "请说明一下物品的独有特征"}, 400)
            with LOCK:
                items = load_items()
                target = next((x for x in items if x.get("id") == item_id), None)
                if not target:
                    return self._json({"error": "not found"}, 404)
                if target.get("ownerToken") == owner:
                    return self._json({"error": "这是你自己发布的"}, 400)
                if target.get("status") == "claimed":
                    return self._json({"error": "这个物品已经被别人认领了"}, 400)
                if target.get("status") != "approved":
                    return self._json({"error": "这条已经不在可认领状态"}, 400)
                claims = load_claims()
                if any(c.get("itemId") == item_id and c.get("from") == owner for c in claims):
                    return self._json({"error": "你已经申请过了"}, 400)
                # 三个方向：
                #  - 招领帖(found)：申请人=失主，填「只有失主知道的特征」
                #  - 寻物帖(lost)：申请人=捡到的人，填「在哪捡到的」
                #  - 爱心求助(help)：申请人=愿意帮忙的人
                if target.get("type") == "help":
                    kind = "help"
                elif target.get("type") == "lost":
                    kind = "found"
                else:
                    kind = "claim"
                claim = {
                    "id": "c_" + uuid.uuid4().hex[:10],
                    "itemId": item_id,
                    "from": owner,
                    "kind": kind,
                    "message": message,
                    "history": [{"message": message, "at": now_ms()}],
                    "contact": contact,
                    "status": "pending",
                    "createdAt": now_ms(),
                    "updatedAt": now_ms(),
                }
                try:
                    _chk0 = claim_ai_check(target, claim)
                    if _chk0:
                        claim["aiCheck"] = _chk0
                except Exception:
                    pass
                claims.append(claim)
                save_claims(claims)
                notices = load_notices()
                if kind == "found":
                    text = "有人捡到了你丢失的《%s》，快去核对" % (target.get("title") or "")
                elif kind == "help":
                    text = "有人愿意帮忙《%s》，去看看吧" % (target.get("title") or "")
                else:
                    text = "有人申请认领你捡到的《%s》" % (target.get("title") or "")
                add_notice(notices, target.get("ownerToken"), "claim", text, item_id, claim["id"])
                save_notices(notices)
            return self._json({"ok": True, "id": claim["id"]})

        if path.startswith("/api/claims/") and path.endswith("/supplement"):
            owner = self._owner()
            claim_id = path[len("/api/claims/"):-len("/supplement")]
            body = self._read_body()
            extra = str(body.get("message") or "").strip()[:200]
            if len(extra) < 2:
                return self._json({"error": "请写一点补充说明"}, 400)
            _ok, _why = moderate_text(extra, "认领补充", allow_help=True)
            if not _ok:
                return self._json({"error": "内容未通过审核：" + _why}, 400)
            with LOCK:
                claims = load_claims()
                items = load_items()
                claim = next((c for c in claims if c.get("id") == claim_id), None)
                if not claim:
                    return self._json({"error": "not found"}, 404)
                if claim.get("from") != owner:
                    return self._json({"error": "只有申请人能补充"}, 403)
                if claim.get("status") not in ("pending", "need_more", "rejected"):
                    return self._json({"error": "当前状态不能补充"}, 400)
                if claim.get("status") == "rejected":
                    # 被拒后重新申请：用新写的内容整体替换，而不是追加
                    claim["message"] = extra[:400]
                    claim["history"] = [{"message": extra, "at": now_ms()}]
                else:
                    claim["message"] = ((claim.get("message") or "") + "\n补充：" + extra)[:400]
                    hist = claim.get("history") or []
                    hist.append({"message": extra, "at": now_ms()})
                    claim["history"] = hist[-10:]
                claim["status"] = "pending"
                claim["updatedAt"] = now_ms()
                try:
                    _it = next((x for x in items if x.get("id") == claim.get("itemId")), None)
                    if _it:
                        _chk = claim_ai_check(_it, claim)
                        if _chk:
                            claim["aiCheck"] = _chk
                except Exception:
                    pass
                save_claims(claims)
                item = next((x for x in items if x.get("id") == claim.get("itemId")), None)
                notices = load_notices()
                if item:
                    add_notice(notices, item.get("ownerToken"), "claim",
                               "有人补充了《%s》的说明，请再核对一次" % (item.get("title") or ""),
                               item.get("id"), claim.get("id"))
                save_notices(notices)
            return self._json({"ok": True})

        if path.startswith("/api/claims/") and path.endswith("/complete"):
            owner = self._owner()
            body = self._read_body()
            claim_id = path[len("/api/claims/"):-len("/complete")]
            with LOCK:
                claims = load_claims()
                items = load_items()
                claim = next((c for c in claims if c.get("id") == claim_id), None)
                if not claim:
                    return self._json({"error": "not found"}, 404)
                item = next((x for x in items if x.get("id") == claim.get("itemId")), None)
                if not item:
                    return self._json({"error": "not found"}, 404)
                code = str((body or {}).get("code") or "").strip()
                if claim.get("returnCode"):
                    holder = claim.get("holder")
                    if holder and holder != owner:
                        return self._json({"error": "只有持有物品的一方才能确认归还"}, 403)
                    if code != claim.get("returnCode"):
                        return self._json({"error": "取件码不对，让对方再看一眼"}, 400)
                elif item.get("ownerToken") != owner:
                    return self._json({"error": "只有发布者能确认完成"}, 403)
                claim["status"] = "completed"
                claim["updatedAt"] = now_ms()
                claim["completedAt"] = now_ms()
                item["status"] = "closed"
                item["closedAt"] = now_ms()
                item["updatedAt"] = now_ms()
                save_claims(claims)
                save_items(items)
                notices = load_notices()
                add_notice(notices, claim.get("from"), "done",
                           "《%s》已标记完成归还，谢谢你" % (item.get("title") or ""), item.get("id"))
                save_notices(notices)
            return self._json({"ok": True})

        if path == "/api/notices/read":
            owner = self._owner()
            with LOCK:
                notices = load_notices()
                for n in notices:
                    if n.get("owner") == owner:
                        n["read"] = True
                save_notices(notices)
            return self._json({"ok": True})

        if path.startswith("/api/items/") and path.endswith("/report"):
            owner = self._owner()
            if not owner:
                return self._json({"error": "缺少设备标识"}, 400)
            item_id = path[len("/api/items/"):-len("/report")]
            need_recheck = False
            with LOCK:
                items = load_items()
                target = next((x for x in items if x.get("id") == item_id), None)
                if not target:
                    return self._json({"error": "not found"}, 404)
                reports = target.get("reports") or []
                if owner not in reports:
                    reports.append(owner)
                target["reports"] = reports
                target["reportCount"] = len(reports)
                need_recheck = len(reports) >= 3 and target.get("status") in PUBLIC_STATUS
                if need_recheck:
                    target["status"] = "hidden"
                    target["hiddenReason"] = "多人举报，正在复核"
                save_items(items)
            if need_recheck:
                ai = ai_review(target, use_llm=True, timeout=12)
                approved = ai.get("source") == "llm" and ai.get("decision") == "approve"
                with LOCK:
                    items = load_items()
                    for x in items:
                        if x.get("id") == item_id:
                            x["ai"] = ai
                            if approved:
                                x["status"] = "approved"
                                x["hiddenReason"] = ""
                            else:
                                x["status"] = "rejected"
                                x["rejectReason"] = "多人举报并经 AI 复核：" + (ai.get("reason") or "")
                            break
                    save_items(items)
            return self._json({"ok": True, "reports": len(reports)})

        if path == "/api/items":
            owner = self._owner()
            if not owner:
                return self._json({"error": "缺少设备标识，请刷新页面"}, 400)
            body = self._read_body()
            if not isinstance(body, dict) or not body.get("title"):
                return self._json({"error": "title required"}, 400)
            ok_rate, msg_rate = rate_allow(owner)
            if not ok_rate:
                return self._json({"error": msg_rate}, 429)
            _t = str(body.get("title") or "").strip()
            _d = str(body.get("desc") or "").strip()
            with LOCK:
                _recent = [x for x in load_items()
                           if x.get("ownerToken") == owner
                           and x.get("title") == _t and x.get("desc") == _d
                           and (now_ms() - (x.get("createdAt") or 0)) < 600000]
            if _recent:
                return self._json({"error": "同样的内容刚发过，别重复提交"}, 409)
            item = self._clean(body)
            _rule_type = detect_lost_found((item.get("title") or "") + " " + (item.get("desc") or ""))
            if _rule_type and _rule_type != item.get("type"):
                item["type"] = _rule_type
                item["typeAutoFixed"] = True
            # 强制模板化：客户端没带摘要时用规则整理兜底，保证展示一致
            if not item.get("summary"):
                _fmt = _format_fallback(item.get("title") or "", item.get("desc") or "", item.get("place") or "")
                item["summary"] = _fmt["summary"]
                if not item.get("fields"):
                    item["fields"] = _fmt["fields"]
            _ph = (item.get("contact") or {}).get("phone") or ""
            if _ph:
                _chk = phone_check(_ph)
                if _chk["status"] == "red":
                    return self._json({"error": "电话号码不正确：" + _chk["reason"]}, 400)
                if (_chk["status"] == "yellow" and not body.get("phoneConfirmed")
                        and not body.get("phoneReviewRequested")
                        and item.get("type") != "help"):
                    return self._json({"error": "电话号码需要确认：" + _chk["reason"],
                                       "needConfirm": True}, 400)
                if _chk["status"] == "yellow" and body.get("phoneReviewRequested"):
                    item["phoneReviewRequested"] = True
                item["contact"]["phone"] = _chk["normalized"] or _ph
                item["phoneStatus"] = _chk["status"]
                item["phoneType"] = _chk["type"]
            item["id"] = "p_" + uuid.uuid4().hex[:12]
            item["status"] = "pending"
            item["rejectReason"] = ""
            item["ownerToken"] = owner
            item["ownerId"] = owner
            item["createdAt"] = now_ms()
            item["updatedAt"] = item["createdAt"]
            cfg = load_ai_config()
            try:
                approve_at = int(cfg.get("approve_threshold") or 0)
            except Exception:
                approve_at = 20
            try:
                reject_at = int(cfg.get("reject_threshold") or 80)
            except Exception:
                reject_at = 80
            # 预检命中：直接判定，用户马上拿到结果
            vision_ok = False
            if item.get("photo") and cfg.get("enabled"):
                try:
                    _raw = str(item["photo"]).split(",")[-1]
                    _vtext = vision_moderate(_raw, "image/jpeg")
                    if _vtext:
                        item["visionDesc"] = _vtext
                        vision_ok = True
                    else:
                        _v = vision_analyze(_raw, "image/jpeg")
                        if _v.get("ok") and (_v.get("features") or _v.get("desc")):
                            item["visionDesc"] = "；".join(
                                [str(x) for x in (_v.get("category"), _v.get("color"),
                                                  _v.get("features"), _v.get("desc")) if x])[:300]
                            vision_ok = True
                except Exception:
                    pass
            check_id = body.get("checkId")
            cached = CHECK_CACHE.get(check_id) if (check_id and not item.get("visionDesc")) else None
            if cached and cached.get("owner") == owner and time.time() - cached.get("at", 0) < 600:
                ai = cached.get("ai") or review_item(item)
                CHECK_CACHE.pop(check_id, None)
                item = apply_ai_decision(item, ai, cfg)
                with LOCK:
                    items_all = load_items()
                    items_all.append(item)
                    save_items(items_all)
                try:
                    run_matching()
                except Exception:
                    pass
                return self._json(item, 201)
            # 没预检：根据当前压力决定排队还是立即审
            note_arrival()
            if should_queue():
                with LOCK:
                    items_all = load_items()
                    items_all.append(item)
                    save_items(items_all)
                queue_add(item["id"])
                pos = queue_position(item["id"])
                return self._json({"id": item["id"], "status": "pending", "queued": True,
                                   "position": pos, "eta": pos * 2}, 202)
            try:
                ai = guarded_review(item)
                item = apply_ai_decision(item, ai, cfg)
                if item.get("photo") and not vision_ok and item.get("status") == "approved":
                    item["status"] = "rejected"
                    item["autoRejected"] = False
                    item["reviewedBy"] = "system"
                    item["reviewedAt"] = now_ms()
                    item["rejectReason"] = "图片审核未完成，请换一张更清晰的图重新提交一次"
            except Exception:
                ai = {"source": "fallback", "decision": "review", "score": 50,
                      "reason": "审核排队中，请稍后查看"}
                item["ai"] = ai
                item["status"] = "pending"
            with LOCK:
                items_all = load_items()
                items_all.append(item)
                save_items(items_all)
            try:
                run_matching()
            except Exception:
                pass
            return self._json(item, 201)

        if path == "/api/admin/reset":
            if not self._need_admin():
                return
            with LOCK:
                items = seed_items()
                save_items(items)
                save_claims([])
                save_notices([])
            return self._json({"ok": True, "items": len(items)})

        if path == "/api/admin/ai/test":
            if not self._need_admin():
                return
            body = self._read_body()
            cfg = load_ai_config()
            for k in ("base_url", "api_key", "model"):
                if body.get(k):
                    cfg[k] = body[k]
            return self._json(ai_test(cfg))

        if path == "/api/admin/ai/config":
            if not self._need_admin():
                return
            body = self._read_body()
            cfg = load_ai_config()
            for k in ("enabled", "base_url", "api_key", "model", "auto_review",
                      "auto_approve", "approve_threshold", "auto_reject", "reject_threshold"):
                if k in body:
                    cfg[k] = body[k]
            try:
                cfg["approve_threshold"] = max(0, min(100, int(cfg.get("approve_threshold") or 0)))
            except Exception:
                cfg["approve_threshold"] = 20
            try:
                cfg["reject_threshold"] = max(0, min(100, int(cfg.get("reject_threshold") or 80)))
            except Exception:
                cfg["reject_threshold"] = 80
            cfg = save_ai_config(cfg)
            return self._json({
                "enabled": bool(cfg.get("enabled")),
                "base_url": cfg.get("base_url") or "",
                "model": cfg.get("model") or "",
                "has_key": bool(cfg.get("api_key")),
                "auto_approve": bool(cfg.get("auto_approve")),
                "approve_threshold": int(cfg.get("approve_threshold") or 0),
            })

        if path.startswith("/api/admin/ai/review/"):
            if not self._need_admin():
                return
            item_id = path[len("/api/admin/ai/review/"):]
            with LOCK:
                items = load_items()
            target = next((x for x in items if x.get("id") == item_id), None)
            if not target:
                return self._json({"error": "not found"}, 404)
            result = ai_review(target, use_llm=True)
            with LOCK:
                items = load_items()
                for x in items:
                    if x.get("id") == item_id:
                        x["ai"] = result
                        break
                save_items(items)
            return self._json(result)

        if path == "/api/admin/ai/review-all":
            if not self._need_admin():
                return
            cfg = load_ai_config()
            use_llm = bool(cfg.get("enabled") and cfg.get("api_key") and cfg.get("base_url"))
            with LOCK:
                items = load_items()
            pending = [x for x in items if x.get("status") == "pending"][:20]
            results = {}
            for i, it in enumerate(pending):
                results[it["id"]] = ai_review(it, use_llm=(use_llm and i < 5))
            with LOCK:
                items = load_items()
                for x in items:
                    if x.get("id") in results:
                        x["ai"] = results[x["id"]]
                save_items(items)
            # 低风险自动上架 / 高危自动拦截
            auto = 0
            auto_rej = 0
            try:
                approve_at = int(cfg.get("approve_threshold") or 0)
            except Exception:
                approve_at = 20
            try:
                reject_at = int(cfg.get("reject_threshold") or 80)
            except Exception:
                reject_at = 80
            with LOCK:
                items = load_items()
                for x in items:
                    if x.get("status") != "pending":
                        continue
                    ai = x.get("ai") or {}
                    hits = scope_violation(x)
                    if hits:
                        x["status"] = "rejected"
                        x["autoRejected"] = True
                        x["rejectReason"] = "标题含交友/招嫖暗示（%s），不属于失物招领范围" % "、".join(hits)
                        x["reviewedBy"] = "AI"
                        x["reviewedAt"] = now_ms()
                        auto_rej += 1
                        continue
                    if ai.get("source") != "llm":
                        continue          # 没有大模型结论时不自动放行
                    score = int(ai.get("score") or 0)
                    if cfg.get("auto_approve") and ai.get("decision") == "approve" and score <= approve_at:
                        x["status"] = "approved"
                        x["autoApproved"] = True
                        x["reviewedBy"] = "AI"
                        x["reviewedAt"] = now_ms()
                        auto += 1
                    elif cfg.get("auto_reject") and ai.get("decision") == "reject" and score >= reject_at:
                        x["status"] = "rejected"
                        x["autoRejected"] = True
                        x["rejectReason"] = "AI 自动拦截：" + (ai.get("reason") or "疑似违规内容")
                        x["reviewedBy"] = "AI"
                        x["reviewedAt"] = now_ms()
                        auto_rej += 1
                save_items(items)
            return self._json({"ok": True, "count": len(results),
                               "llm": use_llm, "autoApproved": auto, "autoRejected": auto_rej})

        return self._send(404, "not found", "text/plain; charset=utf-8")

    def do_PATCH(self):
        path = unquote(urlparse(self.path).path)
        patch = self._read_body()

        if path.startswith("/api/claims/") and not path.endswith("/complete"):
            owner = self._owner()
            claim_id = path[len("/api/claims/"):]
            body = patch
            status = body.get("status")
            if status not in ("accepted", "rejected", "need_more"):
                return self._json({"error": "bad status"}, 400)
            with LOCK:
                claims = load_claims()
                items = load_items()
                claim = next((c for c in claims if c.get("id") == claim_id), None)
                if not claim:
                    return self._json({"error": "not found"}, 404)
                item = next((x for x in items if x.get("id") == claim.get("itemId")), None)
                if not item or item.get("ownerToken") != owner:
                    return self._json({"error": "只有发布者能处理"}, 403)
                claim["status"] = status
                claim["updatedAt"] = now_ms()
                others = []
                if status == "accepted":
                    item["status"] = "claimed"
                    if not claim.get("returnCode") and item.get("type") in ("found", "lost"):
                        claim["returnCode"] = "%06d" % random.randint(0, 999999)
                        claim["returnCodeFor"] = (claim.get("from") if item.get("type") == "found"
                                                  else item.get("ownerToken"))
                        claim["holder"] = (item.get("ownerToken") if item.get("type") == "found"
                                           else claim.get("from"))
                    # 同一个物品的其他待处理申请自动关闭，不能让它们一直挂着
                    for c2 in claims:
                        if (c2.get("itemId") == claim.get("itemId")
                                and c2.get("id") != claim.get("id")
                                and c2.get("status") == "pending"):
                            c2["status"] = "rejected"
                            c2["rejectReason"] = "物品已被其他人认领"
                            c2["updatedAt"] = now_ms()
                            others.append(c2)
                save_claims(claims)
                save_items(items)
                notices = load_notices()
                if status == "accepted":
                    phone = (item.get("contact") or {}).get("phone") or "（发布者没留电话，请在详情里联系）"
                    if claim.get("kind") == "found":
                        add_notice(notices, claim.get("from"), "accepted",
                                   "失主已确认你捡到的《%s》，对方电话：%s" % (item.get("title") or "", phone),
                                   item.get("id"))
                    else:
                        add_notice(notices, claim.get("from"), "accepted",
                                   "你申请的《%s》已通过，发布者电话：%s" % (item.get("title") or "", phone),
                                   item.get("id"))
                    for c2 in others:
                        add_notice(notices, c2.get("from"), "rejected",
                                   "《%s》已被其他同学认领，感谢你的申请" % (item.get("title") or ""),
                                   item.get("id"))
                elif status == "need_more":
                    add_notice(notices, claim.get("from"), "need_more",
                               "发布者希望你再补充一点《%s》的细节（颜色/标记/划痕）" % (item.get("title") or ""),
                               item.get("id"), claim.get("id"))
                else:
                    add_notice(notices, claim.get("from"), "rejected",
                               "发布者认为这不是他丢的《%s》。如果你确认是你的，可以补充说明后再申请"
                               % (item.get("title") or ""),
                               item.get("id"), claim.get("id"))
                save_notices(notices)
            return self._json({"ok": True, "status": status})

        if path.startswith("/api/admin/announcements/"):
            if not self._need_admin():
                return
            aid = path[len("/api/admin/announcements/"):]
            body = patch
            _check_text = (str(body.get("title") or "") + " " + str(body.get("body") or "")).strip()
            if _check_text:
                _ok, _why = moderate_text(_check_text, "公告")
                if not _ok:
                    return self._json({"error": "公告未通过审核：" + _why}, 400)
            with LOCK:
                arr = load_announcements()
                target = next((x for x in arr if x.get("id") == aid), None)
                if not target:
                    return self._json({"error": "not found"}, 404)
                if "title" in body:
                    target["title"] = str(body.get("title") or "").strip()[:60]
                if "body" in body:
                    target["body"] = str(body.get("body") or "").strip()[:2000]
                if "pinned" in body:
                    target["pinned"] = bool(body.get("pinned"))
                if body.get("status") in ("draft", "published"):
                    target["status"] = body["status"]
                    if body["status"] == "published" and not target.get("publishedAt"):
                        target["publishedAt"] = now_ms()
                target["updatedAt"] = now_ms()
                save_announcements(arr)
            return self._json(target)

        if path.startswith("/api/admin/items/"):
            if not self._need_admin():
                return
            item_id = path[len("/api/admin/items/"):]
            with LOCK:
                items = load_items()
                for it in items:
                    if it.get("id") == item_id:
                        status = patch.get("status")
                        if status in ALLOWED_STATUS:
                            it["status"] = status
                        if "rejectReason" in patch:
                            it["rejectReason"] = str(patch["rejectReason"])[:200]
                        it["updatedAt"] = now_ms()
                        save_items(items)
                        return self._json(it)
            return self._json({"error": "not found"}, 404)

        if path.startswith("/api/items/"):
            owner = self._owner()
            item_id = path[len("/api/items/"):]
            snapshot = None
            with LOCK:
                items = load_items()
                for it in items:
                    if it.get("id") == item_id:
                        if not owner or it.get("ownerToken") != owner:
                            return self._json({"error": "forbidden"}, 403)
                        for k in ("title", "desc", "place", "eventTime", "secret", "photo"):
                            if k in patch:
                                it[k] = patch[k]
                        if "cat" in patch:
                            it["cat"] = str(patch["cat"])[:20]
                        elif "category" in patch:
                            it["cat"] = str(patch["category"])[:20]
                        if isinstance(patch.get("contact"), dict):
                            it["contact"] = {"phone": str(patch["contact"].get("phone") or "")[:20]}
                        elif "phone" in patch:
                            it["contact"] = {"phone": str(patch["phone"])[:20]}
                        _ph = (it.get("contact") or {}).get("phone") or ""
                        if _ph:
                            _chk = phone_check(_ph)
                            if _chk["status"] == "red":
                                return self._json({"error": "电话号码不正确：" + _chk["reason"]}, 400)

                            it["contact"]["phone"] = _chk["normalized"] or _ph
                            it["phoneStatus"] = _chk["status"]
                            it["phoneType"] = _chk["type"]
                        it["summary"] = str(patch.get("summary") or "")[:40]
                        it["fields"] = patch.get("fields") if isinstance(patch.get("fields"), dict) else None
                        if not it["summary"]:
                            _f = _format_fallback(it.get("title") or "", it.get("desc") or "", it.get("place") or "")
                            it["summary"] = _f["summary"]
                            if not it.get("fields"):
                                it["fields"] = _f["fields"]
                        it["status"] = "pending"
                        it["rejectReason"] = ""
                        it["updatedAt"] = now_ms()
                        save_items(items)
                        snapshot = dict(it)
                        break
            if not snapshot:
                return self._json({"error": "not found"}, 404)
            # 改完重新过一遍 AI 审核（和首次发布同一条链路，不需要人工）
            ai = review_item(snapshot)
            trusted = ai.get("source") == "llm"
            hits = scope_violation(snapshot)
            status = "pending"
            reason = ""
            if hits:
                status = "rejected"
                reason = "内容涉及平台范围之外：" + "、".join(hits)
            elif not trusted:
                status = "rejected"
                reason = "审核系统暂时不可用，内容没有公开，请稍后重新提交"
            elif ai.get("decision") == "approve":
                status = "approved"
            elif ai.get("decision") == "reject":
                status = "rejected"
                reason = ai.get("reason") or "内容不符合平台规则，请修改后再提交"
            with LOCK:
                items = load_items()
                for it in items:
                    if it.get("id") == item_id:
                        it["ai"] = ai
                        it["status"] = status
                        it["rejectReason"] = reason
                        it["reviewedBy"] = "AI" if trusted else "system"
                        it["reviewedAt"] = now_ms()
                        it["updatedAt"] = now_ms()
                        if (trusted and it.get("type") in ("lost", "found")
                                and ai.get("guessType") and ai["guessType"] != it.get("type")):
                            it["typeSuggestion"] = ai["guessType"]
                        save_items(items)
                        return self._json(it)
            return self._json({"error": "not found"}, 404)

        return self._send(404, "not found", "text/plain; charset=utf-8")

    def do_DELETE(self):
        path = unquote(urlparse(self.path).path)
        if path.startswith("/api/admin/announcements/"):
            if not self._need_admin():
                return
            aid = path[len("/api/admin/announcements/"):]
            with LOCK:
                arr = load_announcements()
                arr = [x for x in arr if x.get("id") != aid]
                save_announcements(arr)
            return self._json({"ok": True})

        if not path.startswith("/api/items/"):
            return self._send(404, "not found", "text/plain; charset=utf-8")
        owner = self._owner()
        item_id = path[len("/api/items/"):]
        with LOCK:
            items = load_items()
            target = next((x for x in items if x.get("id") == item_id), None)
            if not target:
                return self._json({"error": "not found"}, 404)
            if not owner or target.get("ownerToken") != owner:
                return self._json({"error": "forbidden"}, 403)
            save_items([x for x in items if x.get("id") != item_id])
            # 删除后，这条的申请全部关闭，避免申请人一直显示"等待确认"
            claims = load_claims()
            affected = []
            for c in claims:
                if c.get("itemId") == item_id and c.get("status") == "pending":
                    c["status"] = "rejected"
                    c["rejectReason"] = "发布者已撤回这条信息"
                    c["updatedAt"] = now_ms()
                    affected.append(c)
            if affected:
                save_claims(claims)
                notices = load_notices()
                for c in affected:
                    add_notice(notices, c.get("from"), "rejected",
                               "《%s》已被发布者撤回，申请自动关闭" % (target.get("title") or ""),
                               item_id)
                save_notices(notices)
        return self._json({"ok": True})

    # ---------- 实现 ----------
    def _clean(self, body):
        return {
            "type": body.get("type") if body.get("type") in ("lost", "found", "help") else "lost",
            "cat": str(body.get("cat") or "other")[:20],
            "title": str(body.get("title") or "").strip()[:30],
            "desc": str(body.get("desc") or "").strip()[:300],
            "place": str(body.get("place") or "").strip()[:40],
            "eventTime": str(body.get("eventTime") or "")[:40],
            "secret": str(body.get("secret") or "").strip()[:100],
            "photo": body.get("photo") if isinstance(body.get("photo"), str) else None,
            "fields": {k: str((body.get("fields") or {}).get(k) or "")[:30]
                       for k in ("color", "brand", "condition", "feature", "contents")}
            if isinstance(body.get("fields"), dict) else None,
            "summary": str(body.get("summary") or "").strip()[:40],
            "helpCat": str(body.get("helpCat") or "")[:20],
            "contact": {"phone": str((body.get("contact") or {}).get("phone") or "")[:20]}
            if isinstance(body.get("contact"), dict) else {"phone": ""},
        }

    def _serve_file(self, name):
        path = os.path.join(BASE_DIR, name)
        if not os.path.exists(path):
            return self._send(500, "找不到 %s，请确认它和 server.py 在同一个文件夹" % name,
                              "text/plain; charset=utf-8")
        return self._serve_path(path)

    def _serve_path(self, path):
        ext = os.path.splitext(path)[1].lower()
        ctype = {
            ".html": "text/html; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".json": "application/json; charset=utf-8",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".svg": "image/svg+xml",
        }.get(ext, "application/octet-stream")
        with open(path, "rb") as f:
            data = f.read()
        if ext == ".html":
            import hashlib
            etag = '"' + hashlib.md5(data).hexdigest() + '"'
            if self.headers.get("If-None-Match") == etag:
                self.send_response(304)
                self.send_header("ETag", etag)
                self.end_headers()
                return
            self._send(200, data, ctype, {"ETag": etag, "Cache-Control": "no-cache"})
            return
        self._send(200, data, ctype)


# ---------------------------------------------------------------- 网络地址 / 二维码

def lan_ips():
    import subprocess as sp

    scored = []
    try:
        raw = sp.check_output(["ipconfig"], stderr=sp.DEVNULL)
        try:
            text = raw.decode("mbcs", errors="ignore")
        except Exception:
            text = raw.decode("utf-8", errors="ignore")
        for block in re.split(r"\r?\n\r?\n", text):
            m = re.search(r"IPv4[^:：]*[:：]\s*(\d{1,3}(?:\.\d{1,3}){3})", block, re.I)
            if not m:
                continue
            ip = m.group(1)
            if ip.startswith("127.") or ip.startswith("169.254."):
                continue
            head = block.strip().splitlines()[0] if block.strip() else ""
            low = head.lower()
            if any(k in low for k in ("vmware", "virtualbox", "vethernet", "hyper-v", "loopback", "vpn", "tap-")):
                continue
            if "无线" in head or "wi-fi" in low or "wlan" in low:
                score = 0
            elif "以太网" in head or "ethernet" in low:
                score = 1
            else:
                score = 2
            if not any(ip == x[1] for x in scored):
                scored.append((score, ip))
    except Exception:
        pass

    if not scored:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            scored.append((0, s.getsockname()[0]))
            s.close()
        except Exception:
            pass

    def bonus(ip):
        if ip.startswith("192.168."):
            return 0
        if ip.startswith("10."):
            return 1
        if re.match(r"172\.(1[6-9]|2\d|3[01])\.", ip):
            return 2
        return 3

    scored.sort(key=lambda x: (x[0], bonus(x[1])))
    return [ip for _, ip in scored]


def make_qr_png(text, path, box=8, border=4):
    import struct
    import zlib

    import qrcode

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,
                       border=border, box_size=1)
    qr.add_data(text)
    qr.make(fit=True)
    matrix = qr.get_matrix()
    n = len(matrix)
    size = n * box
    rows = []
    for row in matrix:
        line = bytearray()
        for dark in row:
            line += b"\x3b\x1d\x63" * box if dark else b"\xff\xff\xff" * box
        line = b"\x00" + bytes(line)
        for _ in range(box):
            rows.append(line)
    raw = b"".join(rows)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 9))
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return path


QR_HTML = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>扫码打开 · 清华校园拾光里</title>
<style>
body{margin:0;min-height:100vh;background:linear-gradient(160deg,#45106e,#62269c 55%,#8a52c7);
font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;color:#fff;padding:24px 16px;box-sizing:border-box;display:flex;justify-content:center}
.wrap{width:100%;max-width:900px;display:flex;gap:18px;flex-wrap:wrap;justify-content:center;align-items:flex-start}
.card{background:#fff;color:#23202b;border-radius:22px;padding:22px 18px;flex:1 1 320px;max-width:420px;
text-align:center;box-shadow:0 18px 50px rgba(0,0,0,.28)}
.card.admin{border:3px solid #ffd166}
h1{font-size:18px;margin:0 0 2px}
.badge{display:inline-block;font-size:11px;border-radius:99px;padding:2px 10px;margin-bottom:8px}
.badge.user{background:#e6f4ea;color:#2f7d46}
.badge.adminb{background:#fff4d6;color:#a97a00}
p{font-size:12px;color:#8a8594;line-height:1.65;margin:0 0 6px}
img{width:100%;max-width:260px;display:block;margin:12px auto;border-radius:12px;image-rendering:pixelated}
.url{font-size:12px;word-break:break-all;background:#f1eaf9;color:#62269c;border-radius:10px;
padding:9px 11px;user-select:all;line-height:1.5}
.pwd{margin-top:12px;font-size:22px;letter-spacing:4px;font-weight:800;color:#a97a00;
background:#fff8e6;border:1px dashed #e3c98a;border-radius:10px;padding:8px}
.pwd small{display:block;font-size:11px;letter-spacing:0;color:#8a6100;font-weight:400;margin-bottom:2px}
.note{font-size:11px;color:#c0392b;background:#fdf0f0;border-radius:10px;padding:8px 10px;
margin-top:12px;line-height:1.6;text-align:left}
</style></head><body>
<div class="wrap">
  <div class="card">
    <span class="badge user">用户端 · 发给同学</span>
    <h1>手机扫码打开</h1>
    <p>任何网络都行：流量、别家 WiFi 都可以</p>
    <img src="二维码.png" alt="用户端二维码">
    <div class="url">__USER_URL__</div>
    <div class="note">⚠️ 地址只在本次运行期间有效，电脑关了就失效。</div>
  </div>
  <div class="card admin">
    <span class="badge adminb">管理端 · 只给自己</span>
    <h1>管理员扫码登录</h1>
    <p>用这个码打开审核后台</p>
    <img src="管理端二维码.png" alt="管理端二维码">
    <div class="url">__ADMIN_URL__</div>
    <div class="pwd"><small>管理员密码</small>__PASSWORD__</div>
    <div class="note">⚠️ 管理端链接和密码都不要发给别人。</div>
  </div>
</div>
</body></html>
"""


def show_qr(user_url, admin_url=None, password=""):
    try:
        make_qr_png(user_url, os.path.join(BASE_DIR, "二维码.png"))
        if admin_url:
            make_qr_png(admin_url, os.path.join(BASE_DIR, "管理端二维码.png"))
        page = os.path.join(BASE_DIR, "二维码.html")
        html = (QR_HTML
                .replace("__USER_URL__", user_url)
                .replace("__ADMIN_URL__", admin_url or "")
                .replace("__PASSWORD__", password or ""))
        with open(page, "w", encoding="utf-8") as f:
            f.write(html)
        try:
            os.startfile(page)
        except Exception:
            pass
        return True
    except Exception as e:
        print("  （二维码生成失败：%s）" % e)
        return False


def print_qr(url):
    return show_qr(url)


# ---------------------------------------------------------------- 启动

def main():
    if not startup_gate():
        try:
            input("按回车退出…")
        except Exception:
            pass
        return
    port = int(os.environ.get("SG_PORT", "8000"))
    server = None
    for p in range(port, port + 12):
        try:
            server = ThreadingHTTPServer(("0.0.0.0", p), Handler)
            port = p
            break
        except OSError:
            continue
    if server is None:
        print("端口都被占用了，请关掉其他程序后重试。")
        return

    start_review_workers(2)
    pwd = ensure_admin_password()
    ips = lan_ips()
    primary = "http://%s:%d/" % (ips[0], port) if ips else None

    print()
    print("=" * 60)
    print("  清华校园拾光里 · 服务已启动")
    print("=" * 60)
    print("  用户端： http://127.0.0.1:%d/" % port)
    print("  管理端： http://127.0.0.1:%d/管理端.html" % port)
    for ip in ips:
        print("  同一 Wi-Fi： http://%s:%d/" % (ip, port))
    print()
    print("  管理员密码： %s" % pwd)
    print("  （也写在 管理员密码.txt 里；改密码编辑 admin.json）")
    print()
    print("  数据文件： %s" % DATA_FILE)
    print("  停止服务： 关闭这个窗口，或按 Ctrl+C")
    print("=" * 60)
    print()

    if os.environ.get("SG_OPEN") == "1" and primary:
        try:
            import webbrowser
            webbrowser.open("http://127.0.0.1:%d/" % port)
        except Exception:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()

