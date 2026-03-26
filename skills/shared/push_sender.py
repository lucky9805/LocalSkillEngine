#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
钉钉消息发送器
用法: python3 dingding_sender.py "消息内容"
或:   echo "消息内容" | python3 dingding_sender.py
"""

import sys
import time
import hmac
import hashlib
import base64
import urllib.parse
import urllib.request
import json

#带聪慧的群
#WEBHOOK_URL = "https://oapi.dingtalk.com/robot/send?access_token=d9b262492332c795d7c26b9417b8f0558d74978e5c5b76e85a17412c80bc796a"
#SECRET = "SEC98465c787288f3949581eab79282d7e0cff010e9a54389e96b52d2f9969141f9"

#正式
# WEBHOOK_URL = "https://oapi.dingtalk.com/robot/send?access_token=2ec68f2981f5a4776a959c3d2b2025964e936cb81015b572f929b893a19d501e"
# SECRET = "SEC0218e8c8744d9e4ea4c7138be7dc2847a7ac4faad039e45d74efa72e96c985cf"

#自己人的群
WEBHOOK_URL = "https://oapi.dingtalk.com/robot/send?access_token=15a345d488d062d89a7c17a67e6d6edc4c7ffbe918c3c3ecc0e60647271f192e"
SECRET = "SEC698f47c3973cc1af8693ae9b7845a2dabdbf397eaf541300b9b4c7c2f569457e"
def generate_sign():
    """生成钉钉加签"""
    timestamp = str(round(time.time() * 1000))
    secret_enc = SECRET.encode('utf-8')
    string_to_sign = '{}\n{}'.format(timestamp, SECRET)
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return timestamp, sign


def send_markdown(title: str, content: str) -> dict:
    """发送 Markdown 格式消息"""
    timestamp, sign = generate_sign()
    url = f"{WEBHOOK_URL}&timestamp={timestamp}&sign={sign}"
    
    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": content
        }
    }
    
    headers = {"Content-Type": "application/json; charset=utf-8"}
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))


def send_text(content: str) -> dict:
    """发送纯文本消息"""
    timestamp, sign = generate_sign()
    url = f"{WEBHOOK_URL}&timestamp={timestamp}&sign={sign}"
    
    data = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }
    
    headers = {"Content-Type": "application/json; charset=utf-8"}
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))


def main():
    # 从命令行参数或标准输入读取消息
    if len(sys.argv) > 1:
        message = sys.argv[1]
    elif not sys.stdin.isatty():
        message = sys.stdin.read().strip()
    else:
        print("用法: python3 dingding_sender.py \"消息内容\"")
        print("或:   echo \"消息内容\" | python3 dingding_sender.py")
        sys.exit(1)
    
    if not message:
        print("错误: 消息内容不能为空")
        sys.exit(1)
    
    # 检测是否为 Markdown 格式
    if message.startswith('#') or '**' in message or '- ' in message or '\n' in message:
        # 提取标题
        lines = message.split('\n')
        title = "AI新闻监控"
        for line in lines:
            if line.startswith('#'):
                title = line.lstrip('#').strip()[:20]
                break
        result = send_markdown(title, message)
    else:
        result = send_text(message)
    
    if result.get('errcode') == 0:
        print("发送成功")
    else:
        print(f"发送失败: {result}")
        sys.exit(1)


if __name__ == "__main__":
    main()
