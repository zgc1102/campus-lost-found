#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拾光里 · 公网共享启动器
把本机服务 + Cloudflare 快速隧道一起跑起来，任何网络的同学都能访问。
不需要注册任何账号。电脑关掉 / 窗口关闭后，分享就停止。
"""

import os
import re
import subprocess
import sys
import threading
import time
from http.server import ThreadingHTTPServer

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import server as sg  # 复用同一套接口和数据

CF_CANDIDATES = [
    r"C:\Program Files (x86)\cloudflared\cloudflared.exe",
    r"C:\Program Files\cloudflared\cloudflared.exe",
    os.path.join(BASE, "cloudflared.exe"),
    "cloudflared",
]


def write_shortcuts(url):
    """在桌面写两个 .url 快捷方式，每次启动自动指向最新地址"""
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    if not os.path.isdir(desktop):
        desktop = BASE
    for name, target in (("拾光里-用户端.url", url + "/"),
                         ("拾光里-管理端.url", url + "/admin")):
        try:
            with open(os.path.join(desktop, name), "w", encoding="utf-8") as f:
                f.write("[InternetShortcut]\nURL=%s\nIconIndex=0\n" % target)
        except Exception:
            pass


def find_cloudflared():
    for p in CF_CANDIDATES:
        if p == "cloudflared":
            return p
        if os.path.exists(p):
            return p
    return None


def free_port(start=8000):
    import socket
    for p in range(start, start + 12):
        s = socket.socket()
        try:
            s.bind(("0.0.0.0", p))
            s.close()
            return p
        except OSError:
            s.close()
    return start


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    if not sg.startup_gate():
        try:
            input("按回车退出…")
        except Exception:
            pass
        return

    port = free_port()
    httpd = ThreadingHTTPServer(("0.0.0.0", port), sg.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    cf = find_cloudflared()

    print()
    print("=" * 60)
    print("  清华校园拾光里 · 公网共享模式")
    print("=" * 60)
    print("  本机服务已启动： http://127.0.0.1:%d" % port)
    print("  数据文件：       %s" % sg.DATA_FILE)
    print()

    if cf is None:
        print("  [!] 没找到 cloudflared，无法生成公网地址。")
        print("      请先运行：winget install --id Cloudflare.cloudflared")
        print()
        input("按回车退出…")
        return

    print("  正在申请公网地址（约 10 秒）…")
    print()

    while True:
        try:
            proc = subprocess.Popen(
                [cf, "tunnel", "--url", "http://127.0.0.1:%d" % port,
                 "--no-autoupdate", "--protocol", "http2", "--loglevel", "info"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="ignore", bufsize=1,
            )
        except Exception as e:
            print("  启动隧道失败：%s" % e)
            break

        got = False
        for line in proc.stdout:
            m = re.search(r"https://[a-z0-9][a-z0-9-]*\.trycloudflare\.com", line)
            if m and not got:
                got = True
                url = m.group(0)
                try:
                    with open(os.path.join(BASE, "公网地址.txt"), "w", encoding="utf-8") as f:
                        f.write(url + "\n")
                except Exception:
                    pass
                print("=" * 60)
                print("  用户端（发这个给同学，任何网络都能打开）：")
                print()
                print("      %s" % url)
                print()
                print("  管理端（只发给你自己）：")
                print("      %s/admin" % url)
                print("      密码：%s" % sg.ensure_admin_password())
                print()
                print("  二维码页面已自动打开（扫码或直接复制链接）")
                print()
                write_shortcuts(url)
                print("  桌面上已生成「拾光里-用户端」和「拾光里-管理端」快捷方式")
                print()
                sg.show_qr(url + "/", url + "/admin", sg.ensure_admin_password())
                print()
                print("  ⚠️ 这个地址只在本次运行期间有效，窗口关掉就失效。")
                print("  ⚠️ 电脑必须保持开机、窗口必须保持打开。")
                print("=" * 60)
                print()
            if "ERR" in line and ("Failed to connect" in line or "reconnect" in line.lower()):
                print("  · 隧道提示：%s" % line.strip()[:120])

        try:
            proc.wait(timeout=3)
        except Exception:
            pass
        print()
        print("  隧道断开，3 秒后自动重连（公网地址会变，以新打印的为准）…")
        print()
        time.sleep(3)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n已停止。")

