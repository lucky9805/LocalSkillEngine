#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI新闻推送脚本
- 将 Markdown 格式新闻内容存入本地数据库（POST /api/news/push）
- 同步发送到钉钉机器人
用于定时任务执行，两步互不阻塞，任意一步失败均会打印日志但不会影响另一步。
"""

import sys
import time
import re
import hmac
import hashlib
import base64
import urllib.parse
import urllib.request
import urllib.error
import json
import os

# ── 钉钉配置 ──────────────────────────────────────────────────────────────────
WEBHOOK_URL = (
    "https://oapi.dingtalk.com/robot/send?access_token=56f609661c4e0d05fbfe959958be62c402cbd52305a15dbfd124cd8eaafb2340"
)
SECRET = "SEC126c08438eb6b569b3769c90e6d99792567aac1e44523c900abe72759467834a"


##测试群的消息配置
# WEBHOOK_URL = (
#     "https://oapi.dingtalk.com/robot/send?access_token=15a345d488d062d89a7c17a67e6d6edc4c7ffbe918c3c3ecc0e60647271f192e"
# )
# SECRET = "SEC698f47c3973cc1af8693ae9b7845a2dabdbf397eaf541300b9b4c7c2f569457e"

# ── 本地 API 配置（通过环境变量覆盖）────────────────────────────────────────
LOCAL_API_URL = os.environ.get("LOCAL_API_URL", "https://timometric.tipost.com/api/news/push")
ENABLE_LOCAL_PUSH = os.environ.get("ENABLE_LOCAL_PUSH", "true").lower() == "true"

# ── Tipost Daily Scrape 配置（通过环境变量覆盖）──────────────────────────────
TIPOST_SCRAPE_URL = os.environ.get(
    "TIPOST_SCRAPE_URL",
    "https://agisignal-admin.tipost.com/api/daily/scrape",
)
TIPOST_API_KEY = os.environ.get("TIPOST_API_KEY", "AGISIG_PRD_5f7a")
TIPOST_API_SECRET = os.environ.get("TIPOST_API_SECRET", "sk_live_3c7e8f9a1b2d4e5f6a7b8c9")
ENABLE_TIPOST_SCRAPE = os.environ.get("ENABLE_TIPOST_SCRAPE", "true").lower() == "true"


# ── 工具函数 ──────────────────────────────────────────────────────────────────

def generate_sign() -> tuple:
    """生成钉钉加签，返回 (timestamp, sign)"""
    timestamp = str(round(time.time() * 1000))
    string_to_sign = "{}\n{}".format(timestamp, SECRET)
    hmac_code = hmac.new(
        SECRET.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return timestamp, sign


def _post_json(url: str, payload: dict, timeout: int = 30) -> dict:
    """通用 POST JSON 请求"""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post_json_with_headers(url: str, payload: dict, headers: dict, timeout: int = 30) -> dict:
    """带自定义 Header 的 POST JSON 请求"""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req_headers = {"Content-Type": "application/json"}
    req_headers.update(headers or {})
    req = urllib.request.Request(
        url,
        data=body,
        headers=req_headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read().decode("utf-8", errors="replace")
        if not data:
            return {"success": True}
        try:
            return json.loads(data)
        except Exception:
            return {"success": True, "raw": data}


# ── 核心功能 ──────────────────────────────────────────────────────────────────

DINGTALK_MAX_CHARS = 19000  # 钉钉 Markdown 单条限制约 20000，留 1000 余量


def _split_content(content: str, max_chars: int = DINGTALK_MAX_CHARS) -> list:
    """
    按新闻条目边界分割超长内容，保证每段不超过 max_chars 字符。
    优先按 '## N.' 标题行切割，避免截断单条新闻。
    """
    if len(content) <= max_chars:
        return [content]

    # 找所有条目起始位置（包括位置0作为第一个边界）
    boundaries = [0]
    for m in re.finditer(r"\n(?=##\s*\d+[\.\、])", content):
        boundaries.append(m.start() + 1)  # +1 跳过 \n

    parts = []
    seg_start = 0  # 当前段开始位置（在 boundaries 索引意义上）
    seg_len = 0

    for i in range(len(boundaries)):
        pos = boundaries[i]
        next_pos = boundaries[i + 1] if i + 1 < len(boundaries) else len(content)
        block_len = next_pos - pos

        if seg_len + block_len > max_chars and seg_len > 0:
            # 先把已积累的内容切出
            chunk = content[boundaries[seg_start]:pos].strip()
            if chunk:
                parts.append(chunk)
            seg_start = i
            seg_len = block_len
        else:
            seg_len += block_len

    # 最后一段
    last = content[boundaries[seg_start]:].strip()
    if last:
        parts.append(last)

    # 如果某段仍超限（单条正文极长），按字符硬切，保留尽量完整
    final_parts = []
    for part in parts:
        if len(part) <= max_chars:
            final_parts.append(part)
        else:
            for j in range(0, len(part), max_chars):
                final_parts.append(part[j:j + max_chars])

    return final_parts if final_parts else [content[:max_chars]]


def send_to_dingtalk(title: str, content: str) -> dict:
    """发送 Markdown 格式消息到钉钉机器人，超长自动分段"""
    parts = _split_content(content)
    total = len(parts)

    last_result = {"errcode": 0, "errmsg": "ok"}
    for idx, part in enumerate(parts, 1):
        part_title = title if total == 1 else f"{title}（{idx}/{total}）"
        timestamp, sign = generate_sign()
        url = f"{WEBHOOK_URL}&timestamp={timestamp}&sign={sign}"
        payload = {
            "msgtype": "markdown",
            "markdown": {"title": part_title, "text": part},
        }
        try:
            result = _post_json(url, payload)
            last_result = result
            if result.get("errcode") != 0:
                print(f"[dingtalk] 第 {idx}/{total} 段发送失败: {result.get('errmsg')}")
                return result
            print(f"[dingtalk] 第 {idx}/{total} 段发送成功")
            if idx < total:
                import time as _time
                _time.sleep(1)  # 避免触发频率限制
        except Exception as e:
            print(f"[dingtalk] 第 {idx}/{total} 段发送异常: {e}")
            return {"errcode": -1, "errmsg": str(e)}

    return last_result


def push_to_local_api(
    content: str,
    source: str = "dingtalk",
    category: str = "AI早报",
) -> dict:
    """
    将 Markdown 格式新闻内容推送到本地 API 入库。
    本地服务不可用时只打印警告，不影响钉钉发送。
    """
    if not ENABLE_LOCAL_PUSH:
        print("[local] 本地推送已禁用（ENABLE_LOCAL_PUSH=false）")
        return {"success": True, "message": "已禁用"}

    payload = {
        "source": source,
        "content": content,
        "category": category,
        "parse_markdown": True,
    }
    try:
        result = _post_json(LOCAL_API_URL, payload)
        saved = result.get("saved", 0)
        total = result.get("total", 0)
        print(f"[local] 推送成功: 共 {total} 条，新增 {saved} 条")
        return result
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[local] 推送失败 HTTP {e.code}: {body}")
        return {"success": False, "error": f"HTTP {e.code}"}
    except Exception as e:
        print(f"[local] 推送失败（服务可能未启动）: {e}")
        return {"success": False, "error": str(e)}


def push_to_tipost_scrape(content: str) -> dict:
    """
    将 Markdown 内容同步到 Tipost Daily Scrape 接口。
    失败只记录日志，不影响其它步骤。
    """
    if not ENABLE_TIPOST_SCRAPE:
        print("[tipost] daily/scrape 已禁用（ENABLE_TIPOST_SCRAPE=false）")
        return {"success": True, "message": "disabled"}

    payload = {"content": content}
    headers = {
        "X-API-Key": TIPOST_API_KEY,
        "X-API-Secret": TIPOST_API_SECRET,
    }
    try:
       # result = _post_json_with_headers(TIPOST_SCRAPE_URL, payload, headers=headers)
        result=""
        print("[tipost] daily/scrape 不同步")
        return result
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[tipost] daily/scrape 失败 HTTP {e.code}: {body}")
        return {"success": False, "error": f"HTTP {e.code}", "body": body}
    except Exception as e:
        print(f"[tipost] daily/scrape 同步失败: {e}")
        return {"success": False, "error": str(e)}


# ── 入口 ──────────────────────────────────────────────────────────────────────

def main():
    """
    从文件路径参数或标准输入读取内容，然后：
    1. 先推送到本地数据库
    2. 再发送钉钉消息

    用法：
        python push_sender.py news.md   # 从文件读取
        echo "内容" | python push_sender.py  # 从 stdin 读取
    """
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            content = file_path  # 直接把参数当内容（兼容旧用法）
    else:
        content = sys.stdin.read()

    if not content.strip():
        print("错误: 没有内容可发送")
        sys.exit(1)

    # Step 1 — 本地入库（失败不中断后续步骤）
    print("[step 1] 正在推送到本地数据库...")
    local_result = push_to_local_api(content)

    # Step 2 — Tipost daily/scrape（失败不中断后续步骤）
    print("[step 2] 正在同步 Tipost daily/scrape...")
    tipost_result = push_to_tipost_scrape(content)

    # Step 3 — 钉钉推送
    print("[step 3] 正在发送钉钉消息...")
    dd_result = send_to_dingtalk("AI新闻早报", content)

    if dd_result.get("errcode") == 0:
        print("[step 3] 钉钉发送成功 ✓")
    else:
        print(f"[step 3] 钉钉发送失败: {dd_result.get('errmsg')}")
        sys.exit(1)

    print("全部完成 ✓")


if __name__ == "__main__":
    main()
