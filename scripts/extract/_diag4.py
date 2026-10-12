import os, requests, subprocess
API_KEY = os.environ["SENSENOVA_API_KEY"]
URL = "https://token.sensenova.cn/v1/chat/completions"
payload = {"model":"sensenova-6.8-flash-lite","messages":[{"role":"user","content":"hi"}],"max_tokens":10}

# 1) requests with curl-like UA
print("=== requests with curl UA ===")
r = requests.post(URL, headers={
    "Authorization": "***" + API_KEY,
    "Content-Type": "application/json",
    "User-Agent": "curl/8.4.0",
    "Accept": "*/*",
}, json=payload, timeout=30)
print("status:", r.status_code, "body:", r.text[:200])

# 2) requests with NO user-agent
print("\n=== requests with no UA ===")
headers = {"Authorization": "***" + API_KEY, "Content-Type": "application/json"}
requests.utils.default_headers()["User-Agent"] = ""
r = requests.post(URL, headers=headers, json=payload, timeout=30)
print("status:", r.status_code, "body:", r.text[:200])

# 3) subprocess curl
print("\n=== subprocess curl ===")
import json as J
p = subprocess.run([
    "curl.exe", "-sS",
    "-H", "Authorization: Bearer " + API_KEY,
    "-H", "Content-Type: application/json",
    "-d", J.dumps(payload),
    URL,
], capture_output=True, text=True)
print("rc:", p.returncode, "out:", p.stdout[:200], "err:", p.stderr[:200])

# 4) requests, but set UA to empty via session
print("\n=== requests with empty UA via PreparedRequest ===")
s = requests.Session()
req = requests.Request("POST", URL, headers={"Authorization": "***" + API_KEY, "Content-Type": "application/json"}, json=payload)
prepped = s.prepare_request(req)
print("headers:", dict(prepped.headers))
r = s.send(prepped, timeout=30)
print("status:", r.status_code, "body:", r.text[:200])
