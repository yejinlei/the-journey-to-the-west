# -*- coding: utf-8 -*-
"""推送 db.js / sw.js 修复到 gh-pages 和 main 分支。"""
import base64
import json
import os
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


import sys

FILES = [
    ("gh-pages", "js/db.js", "docs/js/db.js"),
    ("gh-pages", "sw.js", "docs/sw.js"),
    ("main", "docs/js/db.js", "docs/js/db.js"),
    ("main", "docs/sw.js", "docs/sw.js"),
]

MSG = sys.argv[1] if len(sys.argv) > 1 else "fix: manifest.json 加载失败 (assetUrl 用 baseURI + bust cache + SW v2)"

for branch, rel, local in FILES:
    url = f"{API}/{urllib.parse.quote(rel, safe='/')}?ref={branch}"
    g = req(url)
    if "__error__" in g:
        print(f"  MISS {branch} {rel}  ->  {g['__error__']}")
        continue
    sha = g["sha"]
    with open(local, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    body = {"message": MSG, "content": b64, "branch": branch, "sha": sha}
    r = req(f"{API}/{urllib.parse.quote(rel, safe='/')}", method="PUT", data=body)
    if "__error__" in r:
        print(f"  PUT FAIL {branch} {rel}  ->  {r['__error__']}  {r['__body__'][:200]}")
    else:
        print(f"  ok {branch} {rel}  ->  {r['commit']['sha'][:7]}")
    time.sleep(0.3)
