#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把之前被设为 hidden 的旧发布恢复为可见。

只处理 hidden，不处理 removed（除非显式 --include-removed）。
默认只预览，真正写入需要 --apply。

在服务器运行：
  cd /opt/lostfound
  python3 restore_hidden_items.py
  python3 restore_hidden_items.py --apply
"""
import argparse
import json
import os
import shutil
import time

PATH = "items.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="真正写回 items.json")
    ap.add_argument("--include-removed", action="store_true", help="连 removed 也恢复")
    args = ap.parse_args()

    if not os.path.isfile(PATH):
        raise SystemExit("找不到 items.json，请先 cd /opt/lostfound")

    with open(PATH, "r", encoding="utf-8") as f:
        items = json.load(f)
    if not isinstance(items, list):
        raise SystemExit("items.json 不是列表，已停止")

    targets = [
        x for x in items
        if isinstance(x, dict)
        and (x.get("status") == "hidden"
             or (args.include_removed and x.get("status") == "removed"))
    ]

    print("总条数：", len(items))
    print("可恢复条数：", len(targets))
    for x in targets[:30]:
        print("-", x.get("status"), x.get("type"), x.get("title"), x.get("ownerToken"))
    if len(targets) > 30:
        print("... 还有", len(targets) - 30, "条")

    if not args.apply:
        print("\n这是预览，没有写入。确认后加 --apply。")
        return

    backup = "items.json.bak.restore.%s" % time.strftime("%Y%m%d%H%M%S")
    shutil.copy2(PATH, backup)
    for x in targets:
        x["status"] = "closed" if x.get("closedAt") else "approved"
        x.pop("hiddenReason", None)
        x["updatedAt"] = int(time.time() * 1000)

    tmp = PATH + ".restore.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    os.replace(tmp, PATH)
    print("已恢复", len(targets), "条")
    print("备份：", backup)
    print("请重启服务： sudo systemctl restart lostfound")


if __name__ == "__main__":
    main()
