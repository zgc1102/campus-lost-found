#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""并发压测（只依赖标准库）

用法：
  python scripts/loadtest.py --base http://127.0.0.1:8000 --path / --requests 1000 --concurrency 100
  python scripts/loadtest.py --base https://你的域名 --path /api/items --requests 2000 --concurrency 200
  python scripts/loadtest.py --base https://你的域名 --path / --requests 10000 --concurrency 500 --out result.json
"""
import argparse
import json
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor


def one(url, timeout):
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "lostfound-loadtest"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp.read()
            return time.time() - t0, resp.status
    except urllib.error.HTTPError as e:
        return time.time() - t0, e.code
    except Exception:
        return time.time() - t0, 0


def pct(values, p):
    if not values:
        return 0
    values = sorted(values)
    k = max(0, min(len(values) - 1, int(round((p / 100.0) * (len(values) - 1)))))
    return values[k]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="站点根地址，例如 https://example.com")
    ap.add_argument("--path", default="/", help="压测路径，默认首页")
    ap.add_argument("--requests", type=int, default=1000)
    ap.add_argument("--concurrency", type=int, default=100)
    ap.add_argument("--timeout", type=float, default=15)
    ap.add_argument("--out", default="", help="把结果写到 JSON 文件")
    args = ap.parse_args()

    url = args.base.rstrip("/") + args.path
    print("目标：%s" % url)
    print("请求：%d，并发：%d" % (args.requests, args.concurrency))

    lat = []
    codes = {}
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        for dt, code in pool.map(lambda _: one(url, args.timeout), range(args.requests)):
            lat.append(dt)
            codes[code] = codes.get(code, 0) + 1
    wall = time.time() - t0

    ok = codes.get(200, 0) + codes.get(304, 0)
    fail = args.requests - ok
    result = {
        "url": url,
        "requests": args.requests,
        "concurrency": args.concurrency,
        "wallSeconds": round(wall, 2),
        "rps": round(args.requests / wall, 1) if wall else 0,
        "ok": ok,
        "failed": fail,
        "failRate": round(fail / args.requests * 100, 2) if args.requests else 0,
        "latencyMs": {
            "p50": round(pct(lat, 50) * 1000),
            "p90": round(pct(lat, 90) * 1000),
            "p95": round(pct(lat, 95) * 1000),
            "p99": round(pct(lat, 99) * 1000),
            "max": round(max(lat) * 1000) if lat else 0,
            "avg": round(statistics.mean(lat) * 1000) if lat else 0,
        },
        "status": codes,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("已保存：%s" % args.out)


if __name__ == "__main__":
    main()
