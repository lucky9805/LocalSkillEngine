#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
硅谷 AI 新闻监控 - Skill Service 标准入口
"""

import os
import sys
import subprocess
from pathlib import Path
from skill_service.llm.multi_model_config import MultiModelConfigManager
from skill_service.llm.provider import LLMProvider

# 添加当前目录到 Python 路径
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from fetch_news import fetch_and_format


def send_to_dingtalk(content: str, push_sender_path: str = None) -> bool:
    """发送消息到钉钉
    
    Args:
        content: 消息内容
        push_sender_path: push_sender.py 脚本路径
    
    Returns:
        bool: 是否发送成功
    """
    if not push_sender_path:
        return False
    
    try:
        # 调用 push_sender.py
        result = subprocess.run(
            [sys.executable, push_sender_path, content],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return result.returncode == 0
    
    except Exception as e:
        print(f"发送钉钉失败: {e}")
        return False


def execute(params=None):
    """Skill Service 标准入口
    
    Args:
        params (dict): 参数
            - top_n (int, 可选): 返回前 N 条新闻，默认 10
            - hours (int, 可选): 过滤最近 N 小时的新闻，默认 24
            - sent_file (str, 可选): 已发送新闻记录文件路径，默认 "memory/sent.json"（开启去重）
            - push_to_dingtalk (bool, 可选): 是否推送到钉钉，默认 False
            - push_sender (str, 可选): push_sender.py 脚本路径，默认 "scripts/push_sender.py"
    
    Returns:
        dict: {
            "success": True/False,
            "output": "Markdown 格式的新闻列表",
            "data": {...统计数据}
        }
    """
    if params is None:
        params = {}
    
    try:
        # 解析参数
        top_n = int(params.get("top_n", 10))
        hours = int(params.get("hours", 24))
        translate = params.get("translate", True)
        push_to_dingtalk = params.get("push_to_dingtalk", False)
        
        # 创建 LLM provider（用于翻译）
        llm_provider = None
        if translate:
            try:
                model = params.get("model")
                config_manager = MultiModelConfigManager()
                llm_provider = config_manager.create_llm_provider(model)
            except Exception as e:
                print(f"创建 LLM provider 失败: {e}，将跳过翻译")
        
        # 默认开启去重，使用 memory/sent.json
        sent_file = params.get("sent_file", "memory/sent.json")
        
        # 如果 sent_file 是相对路径，转换为绝对路径（基于技能工作目录）
        if sent_file and not os.path.isabs(sent_file):
            skill_dir = Path(__file__).parent.parent
            sent_file = str(skill_dir / sent_file)
        
        # push_sender 路径（默认使用 shared 目录下的共享脚本）
        push_sender_path = params.get("push_sender", "../../shared/push_sender.py")
        if push_sender_path and not os.path.isabs(push_sender_path):
            # 基于 scripts 目录解析相对路径
            script_dir = Path(__file__).parent
            push_sender_path = str((script_dir / push_sender_path).resolve())
        
        # 如果 push_sender 不存在，重置为 None（避免报错）
        if push_sender_path and not os.path.exists(push_sender_path):
            print(f"警告: push_sender.py 不存在: {push_sender_path}")
            push_sender_path = None
        
        # 抓取新闻
        result = fetch_and_format(
            top_n=top_n,
            hours=hours,
            sent_file=sent_file,
            translate=translate,
            llm_provider=llm_provider
        )
        
        # 如果抓取成功且需要推送到钉钉
        if result.get("success") and push_to_dingtalk and result.get("output"):
            if send_to_dingtalk(result["output"], push_sender_path):
                result["output"] += "\n\n✅ 已推送到钉钉"
            else:
                result["output"] += "\n\n⚠️ 推送钉钉失败（请检查 push_sender.py 配置）"
        
        return result
    
    except Exception as e:
        return {
            "success": False,
            "output": f"执行失败: {str(e)}",
            "data": None
        }


if __name__ == "__main__":
    # 命令行测试入口
    import json
    
    # 读取 stdin 参数
    if not sys.stdin.isatty():
        params = json.load(sys.stdin)
    else:
        params = {}
    
    result = execute(params)
    
    # 输出结果
    print(result["output"])
    
    # 如果是 JSON 模式，返回完整结果
    if params.get("json_output"):
        print(json.dumps(result, ensure_ascii=False, indent=2))
