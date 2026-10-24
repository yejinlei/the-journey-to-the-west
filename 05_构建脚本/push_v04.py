# -*- coding: utf-8 -*-
"""推送 v0.4（并入古本 + 百回详注两版）到 gh-pages + main。

需要推的文件：
  4 张有变更的 parquet（agent.html 用的 DuckDB 源）
    editions / chapters / lines / pages
  7 个页面 JSON（versions.json 会展示新版；read.json 有 204 回 chapters）
  manifest
"""
import base64
import json
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

REPO = "yejinlei/the-journey-to-the-west"
TOKEN = subprocess.check_output(["gh", "auth", "token"]).decode().strip()
API = f"https://api.github.com/repos/{REPO}/contents"
MSG = "data(v0.4): 并入古本 gubao + 百回详注 baihui_xiangzhu 两版正文（+200 回 / +3917 行 / +200 页）"


def req(url, method="GET", data=None):
    headers = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json"}
    body = json.dumps(data).encode("utf-8") if data else None
    r = urllib.request.Request(url, headers=headers, data=body, method=method)
    if data:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"__error__": e.code, "__body__": e.read().decode("utf-8", "replace")[:400]}


# (branch, remote_path, local_path)
FILES = [
    # --- parquet 数据（4 张有变更的表） ---
    ("gh-pages", "data/editions.parquet", "docs/data/editions.parquet"),
    ("gh-pages", "data/chapters.parquet", "docs/data/chapters.parquet"),
    ("gh-pages", "data/lines.parquet",    "docs/data/lines.parquet"),
    ("gh-pages", "data/pages.parquet",    "docs/data/pages.parquet"),
    # --- 页面 JSON（7 个）---
    ("gh-pages", "data/pages/read.json",         "docs/data/pages/read.json"),
    ("gh-pages", "data/pages/entities.json",     "docs/data/pages/entities.json"),
    ("gh-pages", "data/pages/versions.json",     "docs/data/pages/versions.json"),
    ("gh-pages", "data/pages/relics.json",       "docs/data/pages/relics.json"),
    ("gh-pages", "data/pages/annotations.json",  "docs/data/pages/annotations.json"),
    ("gh-pages", "data/pages/events.json",       "docs/data/pages/events.json"),
    ("gh-pages", "data/pages/graph.json",        "docs/data/pages/graph.json"),
    ("gh-pages", "data/pages/_manifest.json",    "docs/data/pages/_manifest.json"),

    # --- main 分支同步 ---
    ("main", "docs/data/editions.parquet", "docs/data/editions.parquet"),
    ("main", "docs/data/chapters.parquet", "docs/data/chapters.parquet"),
    ("main", "docs/data/lines.parquet",    "docs/data/lines.parquet"),
    ("main", "docs/data/pages.parquet",    "docs/data/pages.parquet"),
    ("main", "docs/data/pages/read.json",         "docs/data/pages/read.json"),
    ("main", "docs/data/pages/entities.json",     "docs/data/pages/entities.json"),
    ("main", "docs/data/pages/versions.json",     "docs/data/pages/versions.json"),
    ("main", "docs/data/pages/relics.json",       "docs/data/pages/relics.json"),
    ("main", "docs/data/pages/annotations.json",  "docs/data/pages/annotations.json"),
    ("main", "docs/data/pages/events.json",       "docs/data/pages/events.json"),
    ("main", "docs/data/pages/graph.json",        "docs/data/pages/graph.json"),
    ("main", "docs/data/pages/_manifest.json",    "docs/data/pages/_manifest.json"),
]


def push_one(branch: str, rel: str, local: str):
    # 探测远程
    url = f"{API}/{urllib.parse.quote(rel, safe='/')}?ref={branch}"
    g = req(url)
    sha = None
    if "__error__" not in g:
        sha = g["sha"]
    # 读本地
    try:
        with open(local, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        print(f"  SKIP missing local {local}")
        return "skip"
    body = {"message": MSG, "content": b64, "branch": branch}
    if sha:
        body["sha"] = sha
    r = req(f"{API}/{urllib.parse.quote(rel, safe='/')}", method="PUT", data=body)
    if "__error__" in r:
        code = r["__error__"]
        body_msg = r.get("__body__", "")[:200]
        print(f"  FAIL {branch} {rel}  ->  {code}  {body_msg}")
        return "fail"
    print(f"  ok   {branch} {rel}  ({len(b64)//1024} KB)  ->  {r['commit']['sha'][:7]}")
    return "ok"


def main():
    ok = fail = skip = 0
    for branch, rel, local in FILES:
        r = push_one(branch, rel, local)
        if r == "ok": ok += 1
        elif r == "skip": skip += 1
        else: fail += 1
        time.sleep(0.4)
    print(f"\nDone. ok={ok}  skip={skip}  fail={fail}")


if __name__ == "__main__":
    main()
