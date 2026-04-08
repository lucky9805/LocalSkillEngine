#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from fetch_grok_papers import fetch_and_format


def _to_bool(v, default=True):
    if isinstance(v, bool):
        return v
    if v is None:
        return default
    return str(v).lower() in ("1", "true", "yes", "y")


def send_via_push_sender(content: str, push_sender_path: str) -> bool:
    if not push_sender_path or not os.path.exists(push_sender_path):
        print(f"[push] push_sender.py 不存在: {push_sender_path}")
        return False

    try:
        result = subprocess.run(
            [sys.executable, push_sender_path],
            input=content,
            capture_output=True,
            text=True,
            timeout=90,
        )
        if result.returncode == 0:
            print(f"[push] 推送成功\n{result.stdout.strip()}")
            return True
        print(f"[push] 推送失败(exit={result.returncode})\n{result.stderr.strip()}")
        return False
    except Exception as e:
        print(f"[push] 调用异常: {e}")
        return False


def execute(params=None):
    if params is None:
        params = {}

    try:
        fetch_timeout = int(params.get("fetch_timeout", 300))
        push_to_dingtalk = _to_bool(params.get("push_to_dingtalk", True), True)

        push_sender_raw = params.get("push_sender", "../../shared/push_sender.py")
        if push_sender_raw and not os.path.isabs(push_sender_raw):
            push_sender_path = str((SCRIPT_DIR / push_sender_raw).resolve())
        else:
            push_sender_path = push_sender_raw

        result = fetch_and_format(fetch_timeout=fetch_timeout)
        if not result.get("success"):
            raw_text = (result.get("raw") or "").strip()
            raw_preview = raw_text[:600] if raw_text else ""
            return {
                "success": False,
                "output": result.get("output", "执行失败"),
                "data": {
                    "pushed": False,
                    "raw_length": len(raw_text),
                    "raw_preview": raw_preview,
                },
            }

        output = result["output"]
        pushed = False
        if push_to_dingtalk:
            pushed = send_via_push_sender(output, push_sender_path)
            output += "\n\n✅ 已推送" if pushed else "\n\n⚠️ 推送失败"

        return {
            "success": True,
            "output": output,
            "data": {
                "pushed": pushed,
                "raw_length": len(result.get("raw", "")),
                "output_length": len(result.get("output", "")),
            },
        }
    except Exception as e:
        return {"success": False, "output": f"执行失败: {e}", "data": None}


if __name__ == "__main__":
    if not sys.stdin.isatty():
        try:
            params = json.load(sys.stdin)
        except Exception:
            params = {}
    else:
        params = {}

    result = execute(params)
    print(result["output"])

    if params.get("json_output"):
        print(json.dumps(result, ensure_ascii=False, indent=2))
