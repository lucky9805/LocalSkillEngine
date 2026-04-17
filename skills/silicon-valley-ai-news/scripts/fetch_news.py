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
import time
import html
from datetime import datetime, timedelta
from pathlib import Path
import concurrent.futures
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import timezone
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
import hashlib

# 默认配置
DEFAULT_SENT_FILE = None  # None 表示不持久化（每次都返回所有新闻）
DEFAULT_TOP_N = 10
DEFAULT_HOURS = 24
DEFAULT_TRANSLATE = True  # 默认翻译成中文

# 新闻源配置
NEWS_SOURCES = {
    # 一级源 - AI巨头官方
    "OpenAI": "https://openai.com/blog/rss.xml",
    "Google AI": "https://blog.google/technology/ai/rss",
    "DeepMind": "https://deepmind.com/blog/feed",
    "Microsoft AI": "https://blogs.microsoft.com/ai/feed/",
    "NVIDIA": "https://blogs.nvidia.com/feed/",
    "AWS ML Blog": "https://aws.amazon.com/blogs/machine-learning/feed/",
    "Engineering at Meta": "https://engineering.fb.com/feed/",
    
    # 二级源 - 权威科技媒体
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "Wired AI": "https://www.wired.com/feed/tag/ai/latest/rss",
    "VentureBeat AI": "https://venturebeat.com/category/ai/feed/",
    "MIT Tech Review": "https://www.technologyreview.com/feed/",
    "MIT News AI": "https://news.mit.edu/rss/topic/artificial-intelligence2",
    "IEEE Spectrum AI": "https://spectrum.ieee.org/customfeeds/feed/all-topics/rss",
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/technology-lab",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "Cloudflare AI": "https://blog.cloudflare.com/tag/ai/rss/",
    
    # 三级源 - 技术社区
    # "Hacker News AI": "https://hnrss.org/newest?q=AI+OR+LLM+OR+GPT+OR+OpenAI+OR+machine+learning",  # 噪音较多，暂时屏蔽
    "KDnuggets": "https://www.kdnuggets.com/feed",
    "Analytics Vidhya": "https://www.analyticsvidhya.com/feed/",
}


SOURCE_TIMEOUTS = {
    "Google AI": 18,  # 这些源在部分网络下响应偏慢
    "Wired AI": 18,
    "IEEE Spectrum AI": 18,
}


def fetch_url(url, timeout=15, retries=2):
    """获取 URL 内容（含重试）"""
    for attempt in range(retries + 1):
        try:
            # 使用完整的浏览器 User-Agent，避免被反爬虫拦截
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/rss+xml, application/xml, text/xml, */*',
                'Accept-Language': 'en-US,en;q=0.9',
            })
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read().decode('utf-8', errors='replace')
        except Exception as e:
            if attempt >= retries:
                print(f"获取失败 {url}: {e}")
                return None
            # 轻量退避，降低瞬时波动带来的漏抓
            time.sleep(0.6 * (attempt + 1))
    return None


def _strip_ns(tag):
    return tag.split('}', 1)[-1].lower() if tag else ""


def _first_text(entry, candidate_tags):
    for child in entry:
        if _strip_ns(child.tag) in candidate_tags:
            text = ''.join(child.itertext()).strip()
            if text:
                return text
    return ""


def _extract_link(entry):
    """兼容 RSS/Atom 的链接提取"""
    rss_link = ""
    atom_alt_href = ""
    atom_any_href = ""

    for child in entry:
        if _strip_ns(child.tag) != 'link':
            continue
        text_link = ''.join(child.itertext()).strip()
        if text_link and not rss_link:
            rss_link = text_link
        href = (child.attrib.get('href') or '').strip()
        rel = (child.attrib.get('rel') or '').strip().lower()
        if href:
            if rel == 'alternate' and not atom_alt_href:
                atom_alt_href = href
            if not atom_any_href:
                atom_any_href = href

    return rss_link or atom_alt_href or atom_any_href


def _clean_desc(text):
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) > 200:
        text = text[:200] + "..."
    return text


def _parse_rss_with_regex(xml_content, source_name):
    """正则兜底解析（兼容旧逻辑）"""
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
        print(f"正则解析失败 {source_name}: {e}")
        return []


def parse_rss(xml_content, source_name):
    """解析 RSS/Atom：优先 XML，失败回退正则"""
    if not xml_content:
        return []

    try:
        normalized_xml = re.sub(r'<!DOCTYPE[^>]*>', '', xml_content)
        root = ET.fromstring(normalized_xml)
        results = []

        root_tag = _strip_ns(root.tag)
        entries = []

        if root_tag in ("rss", "rdf"):
            channel = None
            for child in root:
                if _strip_ns(child.tag) == "channel":
                    channel = child
                    break
            if channel is not None:
                entries = [node for node in channel if _strip_ns(node.tag) == "item"]
        elif root_tag == "feed":
            entries = [node for node in root if _strip_ns(node.tag) == "entry"]
        else:
            # 未知结构时保守处理，避免整树扫描引入误抓
            return _parse_rss_with_regex(xml_content, source_name)

        for entry in entries:

            title_text = _first_text(entry, {"title"})
            link_text = _extract_link(entry)
            date_text = _first_text(entry, {"pubdate", "published", "updated", "date"})
            desc_text = _first_text(entry, {"description", "summary", "encoded", "content"})
            desc_text = _clean_desc(desc_text)

            if not title_text or not link_text:
                continue

            results.append({
                'title': html.unescape(title_text),
                'link': link_text,
                'date': date_text,
                'description': desc_text,
                'source': source_name
            })

        if results:
            return results
    except Exception:
        pass

    return _parse_rss_with_regex(xml_content, source_name)


def _parse_news_datetime(date_str):
    """解析新闻时间，兼容 RFC 2822 / ISO 8601"""
    if not date_str:
        return None
    short = date_str.strip()[:50]
    if not short:
        return None
    try:
        return parsedate_to_datetime(short)
    except Exception:
        pass
    try:
        return datetime.fromisoformat(short.replace('Z', '+00:00'))
    except Exception:
        return None


def _normalize_hn_link(item):
    """统一 Hacker News 条目链接为文章真实链接，避免去重键不一致"""
    if item.get('source') == "Hacker News AI" or is_hacker_news_item(item):
        real_link = extract_real_link_from_hn(item)
        if real_link:
            item['link'] = real_link
    return item


def _canonicalize_url(url: str) -> str:
    """规范化 URL，用于稳定去重键"""
    if not url:
        return ""
    try:
        u = url.strip()
        if not u:
            return ""

        parts = urlsplit(u)
        scheme = (parts.scheme or "https").lower()
        netloc = parts.netloc.lower()
        path = parts.path or "/"
        if path != "/":
            path = path.rstrip("/")

        # 去掉常见追踪参数，降低同一新闻多 URL 形态导致的重复推送
        drop_params = {
            "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
            "gclid", "fbclid", "mc_cid", "mc_eid", "igshid"
        }
        q = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=False) if k.lower() not in drop_params]
        query = urlencode(q, doseq=True)

        # 去 fragment
        return urlunsplit((scheme, netloc, path, query, ""))
    except Exception:
        return url.strip()


def _normalize_title(title: str) -> str:
    """规范化标题用于相似度比较：小写、去除标点、去除多余空格"""
    import unicodedata
    # Unicode 正规化 + 小写
    text = unicodedata.normalize('NFKC', title).lower()
    # 去除常见标点和格式字符
    text = re.sub(r'[\'`\"\'\"\u2018\u2019\u201c\u201d]', '', text)
    # 去除HTML实体
    text = re.sub(r'&[a-z]+;', ' ', text)
    text = re.sub(r'&#\d+;', ' ', text)
    # 去除数字和百分号（版本号、分数等容易变化）
    text = re.sub(r'\s*\d+[\.\d]*\s*', ' ', text)
    # 去除多余空格
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _news_fingerprint(item: dict) -> str:
    """
    内容指纹（跨轮次兜底去重）
    由 source + 规范化标题 + 日期桶 组成，容忍 URL 轻微变化。
    """
    source = (item.get("source") or "").strip().lower()
    title = _normalize_title(item.get("title", ""))
    date_str = (item.get("date") or "").strip()
    date_bucket = date_str[:10] if date_str else ""
    raw = f"{source}|{title}|{date_bucket}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _title_similarity(t1: str, t2: str) -> float:
    """计算两个标题的相似度（0~1），基于字符级 Jaccard"""
    if not t1 or not t2:
        return 0.0
    words1 = set(t1.split())
    words2 = set(t2.split())
    if not words1 or not words2:
        return 0.0
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    return intersection / union if union > 0 else 0.0


def filter_duplicate_titles(news_items: list, known_titles: set, threshold: float = 0.6) -> list:
    """
    基于标题相似度去重。
    如果一条新闻的规范化标题与已知标题集合的相似度 >= threshold，则过滤掉。
    
    Args:
        news_items: 待过滤的新闻列表
        known_titles: 已知的规范化标题集合
        threshold: 相似度阈值（默认 0.6）
    
    Returns:
        过滤后的新闻列表（保留的条目）
    """
    kept = []
    for item in news_items:
        title = item.get('title', '')
        norm = _normalize_title(title)
        if not norm:
            kept.append(item)
            continue
        
        is_duplicate = False
        for known in known_titles:
            if _title_similarity(norm, known) >= threshold:
                is_duplicate = True
                break
        
        if not is_duplicate:
            kept.append(item)
            known_titles.add(norm)
        else:
            print(f"  [去重-标题] {title[:60]}...")
    
    return kept


def convert_to_beijing_time(date_str):
    """转换为北京时间"""
    if not date_str:
        return ""
    
    try:
        date_str = date_str.strip()[:50]
        
        # RFC 2822 格式
        try:
            dt = parsedate_to_datetime(date_str)
            dt = dt.astimezone(timezone(timedelta(hours=8)))
            return dt.strftime('%Y年%m月%d日 %H:%M')
        except:
            pass
        
        # ISO格式
        try:
            if 'T' in date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                if dt.tzinfo:
                    dt = dt.astimezone(timezone(timedelta(hours=8)))
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


def is_hacker_news_item(item):
    """判断是否是 Hacker News 类型的条目（摘要不是真正内容）"""
    desc = item.get('description', '')
    return 'Article URL:' in desc and 'Comments URL:' in desc


def extract_real_link_from_hn(item):
    """从 Hacker News 条目中提取真正的文章链接"""
    desc = item.get('description', '')
    match = re.search(r'Article URL:\s*(\S+)', desc)
    if match:
        return match.group(1)
    return item.get('link', '')


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
        "url": item.get("link", ""),
        "fingerprint": item.get("_fingerprint", ""),
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
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


def generate_missing_summaries(items: list, llm_provider=None) -> list:
    """为缺少摘要的新闻生成一句话摘要
    
    Args:
        items: 新闻列表
        llm_provider: LLM provider 实例
    
    Returns:
        处理后的新闻列表
    """
    if not items or not llm_provider:
        return items
    
    # 找出缺少摘要的条目
    missing_indices = []
    lines = []
    for i, news in enumerate(items):
        if not news.get('description') or news['description'] == '暂无':
            missing_indices.append(i)
            lines.append(f"{i}: {news['title']}")
    
    if not lines:
        return items
    
    try:
        from skill_service.llm.provider import LLMMessage
        
        prompt = (
            "请为以下新闻标题生成一句话摘要（15-30字中文），格式为'编号: 摘要'，每行一条：\n\n"
            + "\n".join(lines)
        )
        messages = [LLMMessage(role="user", content=prompt)]
        
        response = _run_async(llm_provider.chat(messages, max_tokens=1000))
        
        if not (response and response.content):
            return items
        
        # 解析结果
        for line in response.content.strip().splitlines():
            m = re.match(r'^(\d+):\s*(.+)$', line.strip())
            if m:
                idx = int(m.group(1))
                if idx in missing_indices:
                    items[idx]['description'] = m.group(2).strip()
    
    except Exception as e:
        print(f"生成摘要失败: {e}")
    
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
        futures = {
            executor.submit(
                fetch_url,
                url,
                SOURCE_TIMEOUTS.get(name, 12),
                2
            ): name
            for name, url in NEWS_SOURCES.items()
        }
        
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

    # 统一规范化链接（尤其是 Hacker News 条目），保证后续去重键一致
    all_news = [_normalize_hn_link(item) for item in all_news]
    for item in all_news:
        item["_dedupe_key"] = _canonicalize_url(item.get("link", ""))
        item["_fingerprint"] = _news_fingerprint(item)
    
    # 加载已有记录
    records = load_news_records(sent_file) if sent_file else {}
    # 对已发送/已选中的记录都去重，避免连续两次输出相同内容
    dedupe_keys = {
        _canonicalize_url(url)
        for url, rec in records.items()
        if rec.get("status") in {"sent", "selected"}
    }
    dedupe_fingerprints = {
        (rec.get("fingerprint") or "").strip()
        for rec in records.values()
        if rec.get("status") in {"sent", "selected"} and rec.get("fingerprint")
    }
    # ⚠️ 标题相似度去重：只用 sent 状态记录（不包括 filtered_time/filtered_ai/overflow）
    # 原因：filtered_time 的老文章标题也会被纳入，导致新内容被误杀
    known_norm_titles = {
        _normalize_title(rec.get("title", ""))
        for rec in records.values()
        if rec.get("title") and rec.get("status") in {"sent", "selected"}
    }

    # ── 阶段 1：AI 关键词过滤 ──────────────────────────────────────
    ai_news = filter_ai_news(all_news)
    ai_urls = {n.get('_dedupe_key', '') for n in ai_news}
    print(f"AI相关新闻: {len(ai_news)} 条")

    # 记录被 AI 关键词过滤掉的（可选，用于统计）
    # 注意：这些记录不影响去重，仅用于分析
    if sent_file:
        for item in all_news:
            url = item.get('_dedupe_key', '')
            if url and url not in records and url not in ai_urls:
                records[url] = _make_record(item, "filtered_ai")

    # ── 阶段 2：时间窗口过滤 ──────────────────────────────────────
    if hours > 0:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        def is_recent(item):
            date_str = item.get('date', '')
            if not date_str:
                return True
            try:
                dt = _parse_news_datetime(date_str)
                if not dt:
                    return True
                if dt.tzinfo:
                    return dt.timestamp() >= cutoff_time.timestamp()
                return dt.replace(tzinfo=timezone.utc) >= cutoff_time
            except:
                return True

        recent_news = [n for n in ai_news if is_recent(n)]
        recent_urls = {n.get('_dedupe_key', '') for n in recent_news}
        print(f"最近 {hours} 小时内的新闻: {len(recent_news)} 条")

        # 记录超出时间窗口的（可选，用于统计）
        if sent_file:
            for item in ai_news:
                url = item.get('_dedupe_key', '')
                if url and url not in records and url not in recent_urls:
                    records[url] = _make_record(item, "filtered_time")
    else:
        recent_news = ai_news

    # ── 阶段 3：URL+指纹去重（跳过已发送/已选中的）────────────────────
    new_news = []
    for n in recent_news:
        key = n.get('_dedupe_key', '')
        fp = n.get('_fingerprint', '')
        key_dup = bool(key) and key in dedupe_keys
        fp_dup = bool(fp) and fp in dedupe_fingerprints
        if not key_dup and not fp_dup:
            new_news.append(n)
    print(f"URL+指纹去重后: {len(new_news)} 条")

    # ── 阶段 3.5：标题相似度去重（同一新闻多来源报道）────────────────
    new_news = filter_duplicate_titles(new_news, known_norm_titles, threshold=0.65)
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
            dt = _parse_news_datetime(item.get('date', ''))
            if dt:
                if not dt.tzinfo:
                    dt = dt.replace(tzinfo=timezone.utc)
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
            url = item.get('_dedupe_key', '')
            fp = item.get('_fingerprint', '')
            rec_key = url or (f"fp:{fp}" if fp else "")
            if rec_key and rec_key not in records:
                records[rec_key] = _make_record(item, "overflow")
    
    # ── 阶段 6：清理摘要 ─────────────────────────────────────────────
    for news in selected:
        desc = news.get('description', '')
        # Hacker News 类型的条目，摘要不是真正内容
        if is_hacker_news_item(news):
            real_link = extract_real_link_from_hn(news)
            if real_link != news.get('link'):
                news['link'] = real_link
            news['description'] = ''  # 清空无效摘要
        # 清理摘要中的 HTML 标签和多余空白
        elif desc:
            desc = re.sub(r'<[^>]+>', '', desc)
            desc = re.sub(r'\s+', ' ', desc).strip()
            if len(desc) > 200:
                desc = desc[:200] + '...'
            news['description'] = desc
    
    # ── 阶段 7：翻译 ─────────────────────────────────────────────
    if translate and llm_provider:
        print(f"正在批量翻译 {len(selected)} 条新闻...")
        selected = batch_translate_to_chinese(selected, llm_provider)
    
    # ── 阶段 8：生成缺失摘要 ─────────────────────────────────────
    if llm_provider:
        missing_count = sum(1 for n in selected if not n.get('description'))
        if missing_count > 0:
            print(f"正在为 {missing_count} 条新闻生成摘要...")
            selected = generate_missing_summaries(selected, llm_provider)
    
    # ── 格式化输出 ────────────────────────────────────────────────
    output = "## 🤖 硅谷AI最新动态\n\n"
    
    for i, news in enumerate(selected, 1):
        title = news.get('title', '无标题')
        desc = news.get('description', '')
        date_str = news.get('date', '')
        link = news.get('link', '')
        
        beijing_time = convert_to_beijing_time(date_str) if date_str else '未知时间'
        
        output += f"## {i}.{title}\n"
        output += f"**摘要**：{desc if desc else '暂无'}\n\n"
        output += f"**时间**：{beijing_time}\n\n"
        output += f"**来源**：{news.get('source', '未知来源')}\n\n"
        output += f"**链接**：[{link}]({link})\n\n"
    
    # ── 返回结果（不在这里标记 sent，由调用方发送成功后手动标记）────
    # 返回完整的 selected 新闻列表，供发送成功后标记 sent 使用
    selected_for_mark = [
        {"link": item.get('link', ''), "title": item.get('title', ''), "source": item.get('source', '')}
        for item in selected if item.get('link')
    ]

    # 默认将本次选中的新闻记录为 selected，确保下次不会重复产出
    if sent_file:
        for item in selected:
            key = item.get('_dedupe_key', '')
            fp = item.get('_fingerprint', '')
            rec_key = key or (f"fp:{fp}" if fp else "")
            if rec_key:
                prev = records.get(rec_key, {})
                if prev.get("status") != "sent":
                    records[rec_key] = _make_record(item, "selected")
        save_news_records(records, sent_file)
    
    return {
        "success": True,
        "output": output,
        "data": {
            "total": len(all_news),
            "ai_related": len(ai_news),
            "recent": len(recent_news),
            "new": len(new_news),
            "selected": len(selected)
        },
        "selected_for_mark": selected_for_mark  # 供外部标记 sent 使用
    }


def mark_as_sent(news_items: list, sent_file: str = None) -> dict:
    """
    将新闻标记为已发送状态。
    在钉钉/本地 API 发送成功后调用。
    
    Args:
        news_items: 新闻列表，每项需包含 link 字段
        sent_file: sent.json 文件路径
    
    Returns:
        dict: 标记结果
    """
    if not sent_file:
        return {"success": False, "message": "未指定 sent_file"}
    
    records = load_news_records(sent_file)
    
    for item in news_items:
        url = item.get('link', '')
        key = _canonicalize_url(url)
        fp = _news_fingerprint(item)
        rec_key = key or (f"fp:{fp}" if fp else "")
        if rec_key:
            rec_item = dict(item)
            rec_item["_fingerprint"] = fp
            records[rec_key] = _make_record(rec_item, "sent")
    
    save_news_records(records, sent_file)
    sent_count = sum(1 for r in records.values() if r.get("status") == "sent")
    print(f"已标记为 sent，共 {len(records)} 条记录（已发送 {sent_count} 条）")
    
    return {"success": True, "marked_count": len(news_items)}


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
