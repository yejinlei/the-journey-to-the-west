import json, os, urllib.request
API_KEY = os.environ["SENSENOVA_API_KEY"]

req = urllib.request.Request(
    "https://token.sensenova.cn/v1/chat/completions",
    data=b'{"model":"sensenova-6.8-flash-lite","messages":[{"role":"user","content":"hi"}],"max_tokens":10}',
    headers={"Authorization": "***" + API_KEY, "Content-Type": "application/json"},
    method="POST",
)
print("=== urllib default UA ===")
print(dict(req.headers))
try:
    r = urllib.request.urlopen(req, timeout=30)
    print("OK", r.status)
except urllib.error.HTTPError as e:
    print("FAIL", e.code, e.read().decode()[:200])

# 加个自定义 UA 试试
req2 = urllib.request.Request(
    "https://token.sensenova.cn/v1/chat/completions",
    data=b'{"model":"sensenova-6.8-flash-lite","messages":[{"role":"user","content":"hi"}],"max_tokens":10}',
    headers={
        "Authorization": "***" + API_KEY,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
    },
    method="POST",
)
print("\n=== with UA+Accept ===")
print(dict(req2.headers))
try:
    r = urllib.request.urlopen(req2, timeout=30)
    print("OK", r.status)
except urllib.error.HTTPError as e:
    print("FAIL", e.code, e.read().decode()[:200])

# 试试 requests
print("\n=== via requests ===")
try:
    import requests
    r = requests.post(
        "https://token.sensenova.cn/v1/chat/completions",
        headers={"Authorization": "***" + API_KEY, "Content-Type": "application/json"},
        json={"model": "sensenova-6.8-flash-lite", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 10},
        timeout=30,
    )
    print("OK", r.status_code, r.text[:200])
except ImportError:
    print("requests 未安装")
except Exception as e:
    print("FAIL", e)
