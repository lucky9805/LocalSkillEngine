#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import subprocess
import tempfile
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit

_LOCAL_OPENCLI  = "/Users/renhongyu/data/python/opencli"
_GLOBAL_OPENCLI = "/Users/renhongyu/.nvm/versions/node/v22.12.0/lib/node_modules/@jackwener/opencli"
# 优先用本地旧版（Strategy.UI，直接操作用户 Chrome，有真实 Google session）
# 全局 1.6.3 改用 Strategy.COOKIE，但 automation window 无法访问 Gemini，暂不使用
import os as _os
OPENCLI_DIR = _LOCAL_OPENCLI if _os.path.exists(f"{_LOCAL_OPENCLI}/dist/main.js") else _GLOBAL_OPENCLI


def _build_fetch_prompt() -> str:
    """动态构建含今日日期的抓取 Prompt，强制 Gemini 触发 Google Search 实时联网"""
    today = datetime.now().strftime("%Y年%m月%d日")
    return (
        f"今天是{today}（北京时间）。请使用 Google Search 工具，搜索过去24小时内（截至{today}）"
        "全网最新报道的硅谷热门产品动态、AI公司最新动态、AI领域热门投融资事件，共20条，"
        "按发布时间逆序排列，要包括标题、时间、摘要和新闻源链接地址，"
        "可以一条条信息发，不用制作成表格。"
        "类似这样的根网址 https://www.theinformation.com/ 不要，"
        "不要假信息，官网地址不要，只要详情页面url，请以Markdown源代码格式输出。\n"
        "⚠️ 必须联网搜索获取真实最新内容，严禁使用训练数据中的历史新闻。"
    )

# Step 2 格式化已移除：不再发起第二次 Gemini 调用（会新开会话丢失上下文，可能重新编造内容）
# Step 1 prompt 直接要求格式化好的输出，结果由本地 _finalize_output() 解析


def _extract_assistant_output(raw: str) -> str:
    text = raw.strip()
    # 清掉 opencli 尾部会话表格
    for marker in ("  gemini/ask", "\\ngemini/ask", "┌───"):
        idx = text.find(marker)
        if idx > 0:
            text = text[:idx].strip()
            break
    # 移除 ANSI 颜色控制符
    text = re.sub(r"\x1B\[[0-?]*[ -/]*[@-~]", "", text)
    return text.strip()


def _canonicalize_url(url: str) -> str:
    if not url:
        return ""
    try:
        u = url.strip().rstrip(".,;")
        parts = urlsplit(u)
        scheme = (parts.scheme or "https").lower()
        netloc = parts.netloc.lower()
        path = (parts.path or "/").rstrip("/") or "/"
        return urlunsplit((scheme, netloc, path, parts.query, ""))
    except Exception:
        return url.strip()


def _extract_entries(content: str):
    """
    从 Gemini 输出中提取新闻条目，兼容多种字段写法：
    - 摘要/内容/简介/描述
    - 时间/发布时间/日期
    - 链接地址/链接/来源/URL/Source
    - 有无 Markdown 粗体（**xxx**）
    """
    text = content.replace("\r\n", "\n")

    # 宽松版：支持多种字段名变体
    pattern = re.compile(
        r"(?:^|\n)\s*(?:##\s*)?(\d+)[\.\、]\s*\**(.+?)\**\s*\n+"
        r"(?:.{0,5}\n)*?"   # 允许标题下有短行（如空行、--- 分割线）
        r"\s*(?:\*\*)?(?:摘要|内容|简介|描述|Summary|Abstract)(?:\*\*)?[：:]\s*(.+?)\s*\n+"
        r"(?:.{0,5}\n)*?"
        r"\s*(?:\*\*)?(?:时间|发布时间|日期|Time|Date|Published)(?:\*\*)?[：:]\s*(.+?)\s*\n+"
        r"(?:.{0,5}\n)*?"
        r"\s*(?:\*\*)?(?:链接地址|链接|来源链接|来源|URL|Source|Link)(?:\*\*)?[：:]\s*"
        r"(?:\[(https?://[^\]\s]+)\]\([^)]+\)|(https?://\S+)|N/A)",
        re.IGNORECASE | re.DOTALL,
    )

    entries = []
    for m in pattern.finditer(text):
        title = re.sub(r"\s+", " ", m.group(2)).strip().strip("*")
        summary = re.sub(r"\s+", " ", m.group(3)).strip()
        when = re.sub(r"\s+", " ", m.group(4)).strip()
        link = (m.group(5) or m.group(6) or "N/A").strip()
        entries.append(
            {
                "title": title,
                "summary": summary,
                "time": when,
                "link": link,
            }
        )

    # 如果严格匹配失败，尝试宽松回退：按数字序号分割条目
    if not entries:
        entries = _extract_entries_fallback(text)

    return entries


def _extract_entries_fallback(text: str):
    """
    回退解析：按 "数字. 标题" 切分，尽量提取 URL 和摘要片段。
    用于 Gemini 输出格式不规范时的兜底。
    """
    # 按条目头部切割
    blocks = re.split(r"\n(?=\s*(?:##\s*)?\d+[\.\、]\s)", text)
    entries = []
    for block in blocks:
        # 提取编号 + 标题
        header = re.match(r"\s*(?:##\s*)?(\d+)[\.\、]\s*\**(.+?)\**\s*\n", block)
        if not header:
            continue
        title = re.sub(r"\s+", " ", header.group(2)).strip().strip("*")

        # 提取 URL（取第一个出现的 http 链接）
        url_m = re.search(r"https?://[^\s\]）)\"']+", block)
        link = url_m.group(0).rstrip(".,;）)") if url_m else "N/A"

        # 提取时间（尝试匹配日期格式）
        time_m = re.search(
            r"(?:时间|日期|发布|Published|Date)[：:\s]*([^\n]{5,40})"
            r"|(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?(?:\s+\d{2}:\d{2})?)",
            block, re.IGNORECASE,
        )
        when = "N/A"
        if time_m:
            when = (time_m.group(1) or time_m.group(2) or "N/A").strip()

        # 摘要：取标题后第一段有意义的文字（过滤字段名行）
        lines = block.split("\n")[1:]
        summary_lines = []
        for line in lines:
            l = line.strip().lstrip("*").strip()
            if not l or re.match(r"(?:摘要|时间|链接|来源|URL|Published|Source|Date)[：:]", l, re.I):
                continue
            if l.startswith("http"):
                continue
            summary_lines.append(l)
            if len(" ".join(summary_lines)) > 150:
                break
        summary = re.sub(r"\s+", " ", " ".join(summary_lines)).strip() or "N/A"

        entries.append({"title": title, "summary": summary, "time": when, "link": link})
    return entries


def _dedupe_entries(entries):
    seen = set()
    out = []
    for e in entries:
        link_key = _canonicalize_url(e.get("link", "")) or "N/A"
        title_key = re.sub(r"\s+", " ", (e.get("title") or "").lower()).strip()
        key = (link_key, title_key)
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out


def _render_markdown(entries):
    lines = []
    for i, e in enumerate(entries, 1):
        title = e.get("title", "N/A")
        summary = e.get("summary", "N/A")
        when = e.get("time", "N/A")
        link = e.get("link", "N/A")
        lines.append(f"## {i}.{title}")
        lines.append("")
        lines.append(f"**摘要**：{summary}")
        lines.append("")
        lines.append(f"**时间**：{when}")
        lines.append("")
        if link.upper() == "N/A":
            lines.append("**链接地址**：N/A")
        else:
            lines.append(f"**链接地址**：[{link}]({link})")
        lines.append("")
    return "\n".join(lines).strip()


def _finalize_output(content: str):
    """
    强制收敛为标准模板并去重，避免重复段落。
    """
    entries = _extract_entries(content)
    entries = _dedupe_entries(entries)
    if entries:
        # 保留前 20 条，满足需求
        return _render_markdown(entries[:20])
    # 无法结构化提取时，保底返回原文
    return content.strip()


def _get_main_js() -> str:
    """自动检测 opencli 入口文件路径（全局安装结构为 dist/src/main.js，旧版为 dist/main.js）"""
    new_path = _os.path.join(OPENCLI_DIR, "dist", "src", "main.js")
    old_path = _os.path.join(OPENCLI_DIR, "dist", "main.js")
    if _os.path.exists(new_path):
        return new_path
    return old_path


def _run_gemini_ask(prompt: str, timeout: int):
    cmd = [
        "node",
        _get_main_js(),
        "gemini",
        "ask",
        prompt,
        "--timeout",
        str(timeout),
    ]

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8")
    tmp_path = tmp.name
    tmp.close()

    try:
        with open(tmp_path, "w", encoding="utf-8") as fout:
            proc = subprocess.run(
                cmd,
                cwd=OPENCLI_DIR,
                stdout=fout,
                stderr=subprocess.STDOUT,
                timeout=timeout + 30,
            )

        with open(tmp_path, "r", encoding="utf-8", errors="replace") as fin:
            raw = fin.read()

        out = _extract_assistant_output(raw)
        if proc.returncode != 0 and not out:
            return False, f"gemini ask 失败，exit={proc.returncode}"
        if not out:
            return False, "gemini ask 返回空内容"
        return True, out
    except subprocess.TimeoutExpired:
        return False, f"gemini ask 超时（>{timeout}s）"
    except Exception as e:
        return False, str(e)
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def fetch_and_format(fetch_timeout: int = 300, format_timeout: int = 120):
    # 单步：动态生成含今日日期的 prompt，Gemini 联网搜索并直接输出格式化结果
    # 不再发起第二次 Gemini 调用（二次调用会新开会话，丢失实时搜索上下文，导致编造旧新闻）
    ok, raw = _run_gemini_ask(_build_fetch_prompt(), timeout=fetch_timeout)
    if not ok:
        return {"success": False, "output": f"❌ 获取失败: {raw}", "raw": raw}

    final_output = _finalize_output(raw.strip())
    return {"success": True, "output": final_output, "raw": raw}
