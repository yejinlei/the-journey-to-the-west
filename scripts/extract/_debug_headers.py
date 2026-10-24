import json, os, urllib.request
API_KEY = os.environ["SENSENOVA_API_KEY"]
url = "https://token.sensenova.cn/v1/chat/completions"
payload = json.dumps({"model":"sensenova-6.8-flash-lite","messages":[{"role":"user","content":"hi"}],"max_tokens":10}).encode()
h1 = {"Authorization": "***" + API_KEY, "Content-Type": "application/json"}
h2 = {"authorization": "***" + API_KEY, "content-type": "application/json"}
for name, h in [("TitleCase", h1), ("lowercase", h2)]:
    try:
        r = urllib.request.Request(url, data=payload, headers=h, method="POST")
        print(name, "Request headers after urllib:", dict(r.headers))
        resp = urllib.request.urlopen(r, timeout=30)
        print(name, "->", resp.status)
    except Exception as e:
        print(name, "-> FAIL", e)
        if hasattr(e, "read"):
            print("  body:", e.read().decode()[:300])
