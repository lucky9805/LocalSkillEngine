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
import hmac
import hashlib
import base64
import urllib.parse
import urllib.request
import urllib.error
import json
import os

# ── 钉钉配置 ──────────────────────────────────────────────────────────────────
# WEBHOOK_URL = (
#     "https://oapi.dingtalk.com/robot/send"
#     "?access_token=2ec68f2981f5a4776a959c3d2b2025964e936cb81015b572f929b893a19d501e"
# )
# SECRET = "SEC0218e8c8744d9e4ea4c7138be7dc2847a7ac4faad039e45d74efa72e96c985cf"

##测试群的消息配置
WEBHOOK_URL = (
    "https://oapi.dingtalk.com/robot/send?access_token=15a345d488d062d89a7c17a67e6d6edc4c7ffbe918c3c3ecc0e60647271f192e"
)
SECRET = "SEC698f47c3973cc1af8693ae9b7845a2dabdbf397eaf541300b9b4c7c2f569457e"

# ── 本地 API 配置（通过环境变量覆盖）────────────────────────────────────────
LOCAL_API_URL = os.environ.get("LOCAL_API_URL", "https://timometric.tipost.com/api/news/push")
ENABLE_LOCAL_PUSH = os.environ.get("ENABLE_LOCAL_PUSH", "true").lower() == "true"


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


# ── 核心功能 ──────────────────────────────────────────────────────────────────

def send_to_dingtalk(title: str, content: str) -> dict:
    """发送 Markdown 格式消息到钉钉机器人"""
    timestamp, sign = generate_sign()
    url = f"{WEBHOOK_URL}&timestamp={timestamp}&sign={sign}"
    payload = {
        "msgtype": "markdown",
        "markdown": {"title": title, "text": content},
    }
    try:
        result = _post_json(url, payload)
        return result
    except Exception as e:
        print(f"[dingtalk] 发送失败: {e}")
        return {"errcode": -1, "errmsg": str(e)}


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

    # Step 2 — 钉钉推送
    print("[step 2] 正在发送钉钉消息...")
    dd_result = send_to_dingtalk("AI新闻早报", content)

    if dd_result.get("errcode") == 0:
        print("[step 2] 钉钉发送成功 ✓")
    else:
        print(f"[step 2] 钉钉发送失败: {dd_result.get('errmsg')}")
        sys.exit(1)

    print("全部完成 ✓")


if __name__ == "__main__":
    main()
