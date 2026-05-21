#!/usr/bin/env python3
"""
AIHOT News Skill - 从 aihot.virxact.com 获取海外 AI 动态
"""
import re
import json
import sys
import time
import subprocess
import os
from pathlib import Path
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone


# ── 配置 ────────────────────────────────────────────────────────────────────

AIHOT_URL = "https://aihot.virxact.com/all"
AIHOT_ENABLED = True
AIHOT_MAX_RATIO = 0.6  # AIHOT 条目最多占选中总数的 60%
DEFAULT_TOP_N = 10
DEFAULT_HOURS = 48
DEFAULT_SENT_FILE = "memory/sent.json"


# ── 工具函数 ────────────────────────────────────────────────────────────────

def _canonicalize_url(url: str) -> str:
    """URL 规范化：去 utm_*, fbclid, 统一 trailing slash"""
    if not url:
        return ""
    try:
        parsed = urllib.parse.urlparse(url)
        # 去掉跟踪参数
        garbage = {"utm_source", "utm_medium", "utm_campaign", "utm_term",
                   "utm_content", "fbclid", "gclid", "_ga", "mc_cid", "mc_eid"}
        qs = urllib.parse.parse_qs(parsed.query)
        cleaned = {k: v for k, v in qs.items() if k not in garbage}
        new_query = urllib.parse.urlencode(cleaned, doseq=True)
        new_parsed = parsed._replace(query=new_query, fragment="")
        result = urllib.parse.urlunparse(new_parsed)
        # 去掉 trailing slash
        if result.endswith("/") and parsed.path != "/":
            result = result.rstrip("/")
        return result.lower()
    except Exception:
        return url.lower() if url else ""


def _news_fingerprint(item: dict) -> str:
    """生成新闻指纹（用于去重）"""
    title = item.get("title", "")
    desc = item.get("description", "")
    title_norm = re.sub(r"\s+", " ", title.lower()).strip()
    desc_norm = re.sub(r"\s+", " ", desc[:100].lower()).strip()
    return f"{title_norm}::{desc_norm}"


def _normalize_title(title: str) -> str:
    """标题归一化（用于相似度去重）"""
    if not title:
        return ""
    t = title.lower()
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                "being", "have", "has", "had", "do", "does", "did", "will",
                "would", "could", "should", "may", "might", "can", "the", "and",
                "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
    words = [w for w in t.split() if w not in stopwords]
    return " ".join(words)


def _jaccard_similarity(a: str, b: str) -> float:
    """Jaccard 相似度"""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    set_a = set(a.split())
    set_b = set(b.split())
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def filter_duplicate_titles(news_list: list, known_titles: set, threshold: float = 0.65) -> list:
    """标题相似度去重"""
    seen = set(known_titles)
    result = []
    for item in news_list:
        norm = _normalize_title(item.get("title", ""))
        if not norm:
            result.append(item)
            continue
        is_dup = False
        for existing in seen:
            if _jaccard_similarity(norm, existing) >= threshold:
                is_dup = True
                break
        if not is_dup:
            seen.add(norm)
            result.append(item)
    return result


def _parse_news_datetime(date_str: str):
    """解析各种格式的时间字符串"""
    if not date_str:
        return None
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    # 尝试 dateutil
    try:
        from dateutil import parser
        return parser.parse(date_str)
    except Exception:
        pass
    return None


def convert_to_beijing_time(date_str: str) -> str:
    """转换为北京时间字符串"""
    if not date_str:
        return "未知时间"
    try:
        dt = _parse_news_datetime(date_str)
        if dt:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            beijing = dt.astimezone(timezone(timedelta(hours=8)))
            return beijing.strftime("%Y-%m-%d %H:%M")
    except Exception:
        pass
    return date_str


# ── 记录文件读写 ───────────────────────────────────────────────────────────

def _make_record(item: dict, status: str) -> dict:
    """创建一条记录（新增 description 和 link，供补发时使用）"""
    return {
        "status": status,
        "title": item.get("title", ""),
        "source": item.get("source", ""),
        "date": item.get("date", ""),
        "description": item.get("description", ""),
        "link": item.get("link", ""),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "fingerprint": item.get("_fingerprint", ""),
    }


def load_news_records(sent_file: str) -> dict:
    """加载记录文件（兼容旧格式）"""
    if not sent_file:
        return {}
    try:
        with open(sent_file, "r") as f:
            data = json.load(f)
        if isinstance(data, list):
            return {url: {"status": "sent", "title": "", "recorded_at": ""} for url in data}
        return data
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


def save_news_records(records: dict, sent_file: str):
    """保存记录文件"""
    if not sent_file:
        return
    try:
        # 确保目录存在
        sent_dir = os.path.dirname(sent_file)
        if sent_dir and not os.path.exists(sent_dir):
            os.makedirs(sent_dir, exist_ok=True)
        with open(sent_file, "w") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[AIHOT] 保存记录失败: {e}")


def mark_as_sent(selected_keys: list, sent_file: str):
    """推送成功后，将选中条目标记为 sent"""
    if not sent_file or not selected_keys:
        return
    try:
        records = load_news_records(sent_file)
        count = 0
        for key in selected_keys:
            if key in records:
                records[key]["status"] = "sent"
                count += 1
        save_news_records(records, sent_file)
        print(f"[AIHOT] 已标记 {count} 条为 sent")
    except Exception as e:
        print(f"[AIHOT] mark_as_sent 失败: {e}")




def fetch_aihot_html() -> str:
    """抓取 AIHOT 全量页面 HTML"""
    try:
        req = urllib.request.Request(AIHOT_URL, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f"[AIHOT] 抓取失败: {e}")
        return ""


def _unescape_rsc(s: str) -> str:
    """解码 RSC 转义字符串：处理 \\n \\\" \\\\ 等多层转义"""
    if not s:
        return s
    # 多次替换确保处理嵌套转义
    s = s.replace('\\n', '\n')
    s = s.replace('\\t', '\t')
    s = s.replace('\\"', '"')
    s = s.replace('\\\\', '\\')
    return s


def parse_aihot_items(html_content: str) -> list:
    """
    解析 AIHOT RSC payload，提取新闻条目。
    
    策略：
      1. 找包含 items 数据的 push chunk（含 titleZh 字段）
      2. 以 \"id\":\" 为分隔符切割成条目块
      3. 对每个条目块用局部正则提取字段
    """
    if not html_content:
        return []
    
    try:
        # 提取所有 push chunks
        chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html_content, re.DOTALL)
        
        # 找到包含 items 数据的 chunk
        data_chunk = None
        for chunk in chunks:
            if 'titleZh' in chunk and 'publishedAt' in chunk:
                data_chunk = chunk
                break
        
        if not data_chunk:
            print("[AIHOT] 未找到包含新闻数据的 RSC chunk")
            return []
        
        # RSC chunk 中的转义格式是 \"field\":\"value\"
        # 以 \"id\":\" 为分隔符切分条目块
        item_blocks = re.split(r'\\"id\\":\\"', data_chunk)
        
        results = []
        for block in item_blocks[1:]:  # 第一个是 items 数组前的无关内容
            try:
                item = _parse_aihot_item_block(block)
                if item:
                    results.append(item)
            except Exception as e:
                continue
        
        print(f"[AIHOT] 解析出 {len(results)} 条")
        return results
        
    except Exception as e:
        print(f"[AIHOT] 解析失败: {e}")
        return []


def _parse_aihot_item_block(block: str) -> dict:
    """从单个条目块中提取字段
    
    RSC chunk 中字段格式：\"field\":\"value\"
    在 Python 字符串中表现为：\"field\":\"value\"
    正则需要匹配：\\"field\\":\\"value\\"
    
    注意：不提取嵌套的 source 对象（因为 \"id\":\" 分割会切断它），
    改用 URL 和 author 推断来源类型。
    """
    
    # 提取 id（块开头就是 id 值）
    id_m = re.match(r'(.*?)\\"', block)
    item_id = id_m.group(1) if id_m else ""
    
    # 提取 url
    url_m = re.search(r'\\"url\\":\\"(.*?)\\"', block)
    url = url_m.group(1) if url_m else ""
    
    # 提取 titleZh
    title_m = re.search(r'\\"titleZh\\":\\"(.*?)\\"', block)
    title_zh = title_m.group(1) if title_m else ""
    
    # 提取 summaryZh
    summary_m = re.search(r'\\"summaryZh\\":\\"(.*?)\\"', block)
    summary_zh = summary_m.group(1) if summary_m else ""
    
    # 提取 author
    author_m = re.search(r'\\"author\\":\\"(.*?)\\"', block)
    author = author_m.group(1) if author_m else ""
    
    # 提取 publishedAt
    pub_m = re.search(r'\\"publishedAt\\":\\"(.*?)\\"', block)
    published_at = pub_m.group(1) if pub_m else ""
    
    # 必须有 url 和 title
    if not url or not title_zh:
        return None
    
    # 解码转义
    title_zh = _unescape_rsc(title_zh)
    summary_zh = _unescape_rsc(summary_zh)
    
    # 限制摘要长度
    if summary_zh and len(summary_zh) > 200:
        summary_zh = summary_zh[:200] + "..."
    
    # 推断来源类型（不依赖嵌套 source 对象）
    # x.com 链接 + author → AIHOT·X：{author}
    # 其他链接 → AIHOT·{domain}
    if 'x.com/' in url or 'twitter.com/' in url:
        source_label = f"AIHOT·X：{author}" if author else "AIHOT·X"
    else:
        # 从 URL 提取域名作为来源
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.replace('www.', '')
            source_label = f"AIHOT·{domain}" if domain else "AIHOT"
        except Exception:
            source_label = "AIHOT"
    
    return {
        'title': title_zh,
        'link': url,
        'date': published_at,
        'description': summary_zh,
        'source': source_label,
        '_aihot_id': item_id,
    }


def fetch_aihot_items(llm_provider=None) -> list:
    """
    抓取并过滤 AIHOT 新闻（仅保留海外 AI 相关）
    
    Args:
        llm_provider: LLM provider 实例（用于智能过滤）
    
    Returns:
        过滤后的新闻列表
    """
    if not AIHOT_ENABLED:
        return []
    
    html_content = fetch_aihot_html()
    if not html_content:
        return []
    
    items = parse_aihot_items(html_content)
    if not items:
        return []
    
    # LLM 智能过滤：仅保留海外 AI 相关新闻
    filtered = _filter_overseas_ai(items, llm_provider)
    print(f"[AIHOT] 过滤后保留 {len(filtered)}/{len(items)} 条（海外 AI 相关）")
    
    return filtered


def _filter_overseas_ai(items: list, llm_provider=None) -> list:
    """
    过滤 AIHOT 条目，仅保留海外 AI 相关新闻。
    优先使用 LLM 智能判断，失败时降级到关键词过滤。
    """
    if not items:
        return []
    
    if llm_provider:
        result = _llm_filter_overseas(items, llm_provider)
        if result is not None:
            return result
    
    # LLM 不可用或失败，降级到关键词过滤
    return _keyword_filter_fallback(items)


_LLM_OVERSEAS_PROMPT = """你是一个新闻分类助手。判断以下新闻是否属于"海外 AI 相关新闻"。

判断标准：
- ✅ 保留：海外 AI 公司/研究/产品/技术（OpenAI、Anthropic、Google DeepMind、Meta AI、xAI、Mistral、NVIDIA、微软 Copilot 等）
- ✅ 保留：国际 AI 学术研究、大模型技术突破、AI 政策法规
- ✅ 保留：来源是中国媒体/平台，但内容报道的是海外 AI 动态
- ✅ 保留：海外知名 AI 领域专家/从业者的观点和分享
- ❌ 过滤：中国本土 AI 公司/产品动态（百度、阿里、腾讯、华为、字节、DeepSeek、Kimi、智谱等自主研发的新闻）
- ❌ 过滤：股价、财报、投资、招聘等非技术内容
- ❌ 过滤：与 AI 完全无关的内容

回复格式：仅输出编号和 Y/N，每行一条：
0: Y
1: N
不要输出任何解释。"""


def _llm_filter_overseas(items: list, llm_provider) -> list:
    """用 LLM 批量判断每条 AIHOT 新闻是否属于海外 AI 相关"""
    try:
        from skill_service.llm.provider import LLMMessage
        
        lines = []
        for i, item in enumerate(items):
            title = item.get('title', '')
            desc = item.get('description', '')
            source = item.get('source', '')
            lines.append(f"{i}: 标题={title}；摘要={desc}；来源={source}")
        
        user_content = "\n".join(lines)
        messages = [
            LLMMessage(role="system", content=_LLM_OVERSEAS_PROMPT),
            LLMMessage(role="user", content=user_content),
        ]
        
        response = _run_async(llm_provider.chat(messages, max_tokens=1024))
        if not (response and response.content):
            print("[AIHOT-LLM] 无响应，降级到关键词过滤")
            return None
        
        decisions = {}
        for line in response.content.strip().splitlines():
            m = re.match(r'^(\d+)\s*[:：]\s*([YyNn])', line.strip())
            if m:
                decisions[int(m.group(1))] = m.group(2).upper() == "Y"
        
        if not decisions:
            print(f"[AIHOT-LLM] 解析失败，降级到关键词过滤")
            return None
        
        result = [item for i, item in enumerate(items) if decisions.get(i, False)]
        print(f"[AIHOT-LLM] 共 {len(items)} 条 → LLM 保留 {len(result)} 条")
        return result
        
    except Exception as e:
        print(f"[AIHOT-LLM] 调用失败: {e}，降级到关键词过滤")
        return None


def _keyword_filter_fallback(items: list) -> list:
    """关键词兜底过滤：排除明确的中国本土内容"""
    # 中国本土实体关键词（命中则排除）
    domestic_keywords = [
        '百度', '阿里', '腾讯', '华为', '字节', '豆包', '扣子', 'Coze',
        'DeepSeek', 'Kimi', '智谱', '文心', '通义', '讯飞',
        '月之暗面', '零一万物', 'MiniMax',
        '商汤', '旷视', '云从', '依图',
    ]
    
    result = []
    for item in items:
        title = item.get('title', '')
        desc = item.get('description', '')
        source = item.get('source', '')
        text = title + desc + source
        
        # 命中本土关键词则跳过
        is_domestic = any(kw in text for kw in domestic_keywords)
        if not is_domestic:
            result.append(item)
    
    print(f"[AIHOT-关键词] 共 {len(items)} 条 → 保留 {len(result)} 条")
    return result





def _get_priority(source: str) -> int:
    """
    来源优先级排序（数值越小优先级越高）：
    - AIHOT·X（Twitter 专家观点）= 1，最高优先
    - AIHOT·{domain}（媒体聚合，非 ithome）= 4
    - AIHOT·ithome.com（IT之家，消费电子/汽车新闻偏多）= 9，降级
    - 其他 = 999
    """
    if source.startswith("AIHOT·X"):
        return 1
    if "ithome" in source:
        return 9   # ithome.com 降级，排在后面
    if source.startswith("AIHOT·"):
        return 4
    return 999

def _run_async(coro):
    """检测是否在异步环境中，选择合适的执行方式"""
    try:
        loop = asyncio.get_running_loop()
        if loop and loop.is_running():
            import concurrent.futures as _cf
            with _cf.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, coro).result()
    except RuntimeError:
        pass
    return asyncio.run(coro)


import asyncio


# ── 主流程 ─────────────────────────────────────────────────────────────────

def fetch_and_format(top_n=DEFAULT_TOP_N, hours=DEFAULT_HOURS,
                     sent_file=None, llm_provider=None):
    """
    抓取并格式化 AIHOT 新闻。

    Returns:
        dict: {"success": True, "output": "...", "data": {...}}
    """
    print(f"[{datetime.now().isoformat()}] 开始抓取 AIHOT 新闻...")

    # 抓取并过滤
    items = fetch_aihot_items(llm_provider)
    if not items:
        return {
            "success": True,
            "output": "没有获取到 AIHOT 新闻",
            "data": {"total": 0, "filtered": 0, "selected": 0},
        }

    print(f"共获取 {len(items)} 条，开始去重和过滤...")

    # 添加去重键
    for item in items:
        item["_dedupe_key"] = _canonicalize_url(item.get("link", ""))
        item["_fingerprint"] = _news_fingerprint(item)

    # 加载已有记录
    records = load_news_records(sent_file) if sent_file else {}
    # 只屏蔽已成功推送的（sent），不屏蔽 selected（可能推送失败待重试）
    dedupe_keys = {
        _canonicalize_url(url)
        for url, rec in records.items()
        if rec.get("status") == "sent"
    }
    dedupe_fingerprints = {
        (rec.get("fingerprint") or "").strip()
        for rec in records.values()
        if rec.get("status") == "sent" and rec.get("fingerprint")
    }
    known_norm_titles = {
        _normalize_title(rec.get("title", ""))
        for rec in records.values() if rec.get("title")
    }

    # 时间窗口过滤
    if hours > 0:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        def is_recent(item):
            date_str = item.get("date", "")
            if not date_str:
                return True
            try:
                dt = _parse_news_datetime(date_str)
                if not dt:
                    return True
                if dt.tzinfo:
                    return dt.timestamp() >= cutoff_time.timestamp()
                return dt.replace(tzinfo=timezone.utc) >= cutoff_time
            except Exception:
                return True

        items = [n for n in items if is_recent(n)]
        print(f"最近 {hours} 小时内的新闻: {len(items)} 条")

    # URL+指纹去重
    new_items = []
    for n in items:
        key = n.get("_dedupe_key", "")
        fp = n.get("_fingerprint", "")
        key_dup = bool(key) and key in dedupe_keys
        fp_dup = bool(fp) and fp in dedupe_fingerprints
        if not key_dup and not fp_dup:
            new_items.append(n)

    print(f"URL+指纹去重后: {len(new_items)} 条")

    # 标题相似度去重
    new_items = filter_duplicate_titles(new_items, known_norm_titles, threshold=0.65)
    print(f"新增新闻: {len(new_items)} 条")

    if not new_items:
        if sent_file:
            save_news_records(records, sent_file)

        # 无新内容时，尝试补发之前未成功推送的 selected 条目
        retry_items = []
        updated = False
        if sent_file:
            for rec_key, rec in list(records.items()):
                if rec.get("status") == "selected":
                    if rec.get("link"):  # 有 link，可以补发
                        retry_items.append({
                            "title": rec.get("title", ""),
                            "source": rec.get("source", ""),
                            "date": rec.get("date", ""),
                            "description": rec.get("description", ""),
                            "link": rec.get("link", ""),
                            "_dedupe_key": rec_key if rec_key.startswith("http") else "",
                            "_fingerprint": rec.get("fingerprint", ""),
                        })
                    else:  # 没有 link，无法补发，标记为 sent 放弃
                        rec["status"] = "sent"
                        updated = True
            if updated:
                save_news_records(records, sent_file)
            # 按时间排序（新的在前）
            try:
                retry_items.sort(
                    key=lambda x: _parse_news_datetime(x.get("date", "")) or datetime.min.replace(tzinfo=timezone.utc),
                    reverse=True
                )
            except Exception:
                pass
            retry_items = retry_items[:top_n]

        if retry_items:
            output = "## 🤖 AIHOT 海外 AI 动态（补发）\n\n"
            for i, news in enumerate(retry_items, 1):
                beijing_time = convert_to_beijing_time(news.get("date", "")) if news.get("date") else "未知时间"
                output += f"## {i}.{news['title']}\n"
                output += f"**摘要**：{news.get('description', '暂无')}\n\n"
                output += f"**时间**：{beijing_time}\n\n"
                output += f"**来源**：{news.get('source', '未知来源')}\n\n"
                link = news.get("link", "")
                output += f"**链接**：[{link}]({link})\n\n"
            selected_keys = [
                r.get("_dedupe_key", "") or f"fp:{r.get('_fingerprint', '')}"
                for r in retry_items
            ]
            return {
                "success": True,
                "output": output,
                "data": {"total": len(items), "filtered": 0, "new": 0, "selected": len(retry_items)},
                "_selected_keys": selected_keys,
            }

        return {
            "success": True,
            "output": "没有新新闻需要推送",
            "data": {"total": len(items), "filtered": 0, "new": 0, "selected": 0},
        }

    # 排序
    def sort_key(item):
        src_prio = _get_priority(item.get("source", ""))
        try:
            dt = _parse_news_datetime(item.get("date", ""))
            if dt:
                if not dt.tzinfo:
                    dt = dt.replace(tzinfo=timezone.utc)
                return (src_prio, -dt.timestamp())
        except Exception:
            pass
        return (src_prio, 0)

    new_items.sort(key=sort_key)

    # 选取 top_n
    selected = new_items[:top_n]
    overflow = new_items[top_n:]

    print(f"选中 {len(selected)} 条，overflow {len(overflow)} 条")

    # 记录 overflow（未选中的，标记 overflow）
    if sent_file and overflow:
        for item in overflow:
            key = item.get("_dedupe_key", "")
            fp = item.get("_fingerprint", "")
            rec_key = key or (f"fp:{fp}" if fp else "")
            if rec_key and rec_key not in records:
                records[rec_key] = _make_record(item, "overflow")
        save_news_records(records, sent_file)

    # 收集选中条目的 key，供 execute() 在推送成功后标记 sent
    selected_keys = []
    for item in selected:
        key = item.get("_dedupe_key", "")
        fp = item.get("_fingerprint", "")
        rec_key = key or (f"fp:{fp}" if fp else "")
        if rec_key:
            selected_keys.append(rec_key)

    # 记录选中的（tentative，推送成功后会更新为 sent）
    if sent_file:
        for item in selected:
            key = item.get("_dedupe_key", "")
            fp = item.get("_fingerprint", "")
            rec_key = key or (f"fp:{fp}" if fp else "")
            if rec_key:
                records[rec_key] = _make_record(item, "selected")
        save_news_records(records, sent_file)

    # 格式化输出
    output = "## 🤖 AIHOT 海外 AI 动态\n\n"

    for i, news in enumerate(selected, 1):
        title = news.get("title", "无标题")
        desc = news.get("description", "")
        date_str = news.get("date", "")
        link = news.get("link", "")

        beijing_time = convert_to_beijing_time(date_str) if date_str else "未知时间"

        output += f"## {i}.{title}\n"
        output += f"**摘要**：{desc if desc else '暂无'}\n\n"
        output += f"**时间**：{beijing_time}\n\n"
        output += f"**来源**：{news.get('source', '未知来源')}\n\n"
        output += f"**链接**：[{link}]({link})\n\n"

    # 记录选中的
    if sent_file:
        for item in selected:
            key = item.get("_dedupe_key", "")
            fp = item.get("_fingerprint", "")
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
            "total": len(items),
            "new": len(new_items),
            "selected": len(selected),
        },
        "_selected_keys": selected_keys,  # 内部使用，推送成功后标记 sent
    }


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
        # 通过 stdin 传递内容，避免命令行参数长度限制和转义问题
        result = subprocess.run(
            [sys.executable, push_sender_path],
            input=content,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print(f"钉钉推送成功: {result.stdout.strip()}")
            return True
        else:
            print(f"钉钉推送失败: {result.stderr.strip()}")
            return False

    except Exception as e:
        print(f"发送钉钉失败: {e}")
        return False


# ── Skill 入口 ──────────────────────────────────────────────────────────────

def execute(params: dict = None) -> dict:
    """
    Skill Service 入口。

    params:
        top_n (int): 返回前 N 条，默认 10
        hours (int): 时间窗口（小时），默认 48
        sent_file (str): 记录文件路径（用于去重），默认 "memory/sent.json"
        push_to_dingtalk (bool): 是否推送到钉钉，默认 False
        push_sender (str): push_sender.py 脚本路径，默认 "../../shared/push_sender.py"
        translate (bool): 保留兼容（AIHOT 已含中文）
    """
    if params is None:
        params = {}

    top_n = int(params.get("top_n", DEFAULT_TOP_N))
    hours = int(params.get("hours", DEFAULT_HOURS))
    sent_file = params.get("sent_file", DEFAULT_SENT_FILE)
    push_to_dingtalk = str(params.get("push_to_dingtalk", "false")).lower() == "true"
    translate = str(params.get("translate", "true")).lower() != "false"

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

    # llm_provider 需要从 skill service 注入
    llm_provider = params.get("_llm_provider", None)

    result = fetch_and_format(
        top_n=top_n,
        hours=hours,
        sent_file=sent_file,
        llm_provider=llm_provider,
    )

    # 如果抓取成功、有选中的新闻、且需要推送到钉钉
    if result.get("success") and result.get("data", {}).get("selected", 0) > 0 and push_to_dingtalk:
        if send_to_dingtalk(result["output"], push_sender_path):
            result["output"] += "\n\n✅ 已推送到钉钉"
            # 推送成功，标记 selected_keys 为 sent
            selected_keys = result.get("_selected_keys", [])
            if selected_keys and sent_file:
                mark_as_sent(selected_keys, sent_file)
        else:
            result["output"] += "\n\n⚠️ 推送钉钉失败（请检查 push_sender.py 配置）"

    return result


# ── CLI 入口 ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AIHOT News Skill")
    parser.add_argument("--top_n", type=int, default=DEFAULT_TOP_N, help="返回前 N 条")
    parser.add_argument("--hours", type=int, default=DEFAULT_HOURS, help="时间窗口（小时）")
    parser.add_argument("--sent_file", type=str, default="memory/sent.json", help="记录文件路径")
    parser.add_argument("--push_to_dingtalk", action="store_true", help="是否推送到钉钉")
    parser.add_argument("--push_sender", type=str, default="../../shared/push_sender.py", help="push_sender.py 路径")
    parser.add_argument("--translate", action="store_true", default=True, help="是否翻译")

    args = parser.parse_args()

    # 解析 sent_file 相对路径
    sent_file = args.sent_file
    if sent_file and not os.path.isabs(sent_file):
        skill_dir = Path(__file__).parent.parent
        sent_file = str(skill_dir / sent_file)

    # 解析 push_sender 相对路径
    push_sender_path = args.push_sender
    if push_sender_path and not os.path.isabs(push_sender_path):
        script_dir = Path(__file__).parent
        push_sender_path = str((script_dir / push_sender_path).resolve())

    # 如果 push_sender 不存在，重置为 None
    if push_sender_path and not os.path.exists(push_sender_path):
        print(f"警告: push_sender.py 不存在: {push_sender_path}")
        push_sender_path = None

    result = fetch_and_format(
        top_n=args.top_n,
        hours=args.hours,
        sent_file=sent_file,
        llm_provider=None,
    )

    # 如果抓取成功、有选中的新闻、且需要推送到钉钉
    if result.get("success") and result.get("data", {}).get("selected", 0) > 0 and args.push_to_dingtalk:
        if send_to_dingtalk(result["output"], push_sender_path):
            result["output"] += "\n\n✅ 已推送到钉钉"
            # 推送成功，标记 selected_keys 为 sent
            selected_keys = result.get("_selected_keys", [])
            if selected_keys and sent_file:
                mark_as_sent(selected_keys, sent_file)
        else:
            result["output"] += "\n\n⚠️ 推送钉钉失败（请检查 push_sender.py 配置）"

    print(result["output"])
    print(f"\n数据: {result['data']}")
