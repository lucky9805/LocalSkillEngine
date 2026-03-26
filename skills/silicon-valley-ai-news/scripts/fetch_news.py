#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
硅谷AI新闻监控 - 全面扫描所有信息源 (修复版)
"""

import os
import json
import re
import urllib.request
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import concurrent.futures

# 默认配置
DEFAULT_SENT_FILE = None  # None 表示不持久化（每次都返回所有新闻）
DEFAULT_TOP_N = 10
DEFAULT_HOURS = 24
DEFAULT_TRANSLATE = True  # 默认翻译成中文

# 新闻源配置（只保留可用的 RSS 源）
NEWS_SOURCES = {
    # 一级源 - AI巨头官方
    "OpenAI": "https://openai.com/blog/rss.xml",
    "Google AI": "https://blog.google/technology/ai/rss",
    "DeepMind": "https://deepmind.com/blog/feed",
    "Microsoft AI": "https://blogs.microsoft.com/ai/feed/",
    "NVIDIA": "https://blogs.nvidia.com/feed/",
    
    # 二级源 - 权威科技媒体
    "Wired AI": "https://www.wired.com/feed/tag/ai/latest/rss",
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    
    # 三级源 - 技术/学习社区
    "KDnuggets": "https://www.kdnuggets.com/feed",
    "Analytics Vidhya": "https://www.analyticsvidhya.com/feed/",
}


def fetch_url(url, timeout=10):
    """获取URL内容"""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"获取失败 {url}: {e}")
        return None


def parse_rss(xml_content, source_name):
    """解析RSS - 使用正则表达式避免命名空间问题"""
    if not xml_content:
        return []
    
    try:
        results = []
        
        # 移除XML声明和 Doctype
        xml_content = re.sub(r'<\?xml[^?]+\?>', '', xml_content)
        xml_content = re.sub(r'<!DOCTYPE[^>]*>', '', xml_content)
        
        # 提取所有 item 块
        item_pattern = r'<item>(.*?)</item>'
        entry_pattern = r'<entry>(.*?)</entry>'
        
        items = re.findall(item_pattern, xml_content, re.DOTALL)
        if not items:
            items = re.findall(entry_pattern, xml_content, re.DOTALL)
        
        for item_xml in items:
            # 提取各字段
            # 标题
            title_match = re.search(r'<title[^>]*><!\[CDATA\[(.*?)\]\]></title>|<title[^>]*>(.*?)</title>', item_xml, re.DOTALL)
            if title_match:
                title_text = (title_match.group(1) or title_match.group(2) or "").strip()
            else:
                continue
            
            if not title_text:
                continue
            
            # 链接
            link_match = re.search(r'<link[^>]*><!\[CDATA\[(.*?)\]\]></link>|<link[^>]*>(.*?)</link>|<link[^>]*href="([^"]+)"', item_xml, re.DOTALL)
            if link_match:
                link_text = (link_match.group(1) or link_match.group(2) or link_match.group(3) or "").strip()
            else:
                link_text = ""
            
            if not link_text:
                continue
            
            # 日期
            date_match = re.search(r'<pubDate>(.*?)</pubDate>|<published>(.*?)</published>|<dc:date>(.*?)</dc:date>', item_xml, re.DOTALL)
            date_text = (date_match.group(1) or date_match.group(2) or date_match.group(3) or "").strip() if date_match else ""
            
            # 描述 - 多种格式
            desc_match = re.search(r'<description><!\[CDATA\[(.*?)\]\]></description>|<description>(.*?)</description>|<summary><!\[CDATA\[(.*?)\]\]></summary>|<summary>(.*?)</summary>|<content:encoded><!\[CDATA\[(.*?)\]\]></content:encoded>', item_xml, re.DOTALL)
            if desc_match:
                desc_text = (desc_match.group(1) or desc_match.group(2) or desc_match.group(3) or desc_match.group(4) or desc_match.group(5) or "").strip()
                # 移除HTML标签
                desc_text = re.sub(r'<[^>]+>', '', desc_text)
                desc_text = re.sub(r'\s+', ' ', desc_text)
                if len(desc_text) > 200:
                    desc_text = desc_text[:200] + "..."
            else:
                desc_text = ""
            
            results.append({
                'title': title_text,
                'link': link_text,
                'date': date_text,
                'description': desc_text,
                'source': source_name
            })
        
        return results
    except Exception as e:
        print(f"解析失败 {source_name}: {e}")
        return []


def convert_to_beijing_time(date_str):
    """转换为北京时间"""
    if not date_str:
        return ""
    
    try:
        date_str = date_str.strip()[:50]
        
        # RFC 2822 格式
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            dt = dt.astimezone(timedelta(hours=8))
            return dt.strftime('%Y年%m月%d日 %H:%M')
        except:
            pass
        
        # ISO格式
        try:
            if 'T' in date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                if dt.tzinfo:
                    dt = dt.astimezone(timedelta(hours=8))
                return dt.strftime('%Y年%m月%d日 %H:%M')
        except:
            pass
            
    except:
        pass
    
    return date_str[:16] if date_str else ""


def filter_ai_news(items):
    """筛选AI相关新闻"""
    ai_keywords = [
        'AI', 'artificial intelligence', 'LLM', 'GPT', 
        'Claude', 'Gemini', 'OpenAI', 'Anthropic', 'DeepMind', 'Google AI',
        'Microsoft AI', 'Meta AI', 'NVIDIA', 'agent', 'Agent',
        'machine learning', 'ML', 'neural', 'model',
        'inference', 'training', 'deployment', 'startup',
        'funding', 'valuation', 'investment',
        'acquisition', 'release', 'product'
    ]
    
    filtered = []
    for item in items:
        title = item.get('title', '').lower()
        desc = item.get('description', '').lower()
        
        matched = any(kw.lower() in title or kw.lower() in desc for kw in ai_keywords)
        if matched:
            filtered.append(item)
    
    return filtered


def load_news_records(sent_file):
    """加载新闻记录
    
    Returns:
        dict: { url -> record_dict }，其中 record_dict 至少含 "status" 字段
        兼容旧版纯 URL 列表格式（自动升级为 {"status": "sent"}）
    """
    if sent_file and sent_file.strip() and os.path.exists(sent_file):
        try:
            with open(sent_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # 兼容旧版：list[str] → dict
            if isinstance(data, list):
                return {url: {"status": "sent"} for url in data}
            if isinstance(data, dict):
                return data
        except:
            pass
    return {}


def save_news_records(records, sent_file):
    """保存新闻记录（dict 格式）"""
    if sent_file and sent_file.strip():
        os.makedirs(os.path.dirname(sent_file), exist_ok=True)
        with open(sent_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)


def _make_record(item, status):
    """构造一条记录
    
    Args:
        item: 新闻条目 dict（含 title/source/date 等）
        status: sent | filtered_ai | filtered_time | overflow
    
    Returns:
        dict
    """
    return {
        "status": status,
        "title": item.get("title", ""),
        "source": item.get("source", ""),
        "date": item.get("date", ""),
        "recorded_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def _run_async(coro):
    """在任意上下文中安全运行协程（兼容已有事件循环）"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # 已在事件循环中：用线程池跑，避免死锁
        import concurrent.futures as _cf
        with _cf.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    else:
        return asyncio.run(coro)


def batch_translate_to_chinese(items: list, llm_provider=None) -> list:
    """批量翻译新闻列表（标题 + 摘要），一次 LLM 调用
    
    Args:
        items: 新闻列表，每项含 title / description
        llm_provider: LLM provider 实例
    
    Returns:
        翻译后的新闻列表（原地修改 title/description）
    """
    if not items or not llm_provider:
        return items

    # 过滤出需要翻译的字段（不含中文的才翻译）
    def needs_translation(text):
        return text and not re.search(r'[\u4e00-\u9fff]', text)

    # 构建批量翻译请求
    lines = []
    index_map = []  # (item_idx, field) -> line_idx
    for i, news in enumerate(items):
        if needs_translation(news.get('title', '')):
            index_map.append((i, 'title', len(lines)))
            lines.append(f"T{i}: {news['title']}")
        if needs_translation(news.get('description', '')):
            index_map.append((i, 'description', len(lines)))
            lines.append(f"D{i}: {news['description']}")

    if not lines:
        return items

    try:
        from skill_service.llm.provider import LLMMessage

        numbered = "\n".join(lines)
        prompt = (
            "请将以下带编号的英文文本翻译成中文，保留每行开头的编号前缀（如 T0:、D1: 等），"
            "保持专业术语，每行翻译结果单独一行，不要添加解释：\n\n" + numbered
        )
        messages = [LLMMessage(role="user", content=prompt)]

        response = _run_async(llm_provider.chat(messages, max_tokens=2000))

        if not (response and response.content):
            return items

        # 解析回包，格式：T0: 翻译结果\nD0: 翻译结果\n...
        translated = {}
        for line in response.content.strip().splitlines():
            m = re.match(r'^([TD]\d+):\s*(.+)$', line.strip())
            if m:
                translated[m.group(1)] = m.group(2).strip()

        # 回填
        for i, news in enumerate(items):
            tk = f"T{i}"
            dk = f"D{i}"
            if tk in translated:
                news['title'] = translated[tk]
            if dk in translated:
                news['description'] = translated[dk]

    except Exception as e:
        print(f"批量翻译失败: {e}")

    return items


def fetch_and_format(top_n=DEFAULT_TOP_N, hours=DEFAULT_HOURS, sent_file=None, translate=DEFAULT_TRANSLATE, llm_provider=None):
    """抓取并格式化 AI 新闻
    
    Args:
        top_n: 返回前 N 条新闻
        hours: 过滤最近 N 小时的新闻
        sent_file: 新闻记录文件路径（None 则不持久化）
        translate: 是否翻译成中文
        llm_provider: LLM provider 实例（用于翻译）
    
    Returns:
        dict: {
            "success": True,
            "output": "Markdown 格式的新闻列表",
            "data": {
                "total": 1095,
                "ai_related": 1001,
                "recent": 33,
                "new": 24,
                "selected": 10
            }
        }
    """
    print(f"[{datetime.now().isoformat()}] 开始扫描AI新闻...")
    print(f"共 {len(NEWS_SOURCES)} 个新闻源")
    
    all_news = []
    
    # 并行获取所有新闻源
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_url, url, 10): name for name, url in NEWS_SOURCES.items()}
        
        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            try:
                content = future.result()
                if content:
                    items = parse_rss(content, name)
                    if items:
                        all_news.extend(items)
                        print(f"  ✓ {name}: {len(items)} 条")
                    else:
                        print(f"  - {name}: 0 条 (无数据)")
            except Exception as e:
                print(f"  ✗ {name}: {e}")
    
    print(f"\n共获取 {len(all_news)} 条新闻")
    
    # 加载已有记录
    records = load_news_records(sent_file) if sent_file else {}
    # 已处理过的 URL 集合（无论什么状态，都跳过）
    known_urls = set(records.keys())

    # ── 阶段 1：AI 关键词过滤 ──────────────────────────────────────
    ai_news = filter_ai_news(all_news)
    ai_urls = {n['link'] for n in ai_news}
    print(f"AI相关新闻: {len(ai_news)} 条")

    # 记录被 AI 关键词过滤掉的（且之前没见过的）
    if sent_file:
        for item in all_news:
            url = item.get('link', '')
            if url and url not in known_urls and url not in ai_urls:
                records[url] = _make_record(item, "filtered_ai")
                known_urls.add(url)

    # ── 阶段 2：时间窗口过滤 ──────────────────────────────────────
    if hours > 0:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        from email.utils import parsedate_to_datetime

        def is_recent(item):
            date_str = item.get('date', '')
            if not date_str:
                return True
            try:
                dt = parsedate_to_datetime(date_str[:50])
                return dt.timestamp() >= cutoff_time.timestamp()
            except:
                return True

        recent_news = [n for n in ai_news if is_recent(n)]
        recent_urls = {n['link'] for n in recent_news}
        print(f"最近 {hours} 小时内的新闻: {len(recent_news)} 条")

        # 记录超出时间窗口的
        if sent_file:
            for item in ai_news:
                url = item.get('link', '')
                if url and url not in known_urls and url not in recent_urls:
                    records[url] = _make_record(item, "filtered_time")
                    known_urls.add(url)
    else:
        recent_news = ai_news

    # ── 阶段 3：去重（跳过已知 URL）──────────────────────────────
    new_news = [n for n in recent_news if n['link'] not in known_urls]
    print(f"新增新闻: {len(new_news)} 条")
    
    if not new_news:
        if sent_file:
            save_news_records(records, sent_file)
        return {
            "success": True,
            "output": "没有新新闻需要推送",
            "data": {
                "total": len(all_news),
                "ai_related": len(ai_news),
                "recent": len(recent_news),
                "new": 0,
                "selected": 0
            }
        }
    
    # ── 阶段 4：排序 ──────────────────────────────────────────────
    priority = {k: i for i, k in enumerate(NEWS_SOURCES.keys())}
    
    def sort_key(item):
        src_prio = priority.get(item['source'], 999)
        try:
            date_str = item.get('date', '')[:50]
            if date_str:
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(date_str)
                return (src_prio, -dt.timestamp())
        except:
            pass
        return (src_prio, 0)
    
    new_news.sort(key=sort_key)
    
    # ── 阶段 5：top_n 截断，overflow 记录 ────────────────────────
    selected = new_news[:top_n]
    overflow = new_news[top_n:]

    if sent_file and overflow:
        for item in overflow:
            url = item.get('link', '')
            if url and url not in known_urls:
                records[url] = _make_record(item, "overflow")
                known_urls.add(url)
    
    # ── 阶段 6：翻译 ─────────────────────────────────────────────
    if translate and llm_provider:
        print(f"正在批量翻译 {len(selected)} 条新闻...")
        selected = batch_translate_to_chinese(selected, llm_provider)
    
    # ── 格式化输出 ────────────────────────────────────────────────
    output = "## 🤖 硅谷AI最新动态\n\n"
    
    for i, news in enumerate(selected, 1):
        beijing_time = convert_to_beijing_time(news['date'])
        output += f"### {i}. {news['title']}\n\n"
        output += f"**摘要**：{news['description'] if news['description'] else '暂无'}\n\n"
        output += f"**时间**：{beijing_time} (北京时间)\n\n"
        output += f"**来源**：{news['source']}\n\n"
        output += f"**链接地址**：[{news['link']}]({news['link']})\n\n"
        output += "---\n\n"
    
    # ── 保存记录（sent 状态） ─────────────────────────────────────
    if sent_file:
        for item in selected:
            url = item.get('link', '')
            if url:
                records[url] = _make_record(item, "sent")
        save_news_records(records, sent_file)
        sent_count = sum(1 for r in records.values() if r.get("status") == "sent")
        print(f"已更新记录，共 {len(records)} 条（已发送 {sent_count} 条）")
    
    return {
        "success": True,
        "output": output,
        "data": {
            "total": len(all_news),
            "ai_related": len(ai_news),
            "recent": len(recent_news),
            "new": len(new_news),
            "selected": len(selected)
        }
    }


def main():
    """命令行入口（用于直接运行脚本）"""
    import argparse
    
    parser = argparse.ArgumentParser(description='硅谷 AI 新闻监控')
    parser.add_argument('--top', type=int, default=DEFAULT_TOP_N, help='返回前 N 条新闻')
    parser.add_argument('--hours', type=int, default=DEFAULT_HOURS, help='过滤最近 N 小时的新闻')
    parser.add_argument('--sent-file', type=str, default=None, help='已发送新闻记录文件路径')
    
    args = parser.parse_args()
    
    result = fetch_and_format(top_n=args.top, hours=args.hours, sent_file=args.sent_file)
    print(result['output'])


if __name__ == '__main__':
    main()