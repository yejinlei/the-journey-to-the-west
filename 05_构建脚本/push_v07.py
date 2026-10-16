# -*- coding: utf-8 -*-
"""推送 v0.7（本体论 + 统一检索页）到 gh-pages + main。

策略：
  - main 分支：本地 git push（已包含 453 files changed 的完整变更）
  - gh-pages 分支：通过 GitHub Contents API 推 12 个页面 + ontology.json + 4 张关键 parquet

变更清单：
  - 新增：query.html（本体四层统一检索）、data/ontology.json
  - 修改：10 个页面导航（加"本体论"入口）+ index.html（加卡片）
  - 新增：语料 gubao / baihui_xiangzhu 各 100 回 txt + titles.json
  - 新增：05_构建脚本/export_ontology.py + 04_knowledge_data/vocabularies.yaml 修复
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
MSG = "feat(ontology, v0.7): 本体四层统一检索页 + 语料扩广 (gubao/baihui_xiangzhu 200 回)"

NAV_PAGES = [
    "index.html", "read.html", "compare.html", "query.html",
    "entities.html", "versions.html", "relics.html",
    "annotations.html", "events.html", "graph.html", "agent.html",
]

FILES = []
for p in NAV_PAGES:
    FILES.append((p, f"docs/{p}"))
FILES.append(("data/ontology.json", "docs/data/ontology.json"))
for pq in ["editions.parquet", "chapters.parquet", "lines.parquet", "pages.parquet"]:
    FILES.append((f"data/{pq}", f"docs/data/{pq}"))


def req(url, method="GET", data=None):
    headers = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json"}
    body = json.dumps(data).encode("utf-8") if data else None
    r = urllib.request.Request(url, headers=headers, data=body, method=method)
    if data:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=90) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"__error__": e.code, "__body__": e.read().decode("utf-8", "replace")[:400]}


def push_one(rel, local):
    branch = "gh-pages"
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
        print(f"  FAIL {rel}  ->  {code}  {body_msg}")
        return "fail"
    print(f"  ok   {rel}  ({len(b64)//1024} KB)  ->  {r['commit']['sha'][:7]}")
    return "ok"


def main():
    print("=== Phase 1: git push main（本地已 commit） ===")
    r = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
    print(r.stdout)
    if r.stderr:
        print(r.stderr)
    print(f"exit={r.returncode}\n")

    print("=== Phase 2: GitHub API push gh-pages ===")
    ok = fail = skip = 0
    for rel, local in FILES:
        r = push_one(rel, local)
        if r == "ok": ok += 1
        elif r == "skip": skip += 1
        else: fail += 1
        time.sleep(0.5)
    print(f"\nDone. ok={ok}  skip={skip}  fail={fail}")


if __name__ == "__main__":
    main()
