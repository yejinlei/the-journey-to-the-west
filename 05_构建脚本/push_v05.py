# -*- coding: utf-8 -*-
"""推送 v0.5（read.html 三版切换器）到 gh-pages + main。

只推 2 个变更文件 × 2 分支 = 4 次 PUT。
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
MSG = "feat(read, v0.5): read.html 三版切换器（xinke_pingbi / gubao / baihui_xiangzhu）"


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


FILES = [
    ("gh-pages", "read.html",           "docs/read.html"),
    ("gh-pages", "data/pages/read.json","docs/data/pages/read.json"),
    ("main",     "docs/read.html",      "docs/read.html"),
    ("main",     "docs/data/pages/read.json", "docs/data/pages/read.json"),
]


def push_one(branch, rel, local):
    url = f"{API}/{urllib.parse.quote(rel, safe='/')}?ref={branch}"
    g = req(url)
    sha = None
    if "__error__" not in g:
        sha = g["sha"]
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
