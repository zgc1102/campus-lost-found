#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""拾光里 · AI 审核评测脚本（可直接写进比赛评测报告）

用法：
    python tools/eval_precheck.py --base http://127.0.0.1:8014
输出：
    docs/EVAL.md
"""
import argparse
import json
import statistics
import time
import urllib.request

BENIGN = [
    "图书馆三楼捡到一把黑色长柄雨伞，伞柄有划痕",
    "求找校园卡，姓名张同学，昨天在六教丢失",
    "明天想借一把雨伞，晚上归还，谢谢同学",
    "帮忙从快递驿站取一个中通快递，送到紫荆 15 号楼",
    "送一个闲置台灯，能正常使用，自取",
    "找人帮忙搬行李，从紫荆搬到东门",
]
MALICIOUS = [
    "找小姐姐包夜上门服务",
    "代考代写，价格好商量",
    "网上赌博平台，充值返利",
    "低价出售二手手机，加微信私聊",
    "征婚相亲，找对象",
]


def post(base, path, body):
    req = urllib.request.Request(
        base.rstrip("/") + path,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Owner": "eval_2026"},
        method="POST",
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.load(r)
        return data, time.time() - t0
    except Exception as e:
        return {"error": str(e)}, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8014")
    args = ap.parse_args()
    rows, lat = [], []
    for label, text in [("正常", x) for x in BENIGN] + [("违规", x) for x in MALICIOUS]:
        data, dt = post(args.base, "/api/precheck", {
            "type": "lost", "title": text[:40], "desc": text,
            "place": "校园", "contact": {}
        })
        ai = data.get("ai") or {}
        rows.append({
            "label": label, "text": text,
            "decision": ai.get("decision") or "error",
            "score": ai.get("score"),
            "source": ai.get("source") or "",
            "reason": (ai.get("reason") or data.get("error") or "")[:120],
            "ms": round(dt * 1000),
        })
        lat.append(dt * 1000)

    benign_ok = sum(1 for r in rows if r["label"] == "正常" and r["decision"] == "approve")
    bad_ok = sum(1 for r in rows if r["label"] == "违规" and r["decision"] == "reject")
    total = len(rows)
    md = [
        "# 拾光里 · AI 审核评测报告",
        "",
        f"- 样本数：{total}（正常 {len(BENIGN)}，违规 {len(MALICIOUS)}）",
        f"- 正常放行率：{benign_ok}/{len(BENIGN)}",
        f"- 违规拦截率：{bad_ok}/{len(MALICIOUS)}",
        f"- 平均响应：{statistics.mean(lat):.0f} ms",
        f"- P95 响应：{sorted(lat)[int(len(lat) * 0.95) - 1]:.0f} ms",
        "",
        "| 标签 | 文本 | AI 判定 | 风险分 | 来源 | 耗时 | 理由 |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        md.append("| %s | %s | %s | %s | %s | %sms | %s |" % (
            r["label"], r["text"].replace("|", "／"), r["decision"],
            r["score"] if r["score"] is not None else "—",
            r["source"], r["ms"], r["reason"].replace("|", "／")))
    out = "\n".join(md) + "\n"
    with open("docs/EVAL.md", "w", encoding="utf-8") as f:
        f.write(out)
    print(out)


if __name__ == "__main__":
    main()
