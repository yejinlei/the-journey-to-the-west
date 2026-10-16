# -*- coding: utf-8 -*-
"""推送 v0.6（compare.html 评点对照页 + 全站导航）到 gh-pages + main。

- 新增：compare.html（N 源交集自动，回章级并置）
- 导航：10 个已有页面加"评点对照"入口
- 22 次 PUT：11 文件 × 2 分支
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
MSG = "feat(compare, v0.6): 评点对照页（N 源交集自动，回章级并置）+ 全站导航"

# 每个文件（branch, repo_rel, local_path）
NAV_PAGES = [
    "index.html", "read.html", "compare.html",
    "entities.html", "versions.html", "relics.html",
    "annotations.html", "events.html", "graph.html", "agent.html",
]

FILES = []
# gh-pages 分支（根目录）
for p in NAV_PAGES:
    FILES.append(("gh-pages", p, f"docs/{p}"))
# main 分支（docs/ 目录）
for p in NAV_PAGES:
    FILES.append(("main", f"docs/{p}", f"docs/{p}"))


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
    # 按 branch 分组，串行推
    ok = fail = skip = 0
    current_branch = None
    for branch, rel, local in FILES:
        if branch != current_branch:
            current_branch = branch
        r = push_one(branch, rel, local)
        if r == "ok": ok += 1
        elif r == "skip": skip += 1
        else: fail += 1
        time.sleep(0.6)
    print(f"\nDone. ok={ok}  skip={skip}  fail={fail}")


if __name__ == "__main__":
    main()
