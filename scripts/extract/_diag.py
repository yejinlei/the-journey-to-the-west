import json, os, urllib.request, hashlib
API_KEY = os.environ["SENSENOVA_API_KEY"]
print("KEY len:", len(API_KEY))
print("KEY sha1:", hashlib.sha1(API_KEY.encode()).hexdigest()[:16])
print("KEY first6/last6:", API_KEY[:6], "...", API_KEY[-6:])

# 用与 curl 完全一致的字段集
body = json.dumps({
    "model": "sensenova-6.8-flash-lite",
    "messages": [{"role": "user", "content": "hi"}],
    "max_tokens": 10,
}).encode()
req = urllib.request.Request(
    "https://token.sensenova.cn/v1/chat/completions",
    data=body,
    headers={
        "Authorization": "***" + API_KEY,
        "Content-Type": "application/json",
        "User-Agent": "curl/8.4.0",
    },
    method="POST",
)
try:
    r = urllib.request.urlopen(req, timeout=30)
    print("OK", r.status, r.read().decode()[:300])
except Exception as e:
    print("FAIL", e)
    try:
        print("  body:", e.read().decode()[:300])
    except Exception:
        pass
