#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""拾光里 MCP Server（stdio JSON-RPC）

把校园失物能力暴露成 MCP 工具，外部 Agent 可以直接调用：
  - search_lost_found  搜索公开的寻物/招领
  - get_tag            查询拾光码
  - campus_place_tips  校园地点失物建议

运行：
  python mcp_server.py
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))

PLACE_TIPS = {
    "图书馆": ["北馆（李文正馆）一层服务台", "老图书馆借还处", "自助借还机旁"],
    "食堂": ["观畴园（万人食堂）一层服务台", "清芬园入口失物箱", "桃李园前台"],
    "教学楼": ["六教 3 区物业值班室", "三教 / 四教楼管室", "教室讲台和后排"],
    "操场": ["紫操器材室", "综体前台", "看台入口和跑道边"],
    "宿舍": ["紫荆公寓楼管值班室", "一楼公告栏", "洗衣房"],
    "快递": ["快递驿站取件台", "驿站门口货架", "宿舍楼下快递点"],
}


def read_json(name, default):
    try:
        with open(os.path.join(BASE, name), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def public_item(x):
    return {
        "id": x.get("id"), "type": x.get("type"), "title": x.get("title"),
        "desc": x.get("desc"), "place": x.get("place"),
        "status": x.get("status"),
    }


def search_items(args):
    q = str(args.get("query") or "").strip()
    limit = max(1, min(20, int(args.get("limit") or 5)))
    items = read_json("items.json", [])
    rows = [x for x in items if x.get("status") in ("approved", "claimed", "closed")]
    if q:
        keys = [k for k in re.split(r"\s+", q) if k]
        def score(x):
            hay = (x.get("title") or "") + " " + (x.get("desc") or "") + " " + (x.get("place") or "")
            return sum(1 for k in keys if k in hay)
        rows.sort(key=score, reverse=True)
        rows = [x for x in rows if score(x) > 0] or rows
    return {"count": len(rows[:limit]), "items": [public_item(x) for x in rows[:limit]]}


def get_tag(args):
    code = str(args.get("code") or "").strip().upper()
    tags = read_json("tags.json", [])
    tag = next((x for x in tags if str(x.get("code") or "").upper() == code), None)
    if not tag:
        return {"found": False, "message": "拾光码不存在"}
    if not tag.get("active", True):
        return {"found": True, "deactivated": True, "message": "此码已注销"}
    return {
        "found": True, "code": tag.get("code"), "itemName": tag.get("itemName"),
        "note": tag.get("note"), "mode": tag.get("mode"),
        "phoneMasked": re.sub(r"(\d{3})\d{4}(\d{4})", r"\1****\2", str(tag.get("phone") or "")),
        "url": "https://shiguangli.work/?tag=" + str(tag.get("code") or ""),
    }


def place_tips(args):
    place = str(args.get("place") or "")
    for k, tips in PLACE_TIPS.items():
        if k in place:
            return {"place": place, "tips": tips}
    return {"place": place, "tips": ["校方失物招领点", "就近的楼管 / 前台"]}


TOOLS = [
    {
        "name": "search_lost_found",
        "description": "搜索清华校园公开的寻物/招领信息",
        "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["query"]},
    },
    {
        "name": "get_tag",
        "description": "按 code 查询拾光码；注销码返回 deactivated",
        "inputSchema": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]},
    },
    {
        "name": "campus_place_tips",
        "description": "查询校园地点失物招领点建议",
        "inputSchema": {"type": "object", "properties": {"place": {"type": "string"}}, "required": ["place"]},
    },
]


def handle(req):
    method = req.get("method")
    rid = req.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "shiguangli-mcp", "version": "1.0.0"},
        }}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = req.get("params", {}).get("name")
        args = req.get("params", {}).get("arguments") or {}
        if name == "search_lost_found":
            data = search_items(args)
        elif name == "get_tag":
            data = get_tag(args)
        elif name == "campus_place_tips":
            data = place_tips(args)
        else:
            data = {"error": "unknown tool"}
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}]
        }}
    if method and method.startswith("notifications/"):
        return None
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "method not found"}}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            res = handle(req)
            if res is not None:
                sys.stdout.write(json.dumps(res, ensure_ascii=False) + "\n")
                sys.stdout.flush()
        except Exception as e:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": None,
                                         "error": {"code": -32603, "message": str(e)}}, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
