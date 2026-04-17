#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行业资讯监控（新消费 / 3C电子 / 汽车）
多源 RSS 抓取 → 24h 过滤 → URL去重 → LLM智能分类 → 分领域输出 → 钉钉推送
"""

import asyncio
import concurrent.futures as _cf
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Optional

# ── 常量 ──────────────────────────────────────────────────────────────────────

DEFAULT_TOP_N = 20
DEFAULT_HOURS = 24
DEFAULT_SENT_FILE = "memory/sent.json"

# RSS 数据源（各领域主要来源）
RSS_SOURCES = {
    "新消费": [
        {"name": "36kr",    "url": "https://36kr.com/feed"},
        {"name": "第一财经", "url": "https://www.yicai.com/feed"},
    ],
    "3C电子": [
        {"name": "IT之家",  "url": "https://www.ithome.com/rss/"},
        {"name": "爱范儿",  "url": "https://www.ifanr.com/feed"},
    ],
    "汽车": [
        # 汽车之家、太平洋汽车、虎嗅等 RSS 均已下线
        # IT之家 综合 RSS 包含大量汽车资讯（新车/电动车/行业），36kr 也有汽车内容
        # LLM 会将汽车相关条目路由到"汽车"领域
        {"name": "IT之家",  "url": "https://www.ithome.com/rss/"},
        {"name": "36kr",    "url": "https://36kr.com/feed"},
    ],
}

# 目标领域
ALL_DOMAINS = ["新消费", "3C电子", "汽车"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*;q=0.1",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

NS = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc":      "http://purl.org/dc/elements/1.1/",
}


# ── 数据模型 ──────────────────────────────────────────────────────────────────

@dataclass
class NewsItem:
    title: str
    link: str
    pub_time: str       # 原始字符串
    pub_dt: datetime    # 解析后 datetime（UTC 或本地）
    source: str         # 来源名称
    source_domain: str  # 来源域名
    summary: str = ""
    domain: str = ""    # LLM 分类后的领域

    def time_cutoff(self, hours: int, now: datetime) -> bool:
        """判断是否在时间窗口内"""
        delta = now - self.pub_dt
        # pub_dt 如果是 naive datetime，当作本地时间处理
        if self.pub_dt.tzinfo is None:
            delta = now.replace(tzinfo=None) - self.pub_dt
        return abs(delta.total_seconds()) <= hours * 3600


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


# ── RSS 抓取 ─────────────────────────────────────────────────────────────────

def _extract_domain(url: str) -> str:
    """从 URL 提取域名"""
    m = re.match(r'https?://([^/]+)', url)
    return m.group(1) if m else ""


def _fetch_one_feed(source: dict, timeout: int = 15) -> list[NewsItem]:
    """抓取单个 RSS 源，返回 NewsItem 列表"""
    url = source["url"]
    name = source["name"]
    items = []
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
        channel = root.find("channel")
        if channel is None:
            return items

        for entry in channel.findall("item"):
            title = (entry.findtext("title") or "").strip()
            link  = (entry.findtext("link")  or "").strip()
            if not title or not link:
                continue
            pub_raw = entry.findtext("pubDate") or entry.findtext("dc:date") or ""
            desc    = (entry.findtext("description") or "").strip()
            # 去掉 HTML 标签
            desc = re.sub(r'<[^>]+>', '', desc)
            desc = desc[:200]  # 截断

            # 解析时间
            pub_dt = None
            if pub_raw:
                try:
                    pub_dt = parsedate_to_datetime(pub_raw)
                except Exception:
                    pass
            if pub_dt is None:
                pub_dt = datetime.now(timezone.utc)

            items.append(NewsItem(
                title=title,
                link=link,
                pub_time=pub_raw[:16] if pub_raw else "",
                pub_dt=pub_dt,
                source=name,
                source_domain=_extract_domain(url),
                summary=desc,
            ))
        print(f"  ✓ {name}: {len(items)} 条")
    except Exception as e:
        print(f"  ✗ {name}: {e}")
    return items


def fetch_all_sources(sources: list[dict], timeout: int = 15) -> list[NewsItem]:
    """并行抓取所有 RSS 源"""
    print(f"抓取 {len(sources)} 个 RSS 源 ...")
    all_items = []
    for source in sources:
        items = _fetch_one_feed(source, timeout)
        all_items.extend(items)
    return all_items


def fetch_by_domains(domains: list[str]) -> list[NewsItem]:
    """按指定领域抓取所有相关 RSS 源（URL 去重避免重复抓取）"""
    seen_urls = set()
    unique_sources = []
    for d in domains:
        if d in RSS_SOURCES:
            for s in RSS_SOURCES[d]:
                if s["url"] not in seen_urls:
                    seen_urls.add(s["url"])
                    unique_sources.append(s)
    return fetch_all_sources(unique_sources)


# ── 时间窗口 & URL 去重 ──────────────────────────────────────────────────────

def filter_by_window(items: list[NewsItem], hours: int) -> list[NewsItem]:
    """过滤出指定时间窗口内的条目"""
    now = datetime.now(timezone.utc)
    result = [it for it in items if it.time_cutoff(hours, now)]
    print(f"时间窗口（{hours}h）：{len(items)} → {len(result)} 条")
    return result


def deduplicate_by_url(items: list[NewsItem]) -> list[NewsItem]:
    """URL 去重，保留第一条"""
    seen = set()
    result = []
    for it in items:
        if it.link not in seen:
            seen.add(it.link)
            result.append(it)
    print(f"URL去重：{len(items)} → {len(result)} 条")
    return result


# ── LLM 智能分类 ─────────────────────────────────────────────────────────────

_LLM_CLASSIFY_PROMPT = """你是一个新闻分类助手。请判断每条新闻属于哪个领域。

分类标准：
- **新消费**：新零售、电商、品牌营销、消费趋势、生活方式、文旅、餐饮、美妆等
- **3C电子**：手机、电脑、平板、笔记本、数码产品、智能硬件、智能家居、可穿戴设备、芯片等
- **汽车**：新车发布、汽车行业动态、电动车、自动驾驶、车企动态、汽车技术等
- **无关**：上述三个领域以外的内容（如政治、体育、娱乐、游戏、教育、医疗等）

回复格式：仅输出编号和领域名，每行一条，例如：
0: 新消费
1: 3C电子
2: 汽车
3: 无关
不要输出任何解释。"""

_LLM_FILTER_PROMPT = """以下是一批新闻条目（标题+摘要），请判断每条是否属于「新消费」「3C电子」「汽车」三个领域之一。

判断标准：
- ✅ 保留：新消费、3C电子、汽车相关的行业资讯、产品动态、技术趋势、市场分析
- ❌ 过滤：娱乐八卦、游戏电竞、政治新闻、教育培训、医疗健康、金融股市（纯财经，非行业分析）等无关内容
- ⚠️ 注意：金融机构的 AI/数字化转型新闻（如银行用 AI、风控升级）属于汽车/3C的边缘，若新闻主体是金融行业本身则过滤，若主体是技术/产品应用则保留

回复格式：仅输出编号和 Y/N，每行一条，例如：
0: Y
1: N
2: Y
不要输出任何解释。"""


def llm_classify(items: list[NewsItem], llm_provider) -> list[NewsItem]:
    """
    用 LLM 对每条新闻进行领域分类。
    返回带 domain 字段的 NewsItem 列表。
    """
    if not items or llm_provider is None:
        # 降级：不做分类，全部归入第一领域
        return items

    from skill_service.llm.provider import LLMMessage

    # 构造输入
    lines = []
    for i, it in enumerate(items):
        text = f"{i}: 标题={it.title}；摘要={it.summary[:100]}"
        lines.append(text)

    messages = [
        LLMMessage(role="system", content=_LLM_FILTER_PROMPT),
        LLMMessage(role="user", content="\n".join(lines)),
    ]

    try:
        response = _run_async(llm_provider.chat(messages, max_tokens=512))
        if not (response and response.content):
            return items

        decisions = {}
        for line in response.content.strip().splitlines():
            m = re.match(r'^(\d+)\s*[:：]\s*([YyNn])', line.strip())
            if m:
                decisions[int(m.group(1))] = m.group(2).upper() == "Y"

        if not decisions:
            return items

        result = [it for i, it in enumerate(items) if decisions.get(i, False)]
        print(f"[LLM分类] 共 {len(items)} 条 → 保留 {len(result)} 条")
        return result

    except Exception as e:
        print(f"[LLM分类] 调用失败: {e}，跳过分类")
        return items


def llm_assign_domain(items: list[NewsItem], llm_provider) -> list[NewsItem]:
    """
    用 LLM 为已过滤的条目分配具体领域标签。
    如果有 domains 参数限定范围，优先分配到限定域。
    """
    if not items or llm_provider is None:
        for it in items:
            it.domain = "综合"
        return items

    from skill_service.llm.provider import LLMMessage

    lines = []
    for i, it in enumerate(items):
        text = f"{i}: 标题={it.title}；摘要={it.summary[:100]}"
        lines.append(text)

    messages = [
        LLMMessage(role="system", content=_LLM_CLASSIFY_PROMPT),
        LLMMessage(role="user", content="\n".join(lines)),
    ]

    try:
        response = _run_async(llm_provider.chat(messages, max_tokens=512))
        if not (response and response.content):
            return items

        domain_map = {}
        for line in response.content.strip().splitlines():
            m = re.match(r'^(\d+)\s*[:：]\s*(新消费|3C电子|汽车|无关)', line.strip())
            if m:
                domain_map[int(m.group(1))] = m.group(2)

        for i, it in enumerate(items):
            it.domain = domain_map.get(i, "综合")
        return items

    except Exception as e:
        print(f"[LLM领域分配] 调用失败: {e}")
        for it in items:
            it.domain = "综合"
        return items


# ── 去重（已推送记录）─────────────────────────────────────────────────────────

def _ensure_dir(path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def load_sent_records(sent_file: str) -> dict:
    """加载已推送记录"""
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
    """保存已推送记录"""
    if not sent_file:
        return
    _ensure_dir(sent_file)
    with open(sent_file, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def mark_as_sent(items: list[NewsItem], sent_file: str):
    """标记为已推送"""
    if not sent_file:
        return
    records = load_sent_records(sent_file)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for it in items:
        records[it.link] = {
            "status": "sent",
            "title": it.title,
            "domain": it.domain,
            "source": it.source,
            "recorded_at": now_str,
        }
    save_sent_records(sent_file, records)


def filter_unsent(items: list[NewsItem], sent_file: str) -> list[NewsItem]:
    """剔除已推送条目"""
    records = load_sent_records(sent_file)
    result = [it for it in items if it.link not in records]
    dropped = len(items) - len(result)
    if dropped:
        print(f"去重（已推送）：{len(items)} → {len(result)} 条（剔除 {dropped} 条）")
    return result


# ── 格式化输出 ────────────────────────────────────────────────────────────────

def _time_ago(pub_dt: datetime) -> str:
    """计算相对时间"""
    now = datetime.now(timezone.utc)
    if pub_dt.tzinfo is None:
        pub_dt = pub_dt.replace(tzinfo=timezone.utc)
    delta = now - pub_dt
    total = abs(delta.total_seconds())
    if total < 3600:
        return f"{int(total / 60)}分钟前"
    if total < 86400:
        return f"{int(total / 3600)}小时前"
    return f"{int(total / 86400)}天前"


def format_output(grouped: dict[str, list[NewsItem]], total: int, hours: int) -> str:
    """按领域分组格式化 Markdown"""
    if not grouped or all(not v for v in grouped.values()):
        return f"## 行业资讯日报\n\n在过去 {hours} 小时内暂无符合条件的资讯。"

    sections = []
    for domain in ALL_DOMAINS:
        items = grouped.get(domain, [])
        if not items:
            continue
        lines = [f"## 【{domain}】今日资讯（{len(items)} 条）\n"]
        for i, it in enumerate(items, 1):
            ago = _time_ago(it.pub_dt)
            lines.append(f"**{i}. {it.title}**")
            if it.summary:
                lines.append(f"   > {it.summary[:120]}...")
            lines.append(f"   - 来源：{it.source} · {ago}")
            lines.append(f"   - 链接：[{it.link}]({it.link})")
            lines.append("")
        sections.append("\n".join(lines))

    header = f"## 行业资讯日报（过去 {hours} 小时）\n"
    total_items = sum(len(v) for v in grouped.values())
    footer = f"\n> 共抓取 {total} 条，经去重/过滤保留 {total_items} 条。"
    return header + "\n\n".join(sections) + footer


# ── 推送 ─────────────────────────────────────────────────────────────────────

def send_to_dingtalk(content: str, push_sender_path: str) -> bool:
    """通过 push_sender.py 推送到钉钉"""
    if not push_sender_path or not os.path.exists(push_sender_path):
        print(f"警告: push_sender_xiaofei.py 不存在: {push_sender_path}")
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
        top_n (int): 每领域最多推送条数，默认 20
        hours (int): 抓取时间窗口（小时），默认 24
        domains (str): 监控领域，逗号分隔，默认 all（新消费,3C电子,汽车）
        push_to_dingtalk (bool): 是否推送到钉钉，默认 False
        dry_run (bool): dry_run 模式，默认 True
        sent_file (str): 去重记录文件，默认 memory/sent.json
        model (str): 指定 LLM 模型（可选）
    """
    if params is None:
        params = {}

    try:
        top_n   = int(params.get("top_n", DEFAULT_TOP_N))
        hours   = int(params.get("hours", DEFAULT_HOURS))
        domains_str = params.get("domains", "all")
        push_to_dingtalk = str(params.get("push_to_dingtalk", "false")).lower() == "true"
        dry_run = str(params.get("dry_run", "false")).lower() == "true"
        model_name = params.get("model")

        # 解析领域
        if domains_str.lower() == "all":
            target_domains = ALL_DOMAINS
        else:
            target_domains = [d.strip() for d in domains_str.split(",")]
            target_domains = [d for d in target_domains if d in ALL_DOMAINS]
            if not target_domains:
                target_domains = ALL_DOMAINS

        # 路径处理
        sent_file = params.get("sent_file", DEFAULT_SENT_FILE)
        if sent_file and not os.path.isabs(sent_file):
            skill_dir = Path(__file__).parent.parent
            sent_file = str(skill_dir / sent_file)

        push_sender_path = params.get("push_sender", "../../shared/push_sender_xiaofei.py")
        if push_sender_path and not os.path.isabs(push_sender_path):
            script_dir = Path(__file__).parent
            push_sender_path = str((script_dir / push_sender_path).resolve())

        # 初始化 LLM
        llm_provider = None
        try:
            from skill_service.llm.multi_model_config import get_multi_model_manager
            manager = get_multi_model_manager()
            llm_provider = manager.create_llm_provider(model=model_name)
            profile = manager.get_current_profile()
            print(f"[LLM] 使用模型: {profile.model if profile else 'unknown'}")
        except Exception as e:
            print(f"[LLM] 初始化失败: {e}")

        # Step 1: 抓取
        print(f"\n=== Step 1: 抓取 RSS（目标领域: {', '.join(target_domains)}）===")
        all_items = fetch_by_domains(target_domains)
        total_fetched = len(all_items)
        print(f"合计抓取：{total_fetched} 条\n")

        # Step 2: 时间窗口过滤
        print("=== Step 2: 时间窗口过滤 ===")
        all_items = filter_by_window(all_items, hours)

        # Step 3: URL 去重
        print("=== Step 3: URL 去重 ===")
        all_items = deduplicate_by_url(all_items)

        # Step 4: 去重（已推送）
        print("=== Step 4: 已推送去重 ===")
        all_items = filter_unsent(all_items, sent_file)

        if not all_items:
            print("无新内容，结束。")
            return {"success": True, "output": f"## 行业资讯日报\n\n在过去 {hours} 小时内暂无新资讯。", "data": None}

        # Step 5: LLM 过滤 + 领域分类
        print("\n=== Step 5: LLM 过滤 & 领域分类 ===")
        all_items = llm_classify(all_items, llm_provider)
        all_items = llm_assign_domain(all_items, llm_provider)

        # 限制每领域条数
        grouped: dict[str, list[NewsItem]] = {d: [] for d in target_domains}
        for it in all_items:
            if it.domain in grouped and len(grouped[it.domain]) < top_n:
                grouped[it.domain].append(it)

        # 格式化
        output = format_output(grouped, total_fetched, hours)

        # Step 6: 推送
        if push_to_dingtalk and not dry_run:
            print("\n=== Step 6: 推送到钉钉 ===")
            ok = send_to_dingtalk(output, push_sender_path)
            if ok:
                mark_as_sent(all_items, sent_file)
                output += "\n\n✅ 已推送到钉钉"
            else:
                output += "\n\n⚠️ 推送失败（请检查 push_sender.py）"
        elif dry_run:
            print("\n=== Step 6: dry_run 模式，跳过推送 ===")
        else:
            print("\n=== Step 6: push_to_dingtalk=false，跳过推送 ===")

        return {
            "success": True,
            "output": output,
            "data": {
                "total_fetched": total_fetched,
                "in_window": sum(1 for _ in all_items),
                "grouped": {d: [{"title": it.title, "link": it.link, "domain": it.domain,
                                  "source": it.source, "pub_time": it.pub_time}
                                 for it in items]
                            for d, items in grouped.items() if items},
            },
        }

    except Exception as e:
        import traceback
        return {"success": False, "output": f"执行失败: {e}\n{traceback.format_exc()}", "data": None}


# ── 命令行入口 ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="行业资讯监控（新消费 / 3C电子 / 汽车）")
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N, help="每领域最多推送条数")
    parser.add_argument("--hours", type=int, default=DEFAULT_HOURS, help="时间窗口（小时）")
    parser.add_argument("--domains", default="all", help="监控领域，逗号分隔")
    parser.add_argument("--push", action="store_true", help="推送到钉钉")
    parser.add_argument("--dry-run", action="store_true", help="只输出不推送")
    parser.add_argument("--sent-file", default=DEFAULT_SENT_FILE, help="去重文件")
    parser.add_argument("--model", default=None, help="指定 LLM 模型")
    args = parser.parse_args()

    result = execute({
        "top_n": args.top_n,
        "hours": args.hours,
        "domains": args.domains,
        "push_to_dingtalk": args.push,
        "dry_run": args.dry_run,
        "sent_file": args.sent_file,
        "model": args.model,
    })
    print("\n" + result["output"])
    if not result["success"]:
        sys.exit(1)
