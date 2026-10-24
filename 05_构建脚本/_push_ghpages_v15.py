"""把 main 上本次修复涉及的 19 个 docs/ 文件推送到 gh-pages 分支。"""
import base64, json, subprocess, time, urllib.error, urllib.parse, urllib.request, os

REPO = "yejinlei/the-journey-to-the-west"
TOKEN = subprocess.check_output(["gh", "auth", "token"]).decode().strip()
API = f"https://api.github.com/repos/{REPO}/contents"

def req(url, method="GET", data=None):
    headers = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json"}
    body = json.dumps(data).encode("utf-8") if data else None
    r = urllib.request.Request(url, headers=headers, data=body, method=method)
    if data: r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"__error__": e.code, "__body__": e.read().decode("utf-8", "replace")[:400]}

MSG = "fix(cache): bump SW v15 + read.json v=099 + toggle.js v=098"

FILES = [
    "agent.html", "annotations.html", "compare.html", "editions.html",
    "entities.html", "events.html", "graph.html", "index.html",
    "journey.html", "js/page.js", "motif.html", "query.html", "read.html",
    "relics.html", "sw.js", "symbols.html", "versions.html", "voice.html",
    "witmap.html",
]

ok = fail = 0
for rel in FILES:
    local = os.path.join("docs", rel.replace("/", os.sep))
    url = f"{API}/{urllib.parse.quote(rel, safe='/')}?ref=gh-pages"
    g = req(url)
    sha = None
    if "__error__" not in g:
        sha = g["sha"]
    else:
        print(f"  GET fail {rel}: {g['__error__']}")
    with open(local, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    body = {"message": MSG, "content": b64, "branch": "gh-pages"}
    if sha:
        body["sha"] = sha
    r = req(f"{API}/{urllib.parse.quote(rel, safe='/')}", method="PUT", data=body)
    if "__error__" in r:
        print(f"  FAIL PUT {rel} -> {r['__error__']} {r.get('__body__','')[:200]}")
        fail += 1
    else:
        print(f"  ok   gh-pages {rel} -> {r['commit']['sha'][:7]}")
        ok += 1
    time.sleep(0.4)

print(f"\nDone. ok={ok} fail={fail}")
