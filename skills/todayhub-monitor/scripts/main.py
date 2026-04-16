#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TodayHub AI 新闻监控
抓取 tophub.today/topics?orderby=time，用 LLM 智能判断是否为"海外 AI 相关新闻"，
并将新条目推送到钉钉。
"""

import asyncio
import concurrent.futures as _cf
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

# ── 常量 ──────────────────────────────────────────────────────────────────────

TOPHUB_URL = "https://tophub.today/topics?orderby=time"
DEFAULT_TOP_N = 10
DEFAULT_SENT_FILE = "memory/sent.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# 兜底关键词（仅当 LLM 不可用时使用）
_FALLBACK_AI_KW = [
    "OpenAI", "Anthropic", "Claude", "Gemini", "Grok", "GPT", "ChatGPT",
    "NVIDIA", "英伟达", "黄仁勋", "DeepMind", "Meta AI", "Meta Llama",
    "xAI", "Mistral", "Cohere", "Runway", "Midjourney", "Stable Diffusion",
    "Sora", "LLM", "大模型", "AI", "人工智能",
]
_FALLBACK_DOMESTIC_KW = [
    "百度", "阿里", "腾讯", "华为", "字节", "DeepSeek", "Kimi", "智谱",
    "文心", "通义", "讯飞", "月之暗面", "零一万物", "MiniMax",
]


# ── 异步兼容 ──────────────────────────────────────────────────────────────────

def _run_async(coro):
    """在任意上下文（含 FastAPI 事件循环）中安全运行协程"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with _cf.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


# ── 抓取 ──────────────────────────────────────────────────────────────────────

def fetch_tophub_html() -> str:
    """抓取今日热榜话题页 HTML"""
    req = urllib.request.Request(TOPHUB_URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", errors="replace")


def parse_topics(html: str) -> list:
    """
    解析 HTML，提取话题条目。
    策略：
      1. 找所有 <div class="word"> 块，提取标题/摘要/时间
      2. 紧接其后找 <div class="react-doc-list">，提取第一个真实 URL
    """
    results = []
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    word_pattern = re.compile(
        r'<div class="word">\s*<h3>(?P<title>[^<]+)</h3>\s*'
        r'<div class="des">(?P<summary>[^<]*)</div>\s*'
        r'<div class="msg">.*?'
        r'<div class="time">(?P<time>[^<]+)</div>',
        re.S,
    )
    doc_link_pattern = re.compile(
        r'<a class="doc-title"\s+href="(?P<url>[^"]+)"[^>]*>',
        re.S,
    )

    matches = list(word_pattern.finditer(html))
    for i, m in enumerate(matches):
        title = m.group("title").strip()
        summary = m.group("summary").strip()
        pub_time = m.group("time").strip()

        seg_start = m.end()
        seg_end = matches[i + 1].start() if i + 1 < len(matches) else len(html)
        segment = html[seg_start:seg_end]

        real_url = ""
        for lm in doc_link_pattern.finditer(segment):
            url = lm.group("url")
            if url.startswith("http") and "tophub.today" not in url:
                real_url = url
                break

        if not real_url:
            continue

        results.append({
            "title": title,
            "summary": summary,
            "pub_time": pub_time,
            "url": real_url,
            "fetched_at": now_str,
            "sent": False,
        })

    return results


# ── LLM 智能过滤 ──────────────────────────────────────────────────────────────

_LLM_SYSTEM_PROMPT = """你是一个新闻分类助手。你的任务是判断给定的新闻条目是否属于"海外 AI 相关新闻"。

判断标准：
- ✅ 保留：主题涉及海外 AI 公司/研究机构/产品/技术进展（如 OpenAI、Anthropic、Google DeepMind、Meta AI、xAI、Mistral、NVIDIA、微软 Copilot、GitHub Copilot、AWS Bedrock 等）
- ✅ 保留：国际 AI 学术研究、大模型技术突破、AI 政策法规（来自欧盟/美国/国际组织）
- ✅ 保留：即使文章来源是中国媒体，只要内容主体是报道海外 AI 动态也保留
- ❌ 过滤：主题是中国本土 AI 公司/产品（百度、阿里、腾讯、华为、字节、DeepSeek、Kimi、智谱、文心、通义等）
- ❌ 过滤：股价、财报、投资、招聘、广告、促销等内容
- ❌ 过滤：与 AI 无关的新闻

回复格式：仅输出编号和 Y/N，每行一条，例如：
0: Y
1: N
2: Y
不要输出任何解释。"""


def llm_filter_ai_news(items: list, llm_provider) -> list:
    """
    用 LLM 批量判断每条新闻是否属于"海外 AI 相关"，一次调用搞定。
    返回通过过滤的条目列表。
    """
    if not items or llm_provider is None:
        return items

    from skill_service.llm.provider import LLMMessage

    # 构建输入文本
    lines = []
    for i, item in enumerate(items):
        title = item.get("title", "")
        summary = item.get("summary", "")
        text = f"{i}: 标题={title}；摘要={summary}"
        lines.append(text)

    user_content = "\n".join(lines)
    messages = [
        LLMMessage(role="system", content=_LLM_SYSTEM_PROMPT),
        LLMMessage(role="user", content=user_content),
    ]

    try:
        response = _run_async(llm_provider.chat(messages, max_tokens=512))
        if not (response and response.content):
            print("[LLM过滤] 无响应，降级到关键词过滤")
            return _fallback_filter(items)

        # 解析 "0: Y\n1: N\n..." 格式
        decisions = {}
        for line in response.content.strip().splitlines():
            m = re.match(r'^(\d+)\s*[:：]\s*([YyNn])', line.strip())
            if m:
                decisions[int(m.group(1))] = m.group(2).upper() == "Y"

        if not decisions:
            print(f"[LLM过滤] 解析失败，响应内容：{response.content[:200]}")
            return _fallback_filter(items)

        result = [item for i, item in enumerate(items) if decisions.get(i, False)]
        print(f"[LLM过滤] 共 {len(items)} 条 → LLM 保留 {len(result)} 条")
        return result

    except Exception as e:
        print(f"[LLM过滤] 调用失败: {e}，降级到关键词过滤")
        return _fallback_filter(items)


def _fallback_filter(items: list) -> list:
    """
    关键词兜底过滤（仅在 LLM 不可用时使用）。
    逻辑：命中 AI 关键词 且 未命中国内实体关键词。
    """
    result = []
    for item in items:
        text = (item.get("title", "") + " " + item.get("summary", "")).lower()
        has_ai = any(kw.lower() in text for kw in _FALLBACK_AI_KW)
        has_domestic = any(kw in (item.get("title", "") + item.get("summary", "")) for kw in _FALLBACK_DOMESTIC_KW)
        if has_ai and not has_domestic:
            result.append(item)
    print(f"[关键词兜底] 共 {len(items)} 条 → 保留 {len(result)} 条")
    return result


# ── 去重 ─────────────────────────────────────────────────────────────────────

def _ensure_dir(path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def load_sent_records(sent_file: str) -> dict:
    """加载去重记录"""
    if not sent_file or not os.path.exists(sent_file):
        return {}
    try:
        with open(sent_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return {url: {"status": "sent"} for url in data}
        return data
    except Exception:
        return {}


def save_sent_records(sent_file: str, records: dict):
    """保存去重记录"""
    if not sent_file:
        return
    _ensure_dir(sent_file)
    with open(sent_file, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def mark_as_sent(items: list, sent_file: str):
    """标记为已推送"""
    if not sent_file:
        return
    records = load_sent_records(sent_file)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for item in items:
        records[item["url"]] = {
            "status": "sent",
            "title": item["title"],
            "recorded_at": now_str,
        }
    save_sent_records(sent_file, records)


def filter_unsent(items: list, sent_file: str) -> tuple:
    """返回 (未推送列表, 所有记录dict)"""
    records = load_sent_records(sent_file)
    unsent = []
    for item in items:
        url = item["url"]
        if url not in records or records[url].get("status") != "sent":
            unsent.append(item)
    return unsent, records


# ── 格式化输出 ────────────────────────────────────────────────────────────────

def format_output(items: list, total_fetched: int, unseen_count: int, total_ai: int) -> str:
    """格式化为 Markdown"""
    if not items:
        return "## 今日热榜 AI 动态\n\n暂无新的 AI 相关新闻。"

    lines = [f"## 今日热榜 AI 动态（{len(items)} 条）\n"]
    seen_urls = set()
    idx = 1
    for item in items:
        url = item["url"]
        if url in seen_urls:
            continue
        seen_urls.add(url)
        lines.append(f"## {idx}.{item['title']}")
        if item.get("summary"):
            lines.append(f"**摘要**：{item['summary']}")
        lines.append(f"**时间**：{item['pub_time']}（抓取：{item['fetched_at']}）")
        lines.append(f"**链接**：[{url}]({url})")
        lines.append("")
        idx += 1

    lines.append(f"\n> 共抓取 {total_fetched} 条话题，未推送 {unseen_count} 条，经 LLM 过滤保留 {total_ai} 条，本次推送 {len(items)} 条。")

    return "\n".join(lines)


# ── 推送 ─────────────────────────────────────────────────────────────────────

def send_to_dingtalk(content: str, push_sender_path: str) -> bool:
    """通过 push_sender.py 推送到钉钉"""
    if not push_sender_path or not os.path.exists(push_sender_path):
        print(f"警告: push_sender.py 不存在: {push_sender_path}")
        return False
    try:
        result = subprocess.run(
            [sys.executable, push_sender_path],
            input=content,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            print("[钉钉] 推送成功")
            return True
        else:
            print(f"[钉钉] 推送失败: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"[钉钉] 推送异常: {e}")
        return False


# ── Skill 入口 ────────────────────────────────────────────────────────────────

def execute(params=None) -> dict:
    """
    Skill Service 标准入口

    params:
        top_n (int): 最多推送条数，默认 10
        sent_file (str): 去重记录文件（相对路径），默认 memory/sent.json
        push_to_dingtalk (bool): 是否推送到钉钉，默认 False
        push_sender (str): push_sender.py 相对路径，默认 ../../shared/push_sender.py
        dry_run (bool): 只输出不推送，默认 False
        model (str): 指定模型名（可选），默认使用系统当前配置
    """
    if params is None:
        params = {}

    try:
        top_n = int(params.get("top_n", DEFAULT_TOP_N))
        push_to_dingtalk = str(params.get("push_to_dingtalk", "false")).lower() == "true"
        dry_run = str(params.get("dry_run", "false")).lower() == "true"
        model_name = params.get("model")

        # 去重文件路径
        sent_file = params.get("sent_file", DEFAULT_SENT_FILE)
        if sent_file and not os.path.isabs(sent_file):
            skill_dir = Path(__file__).parent.parent
            sent_file = str(skill_dir / sent_file)

        # push_sender 路径
        push_sender_path = params.get("push_sender", "../../shared/push_sender.py")
        if push_sender_path and not os.path.isabs(push_sender_path):
            script_dir = Path(__file__).parent
            push_sender_path = str((script_dir / push_sender_path).resolve())

        # 初始化 LLM（可选）
        llm_provider = None
        try:
            from skill_service.llm.multi_model_config import get_multi_model_manager
            manager = get_multi_model_manager()
            llm_provider = manager.create_llm_provider(model=model_name)
            profile = manager.get_current_profile()
            print(f"[LLM] 使用模型: {profile.model if profile else 'unknown'}")
        except Exception as e:
            print(f"[LLM] 初始化失败，将使用关键词兜底: {e}")

        # Step 1: 抓取
        print(f"[step 1] 抓取 {TOPHUB_URL} ...")
        html = fetch_tophub_html()
        all_topics = parse_topics(html)
        print(f"[step 1] 共解析 {len(all_topics)} 条话题")

        # Step 2: 去重（先剔除已推送，只对新条目做 LLM 判断，节省用量）
        print("[step 2] 去重检查 ...")
        unseen, records = filter_unsent(all_topics, sent_file)
        print(f"[step 2] 未见过的新条目: {len(unseen)} 条")

        # Step 3: LLM 智能过滤（只判断新条目）
        print("[step 3] 过滤海外 AI 相关新闻 ...")
        ai_news = llm_filter_ai_news(unseen, llm_provider)
        print(f"[step 3] 保留 {len(ai_news)} 条")

        unsent = ai_news[:top_n]
        print(f"取前 {top_n} 条，实际推送: {len(unsent)} 条")

        # 格式化输出
        output = format_output(unsent, len(all_topics), len(unseen), len(ai_news))

        # Step 4: 推送
        if unsent and push_to_dingtalk and not dry_run:
            print("[step 4] 推送到钉钉 ...")
            ok = send_to_dingtalk(output, push_sender_path)
            if ok:
                mark_as_sent(unsent, sent_file)
                output += "\n\n✅ 已推送到钉钉"
            else:
                output += "\n\n⚠️ 推送钉钉失败（请检查 push_sender.py 配置）"
        elif dry_run:
            print("[step 4] dry_run 模式，跳过推送")
        elif not unsent:
            print("[step 4] 无符合条件的海外 AI 新闻，跳过推送")
        else:
            print("[step 4] push_to_dingtalk=false，跳过推送")

        return {
            "success": True,
            "output": output,
            "data": {
                "total_fetched": len(all_topics),
                "unseen": len(unseen),
                "ai_related": len(ai_news),
                "new_items": len(unsent),
                "items": [
                    {
                        "title": item["title"],
                        "url": item["url"],
                        "pub_time": item["pub_time"],
                        "fetched_at": item["fetched_at"],
                        "sent": push_to_dingtalk and not dry_run,
                    }
                    for item in unsent
                ],
            },
        }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "output": f"执行失败: {e}\n{traceback.format_exc()}",
            "data": None,
        }


# ── 命令行入口 ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="TodayHub AI 新闻监控")
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--push", action="store_true", help="推送到钉钉")
    parser.add_argument("--dry-run", action="store_true", help="只输出不推送")
    parser.add_argument("--sent-file", default=DEFAULT_SENT_FILE)
    parser.add_argument("--model", default=None, help="指定 LLM 模型名")
    args = parser.parse_args()

    result = execute({
        "top_n": args.top_n,
        "push_to_dingtalk": args.push,
        "dry_run": args.dry_run,
        "sent_file": args.sent_file,
        "model": args.model,
    })

    print(result["output"])
    if not result["success"]:
        sys.exit(1)
