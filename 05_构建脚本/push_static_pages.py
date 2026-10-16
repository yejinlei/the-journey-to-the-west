# -*- coding: utf-8 -*-
"""推送静态渲染改造文件到 gh-pages 与 main 分支。

路径映射：
  docs/<x>          → gh-pages 根： <x>
  docs/<x>          → main 分支：  docs/<x>
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


def req(url, method="GET", data=None):
    headers = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json"}
    body = json.dumps(data).encode("utf-8") if data else None
    r = urllib.request.Request(url, headers=headers, data=body, method=method)
    if data:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"__error__": e.code, "__body__": e.read().decode("utf-8", "replace")[:400]}


# (branch, remote_path, local_path)
FILES = [
    # 7 个改造后的 HTML
    ("gh-pages", "read.html",         "docs/read.html"),
    ("gh-pages", "entities.html",     "docs/entities.html"),
    ("gh-pages", "versions.html",     "docs/versions.html"),
    ("gh-pages", "relics.html",       "docs/relics.html"),
    ("gh-pages", "annotations.html",  "docs/annotations.html"),
    ("gh-pages", "events.html",       "docs/events.html"),
    ("gh-pages", "graph.html",        "docs/graph.html"),
    # helper
    ("gh-pages", "js/page.js",        "docs/js/page.js"),
    # 7 个 JSON + manifest
    ("gh-pages", "data/pages/read.json",         "docs/data/pages/read.json"),
    ("gh-pages", "data/pages/entities.json",     "docs/data/pages/entities.json"),
    ("gh-pages", "data/pages/versions.json",     "docs/data/pages/versions.json"),
    ("gh-pages", "data/pages/relics.json",       "docs/data/pages/relics.json"),
    ("gh-pages", "data/pages/annotations.json",  "docs/data/pages/annotations.json"),
    ("gh-pages", "data/pages/events.json",       "docs/data/pages/events.json"),
    ("gh-pages", "data/pages/graph.json",        "docs/data/pages/graph.json"),
    ("gh-pages", "data/pages/_manifest.json",    "docs/data/pages/_manifest.json"),

    # main 分支同步（docs/ 子目录结构）
    ("main", "docs/read.html",         "docs/read.html"),
    ("main", "docs/entities.html",     "docs/entities.html"),
    ("main", "docs/versions.html",     "docs/versions.html"),
    ("main", "docs/relics.html",       "docs/relics.html"),
    ("main", "docs/annotations.html",  "docs/annotations.html"),
    ("main", "docs/events.html",       "docs/events.html"),
    ("main", "docs/graph.html",        "docs/graph.html"),
    ("main", "docs/js/page.js",        "docs/js/page.js"),
    ("main", "docs/data/pages/read.json",         "docs/data/pages/read.json"),
    ("main", "docs/data/pages/entities.json",     "docs/data/pages/entities.json"),
    ("main", "docs/data/pages/versions.json",     "docs/data/pages/versions.json"),
    ("main", "docs/data/pages/relics.json",       "docs/data/pages/relics.json"),
    ("main", "docs/data/pages/annotations.json",  "docs/data/pages/annotations.json"),
    ("main", "docs/data/pages/events.json",       "docs/data/pages/events.json"),
    ("main", "docs/data/pages/graph.json",        "docs/data/pages/graph.json"),
    ("main", "docs/data/pages/_manifest.json",    "docs/data/pages/_manifest.json"),
]

MSG = "feat: 构建期静态渲染 —— 7 页读 JSON，agent 页保留 DuckDB-WASM 实时查询"

ok = fail = skip = 0
for branch, rel, local in FILES:
    # 先探测远程
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
        skip += 1
        continue
    body = {"message": MSG, "content": b64, "branch": branch}
    if sha:
        body["sha"] = sha
    r = req(f"{API}/{urllib.parse.quote(rel, safe='/')}", method="PUT", data=body)
    if "__error__" in r:
        code = r["__error__"]
        body_msg = r.get("__body__", "")[:200]
        if code == 422 and "already exists" not in body_msg.lower() and "sha" not in body_msg.lower():
            # 422 通常是内容未变
            print(f"  SKIP {branch} {rel}  (unchanged)")
            skip += 1
        else:
            print(f"  FAIL {branch} {rel}  ->  {code}  {body_msg}")
            fail += 1
    else:
        print(f"  ok   {branch} {rel}  ->  {r['commit']['sha'][:7]}")
        ok += 1
    time.sleep(0.35)

print(f"\nDone. ok={ok}  skip={skip}  fail={fail}")
