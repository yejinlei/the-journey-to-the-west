"""
浏览器冒烟测试：验证前端渲染、DuckDB 数据加载、Agent 问答全流程
"""
from playwright.sync_api import sync_playwright
import sys

URL = "http://127.0.0.1:8000/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 900})

    errors = []
    console_msgs = []
    failed_requests = []

    page.on("console", lambda m: console_msgs.append(f"[{m.type}] {m.text}"))
    page.on("pageerror", lambda e: errors.append(f"PAGE ERROR: {e}"))
    page.on("requestfailed", lambda r: failed_requests.append(f"{r.method} {r.url} → {r.failure}"))

    try:
        page.goto(URL, wait_until="networkidle", timeout=120000)
    except Exception as e:
        print(f"goto exception: {e}")

    page.wait_for_timeout(5000)

    # 检查数据库状态
    status = page.evaluate("() => document.querySelector('#dbStatus .status-text')?.textContent")
    mode = page.evaluate("() => document.querySelector('#modeBadge')?.textContent")
    welcome_stats = page.evaluate("() => document.querySelector('#welcomeStats')?.textContent?.trim()?.slice(0,200)")
    print(f"DB Status: {status!r}")
    print(f"Mode Badge: {mode!r}")
    print(f"Welcome Stats: {welcome_stats!r}")

    # 截图
    page.screenshot(path="scripts/smoke_initial.png", full_page=True)
    print("Screenshot: scripts/smoke_initial.png")

    # 尝试触发一次知识入口
    page.click('.nav-link[data-q="知识图谱总览"]')
    page.wait_for_timeout(8000)

    chat_msgs = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('#chatMessages .msg')).map(m => ({
            role: m.querySelector('.msg-role')?.textContent,
            body: m.querySelector('.msg-body')?.textContent?.slice(0, 300),
        }));
    }""")
    print(f"Chat messages after click: {chat_msgs}")

    page.screenshot(path="scripts/smoke_after_query.png", full_page=True)

    print("\n=== Console Messages ===")
    for m in console_msgs[-40:]:
        print(m)
    print("\n=== Page Errors ===")
    for e in errors:
        print(e)
    print("\n=== Failed Requests ===")
    for r in failed_requests[-20:]:
        print(r)

    browser.close()
