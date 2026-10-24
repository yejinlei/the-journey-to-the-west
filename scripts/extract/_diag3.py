import json, os, urllib.request, subprocess
API_KEY = os.environ["SENSENOVA_API_KEY"]

# 用 subprocess 调 curl 验证 key 本身有效
cmd = [
    "curl.exe", "-sS", "-o", "-", "-w", "\nHTTP %{http_code}\n",
    "-H", "Authorization: Bearer " + API_KEY,
    "-H", "Content-Type: application/json",
    "-d", '{"model":"sensenova-6.8-flash-lite","messages":[{"role":"user","content":"hi"}],"max_tokens":10}',
    "https://token.sensenova.cn/v1/chat/completions",
]
print("=== curl via subprocess ===")
r = subprocess.run(cmd, capture_output=True, text=True)
print(r.stdout[:300])
print("stderr:", r.stderr[:300])

# 再试试 Python 用 socks 或者不用
print("\n=== urllib with Accept-Encoding ===")
req = urllib.request.Request(
    "https://token.sensenova.cn/v1/chat/completions",
    data=json.dumps({"model":"sensenova-6.8-flash-lite","messages":[{"role":"user","content":"hi"}],"max_tokens":10}).encode(),
    headers={
        "Authorization": "***" + API_KEY,
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Accept-Encoding": "gzip",
        "User-Agent": "python-urllib/3.11",
    },
    method="POST",
)
try:
    resp = urllib.request.urlopen(req, timeout=30)
    print("OK", resp.status)
except urllib.error.HTTPError as e:
    print("FAIL", e.code, e.read().decode()[:200])

# 打印 urllib 实际发送的 raw headers
print("\n=== raw bytes of request ===")
import io
class DumpHandler(urllib.request.HTTPSHandler):
    def do_open(self, http_class, req, **kwargs):
        print("METHOD:", req.get_method())
        print("URL:", req.full_url)
        for h, v in req.header_items():
            print(f"  {h}: {v!r}")
        print("  body:", req.data[:120])
        return super().do_open(http_class, req, **kwargs)

opener = urllib.request.build_opener(DumpHandler())
try:
    resp = opener.open(req, timeout=30)
    print("OK", resp.status)
except urllib.error.HTTPError as e:
    print("FAIL", e.code)
