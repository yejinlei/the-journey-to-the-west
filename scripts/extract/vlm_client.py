#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SenseNova VLM 客户端（通过 curl.exe 通道）。

为什么走 curl：token.sensenova.cn 的网关识别 Python HTTP 客户端（urllib / requests）
并返回 401 Forbidden；curl.exe 直连可以正常拿到 200。因此所有 VLM 调用通过
subprocess 调 curl.exe 完成。

配置（环境变量）：
  SENSENOVA_API_KEY       必填
  SENSENOVA_BASE_URL      默认 https://token.sensenova.cn/v1
  SENSENOVA_MODEL         默认 sensenova-6.8-flash-lite
  VLM_CURL_PATH           默认 curl.exe
"""
import base64
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_BASE_URL = "https://token.sensenova.cn/v1"
DEFAULT_MODEL = "sensenova-6.8-flash-lite"

BASE_URL = os.environ.get("SENSENOVA_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
MODEL = os.environ.get("SENSENOVA_MODEL", DEFAULT_MODEL)
API_KEY = os.environ.get("SENSENOVA_API_KEY", "")
CURL = os.environ.get("VLM_CURL_PATH", "curl.exe")

# 传给 VLM 前 resize，节省体积与传输时间
MAX_INLINE_SIDE = 1600
JPEG_QUALITY = 92


def encode_image(path):
    """返回 base64 编码（必要时先降采样到 MAX_INLINE_SIDE）。"""
    path = Path(path)
    raw = path.read_bytes()
    try:
        from PIL import Image
        import io
        with Image.open(path) as im:
            im = im.convert("RGB")
            w, h = im.size
            if max(w, h) > MAX_INLINE_SIDE:
                scale = MAX_INLINE_SIDE / max(w, h)
                im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
            raw = buf.getvalue()
    except Exception:
        pass  # Pillow 不可用则原样上传
    return base64.b64encode(raw).decode("ascii")


def _text_image_uri(image_path):
    ext = Path(image_path).suffix.lower().lstrip(".")
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}.get(ext, "jpeg")
    return f"data:image/{mime};base64,{encode_image(image_path)}"


def _build_messages(messages):
    """把 messages 里的 image_paths 展开成 OpenAI 多模态结构。"""
    out = []
    for m in messages:
        role = m["role"]
        content = m.get("content")
        if isinstance(content, str):
            out.append({"role": role, "content": content})
            continue
        if isinstance(content, dict) and "image_paths" in content:
            parts = []
            if content.get("text"):
                parts.append({"type": "text", "text": content["text"]})
            for p in content["image_paths"]:
                parts.append({"type": "image_url",
                              "image_url": {"url": _text_image_uri(p), "detail": "high"}})
            out.append({"role": role, "content": parts})
        else:
            out.append({"role": role, "content": content})
    return out


def vlm_chat(messages, temperature=0.1, max_tokens=4000, timeout=180, retries=3):
    """通过 curl.exe 调 /chat/completions，返回 assistant 文本内容。

    注意：sensenova-6.8-flash-lite 是推理型模型，reasoning 会先消耗一部分
    completion_tokens。max_tokens 太小会导致 content 为空；OCR 场景 4000
    已够，若返回空则加大到 8000 再试。
    """
    if not API_KEY:
        raise RuntimeError("未设置 SENSENOVA_API_KEY")
    url = BASE_URL + "/chat/completions"
    body = json.dumps({
        "model": MODEL,
        "messages": _build_messages(messages),
        "temperature": temperature,
        "max_tokens": max_tokens,
    }, ensure_ascii=False)

    last_err = None
    for attempt in range(1, retries + 1):
        tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        try:
            tmp.write(body)
            tmp.close()
            cmd = [CURL, "-sS", "--max-time", str(timeout),
                   "-H", "Authorization: Bearer " + API_KEY,
                   "-H", "Content-Type: application/json",
                   "--data-binary", "@" + tmp.name,
                   url]
            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
            if r.returncode != 0:
                raise RuntimeError(f"curl 退出码 {r.returncode}: {r.stderr[:300]}")
            data = json.loads(r.stdout)
            if "error" in data:
                raise RuntimeError("API error: " + json.dumps(data["error"], ensure_ascii=False))
            if "choices" in data and data["choices"]:
                msg = data["choices"][0].get("message", {})
                return msg.get("content") or ""
            return json.dumps(data, ensure_ascii=False)
        except Exception as e:
            last_err = e
            print(f"    VLM 失败({attempt}/{retries}): {e}", flush=True)
        finally:
            try:
                os.unlink(tmp.name)
            except OSError:
                pass
        time.sleep(min(2 ** attempt, 30))
    raise last_err


# 便捷构造
def text_messages(system, user_text):
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_text},
    ]


def image_messages(system, user_text, image_paths, labels=None):
    """多模态消息：user 消息里带文本 + 若干张图。"""
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": {
            "text": user_text,
            "image_paths": image_paths,
        }},
    ]


def text_only(text):
    """兼容旧调用风格：返回单条 user 消息 dict。"""
    return [{"role": "user", "content": text}]


if __name__ == "__main__":
    if not os.environ.get("SENSENOVA_API_KEY"):
        print("请先设置 SENSENOVA_API_KEY", file=sys.stderr)
        sys.exit(1)
    r = vlm_chat(text_messages("You are helpful.", "只回复两个字：正常"),
                 max_tokens=50, timeout=60)
    print("VLM 冒烟返回:", repr(r[:200]))
