#!/usr/bin/env python3
"""
mock_server.py —— 西游记 Agent · 本地测试用 Mock OpenAI 兼容端点 + 静态文件服务
===============================================================================
用途：零真 Key 验证 LangGraph 完整流程。
- GET  /*      → 静态文件（index.html / js/* / css/* / lib/* / data/*）
- POST /v1/chat/completions → 一个"会调工具"的假模型：
    · 第一轮：根据关键词粗略判断意图并返回 tool_calls
    · 工具结果回来后：返回流式中文回答

仅用于本地测试，不要部署到公网。

启动：
    python mock_server.py 8000
    浏览器打开 http://localhost:8000
    在设置里填 baseUrl=http://localhost:8000/v1  model=mock  apiKey=任意值
"""
import json, sys, re, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

# 西游主要人名表
PERSONS = [
    '孙悟空', '孫悟空', '孫大聖', '孫行者', '孙行者', '齐天大圣', '行者',
    '唐僧', '唐三藏', '三藏',
    '八戒', '豬八戒',
    '沙僧', '沙和尚', '沙悟淨',
    '白骨精', '白骨夫人',
    '觀音', '观音',
    '玉帝', '玉皇',
    '太上老君', '老君',
    '菩提',
    '金剛', '金公',
]


def guess_tools(q):
    calls = []
    def add(name, args):
        calls.append({
            "id": f"call_{len(calls)+1}",
            "type": "function",
            "function": {"name": name, "arguments": json.dumps(args, ensure_ascii=False)}
        })

    n = q.lower()
    if any(k in q for k in ['总览', '统计', '有多少', '规模', '概况']):
        add('知识图谱总览', {}); return calls
    if any(k in q for k in ['版本比较', '版本差异', '不同版本']):
        add('版本比较', {}); return calls
    if any(k in q for k in ['三教', '佛教', '道教', '儒教', '佛道', '论理', '三家']):
        add('三教论理分析', {}); return calls
    if any(k in q for k in ['诙谐', '耍猴', '呆子', '阿弥陀佛', '念经', '插科打诨']):
        if '呆子' in q or '耍猴' in q: add('诙谐点查找', {'witType': 'monkey_mischief'})
        elif '阿彌陀佛' in q or '阿弥陀佛' in q: add('诙谐点查找', {'witType': 'tang_sutra'})
        else: add('诙谐点查找', {})
        return calls
    if any(k in q for k in ['法宝', '金箍棒', '紧箍', '芭蕉扇', '紫金葫芦', '如意']):
        kw = next((k for k in ['金箍棒', '紧箍', '芭蕉扇', '紫金葫芦'] if k in q), None)
        add('法宝查询', {'keyword': kw} if kw else {}); return calls
    if any(k in q for k in ['母题', '拜師', '拜师', '受戒', '變化', '变化', '结拜', '取经']):
        kw = next((k for k in ['拜師', '受戒', '變化', '结拜', '取经'] if k in q), '拜師')
        add('母题追踪', {'motif': kw}); return calls
    if any(k in q for k in ['语体', '口吻', '体例']):
        add('语体分析', {}); return calls
    if any(k in q for k in ['共现', '和.*一起', '谁和谁']):
        names = [n for n in PERSONS if n in q]
        if len(names) >= 2:
            add('人物共现', {'personA': names[0], 'personB': names[1]})
            return calls
    if any(k in q for k in ['事件', '情节', '战妖', '降妖']):
        kw = next((k for k in ['战妖', '降妖', '取经', '大闹'] if k in q), None)
        add('事件检索', {'keyword': kw} if kw else {}); return calls
    if any(k in q for k in ['关系', '谁拜', '师徒', '拜師', '弟子']):
        names = [n for n in PERSONS if n in q]
        add('关系链查询', {'person': names[0]} if names else {}); return calls
    if any(k in q for k in ['章节', '回目', '第']):
        m = re.search(r'第[一二三四五六七八九十百\d]+回', q)
        add('章节检索', {'chapter': m.group(0)} if m else {}); return calls
    # 单人画像
    names = [n for n in PERSONS if n in q]
    if names:
        add('人物画像', {'person': names[0]}); return calls
    add('知识图谱总览', {})
    return calls


MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".parquet": "application/octet-stream",
    ".br": "application/brotli",
    ".wasm": "application/wasm",
    ".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml",
    ".ico": "image/x-icon", ".woff2": "font/woff2",
    ".ttl": "text/turtle; charset=utf-8",
    ".yaml": "text/yaml; charset=utf-8", ".yml": "text/yaml; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("[mock] %s - %s\n" % (self.address_string(), fmt % args))

    def do_GET(self):
        u = urlparse(self.path)
        p = u.path
        if p == "/" or p == "":
            p = "/index.html"
        fp = (ROOT / p.lstrip("/")).resolve()
        try:
            fp.relative_to(ROOT)
        except ValueError:
            self.send_error(403); return
        if fp.is_dir():
            fp = fp / "index.html"
        if not fp.exists():
            self.send_error(404, f"not found: {p}"); return
        ext = fp.suffix.lower()
        self.send_response(200)
        self.send_header("Content-Type", MIME.get(ext, "application/octet-stream"))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        with open(fp, "rb") as f:
            self.wfile.write(f.read())

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type,Authorization")
        self.end_headers()

    def do_POST(self):
        u = urlparse(self.path)
        if not u.path.endswith("/chat/completions"):
            self.send_error(404); return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length)
        try:
            body = json.loads(raw.decode("utf-8"))
        except Exception:
            self.send_error(400, "bad json"); return
        msgs = body.get("messages") or []
        stream = bool(body.get("stream"))

        has_tool_result = any(m.get("role") == "tool" for m in msgs)
        user_q = ""
        for m in reversed(msgs):
            if m.get("role") == "user":
                user_q = m.get("content") or ""
                break

        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        if stream:
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self._stream_reply(has_tool_result, user_q, msgs)
        else:
            data = self._reply(has_tool_result, user_q, msgs)
            payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    def _reply(self, has_tool_result, user_q, msgs):
        if not has_tool_result:
            calls = guess_tools(user_q)
            return {
                "id": "chatcmpl-mock",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "mock",
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": None, "tool_calls": calls},
                    "finish_reason": "tool_calls",
                }],
            }
        tool_texts = []
        for m in msgs:
            if m.get("role") == "tool":
                try:
                    obj = json.loads(m.get("content") or "{}")
                    if isinstance(obj, dict) and obj.get("text"):
                        tool_texts.append(obj["text"][:500])
                except Exception:
                    pass
        answer = (
            "（本地 Mock 模型）已根据西游记知识图谱工具返回的结果整理如下：\n\n"
            + ("\n\n---\n\n".join(tool_texts) if tool_texts else "（工具未返回文本）")
            + "\n\n> 提示：这是本地 Mock 端点的固定回答。接入真实模型（如 OpenRouter 的 gpt-4o-mini）后自动启用多步推理与自然语言综合。"
        )
        return {
            "id": "chatcmpl-mock",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "mock",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": answer}, "finish_reason": "stop"}],
        }

    def _stream_reply(self, has_tool_result, user_q, msgs):
        def send(ev):
            self.wfile.write(("data: " + json.dumps(ev, ensure_ascii=False) + "\n\n").encode("utf-8"))
            self.wfile.flush()

        if not has_tool_result:
            calls = guess_tools(user_q)
            send({
                "id": "chatcmpl-mock", "object": "chat.completion.chunk",
                "created": int(time.time()), "model": "mock",
                "choices": [{"index": 0, "delta": {"role": "assistant", "content": None}, "finish_reason": None}]
            })
            tc_delta = [{
                "index": i, "id": c["id"], "type": "function",
                "function": {"name": c["function"]["name"], "arguments": c["function"]["arguments"]},
            } for i, c in enumerate(calls)]
            send({
                "id": "chatcmpl-mock", "object": "chat.completion.chunk",
                "created": int(time.time()), "model": "mock",
                "choices": [{"index": 0, "delta": {"tool_calls": tc_delta}, "finish_reason": None}]
            })
            send({
                "id": "chatcmpl-mock", "object": "chat.completion.chunk",
                "created": int(time.time()), "model": "mock",
                "choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls"}]
            })
            send("[DONE]")
            return

        # 工具回来：流式吐字
        tool_texts = []
        for m in msgs:
            if m.get("role") == "tool":
                try:
                    obj = json.loads(m.get("content") or "{}")
                    if isinstance(obj, dict) and obj.get("text"):
                        tool_texts.append(obj["text"][:800])
                except Exception:
                    pass

        reply = (
            "（本地 Mock 模型）已根据西游记知识图谱工具返回的结果整理如下：\n\n"
            + ("\n\n---\n\n".join(tool_texts) if tool_texts else "（工具未返回文本）")
            + "\n\n> 接入真实模型后可启用多步推理与自然语言综合。"
        )
        send({"id": "chatcmpl-mock", "object": "chat.completion.chunk", "created": int(time.time()), "model": "mock",
              "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]})
        for ch in reply:
            send({"id": "chatcmpl-mock", "object": "chat.completion.chunk", "created": int(time.time()), "model": "mock",
                  "choices": [{"index": 0, "delta": {"content": ch}, "finish_reason": None}]})
            time.sleep(0.005)
        send({"id": "chatcmpl-mock", "object": "chat.completion.chunk", "created": int(time.time()), "model": "mock",
              "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]})
        send("[DONE]")


def main():
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"[mock] 西游记 Agent 本地服务已启动：http://127.0.0.1:{PORT}")
    print(f"[mock]   静态文件根: {ROOT}")
    print(f"[mock]   Mock OpenAI 端点: http://127.0.0.1:{PORT}/v1/chat/completions")
    print(f"[mock]   浏览器打开 http://localhost:{PORT} ，")
    print(f"[mock]   设置中填 baseUrl=http://localhost:{PORT}/v1  model=mock  apiKey=任意值")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n[mock] 已停止。")

if __name__ == "__main__":
    main()
