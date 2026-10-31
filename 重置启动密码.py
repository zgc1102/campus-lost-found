#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重置启动密码：验证旧密码后删除绑定，下次启动会重新设置。"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import server as sg

if not os.path.exists(sg.STARTUP_FILE):
    print("还没有设置过启动密码，直接启动一次就会提示设置。")
    input("按回车退出…")
    sys.exit(0)

with open(sg.STARTUP_FILE, "r", encoding="utf-8") as f:
    cfg = __import__("json").load(f)

print("=" * 60)
print("  重置启动密码")
print("=" * 60)
for _ in range(3):
    pwd = sg._ask("当前启动密码：")
    if sg._hash_pwd(pwd, cfg.get("salt") or "") == cfg.get("hash"):
        os.remove(sg.STARTUP_FILE)
        print("已清除。下次启动会重新设置一个新的启动密码。")
        break
    print("密码不对。")
else:
    print("连续错误，未做任何修改。")

input("按回车退出…")
