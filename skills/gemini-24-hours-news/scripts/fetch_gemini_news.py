#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import subprocess
import tempfile
from urllib.parse import urlsplit, urlunsplit

OPENCLI_DIR = "/Users/renhongyu/data/python/opencli"

FETCH_PROMPT = (
    "帮我整理最近24小时(北京时间)全网报道的关于硅谷热门产品动态，AI公司的最新动态，"
    "AI领域热门投融资事件，20条，按发布时间逆序排列，要包括标题，时间，摘要和新闻源链接地址,"
    "可以一条条信息发，不用制作成表格。类似这样的根网址，https://www.theinformation.com/ 不要，"
    "不要假信息，官网地址不要，只要详情页面url，请以Markdown源代码格式输出。"
)

FORMAT_PROMPT_TEMPLATE = (
    "请把下面内容整理成固定 Markdown 格式，只输出结果，不要解释：\\n\\n"
    "## 1.标题\\n\\n"
    "**摘要**：摘要\\n\\n"
    "**时间**：时间\\n\\n"
    "**链接地址**：[真实链接地址](真实链接地址)\\n\\n"
    "## 2.标题\\n\\n"
    "**摘要**：摘要\\n\\n"
    "**时间**：时间\\n\\n"
    "**链接地址**：[真实链接地址](真实链接地址)\\n\\n"
    "要求：\\n"
    "- 输出 20 条\\n"
    "- 按发布时间逆序\\n"
    "- 时间以北京时间表达\\n"
    "- 只保留新闻详情页面 URL，不要官网根网址（例如 https://www.theinformation.com/）\\n"
    "- 不要假信息\\n"
    "- 摘要使用中文\\n\\n"
    "原始内容：\\n{raw_content}"
)


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
    从 Gemini 输出中提取新闻条目，兼容有/无 Markdown 的字段写法。
    """
    text = content.replace("\r\n", "\n")
    pattern = re.compile(
        r"(?:^|\n)\s*(?:##\s*)?(\d+)[\.\、]\s*(.+?)\s*\n+"
        r"\s*(?:\*\*)?摘要(?:\*\*)?[：:]\s*(.+?)\s*\n+"
        r"\s*(?:\*\*)?时间(?:\*\*)?[：:]\s*(.+?)\s*\n+"
        r"\s*(?:\*\*)?链接地址(?:\*\*)?[：:]\s*"
        r"(?:\[(https?://[^\]\s]+)\]\([^)]+\)|(https?://\S+)|N/A)",
        re.IGNORECASE | re.DOTALL,
    )

    entries = []
    for m in pattern.finditer(text):
        title = re.sub(r"\s+", " ", m.group(2)).strip()
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


def _run_gemini_ask(prompt: str, timeout: int):
    cmd = [
        "node",
        "dist/main.js",
        "gemini",
        "ask",
        prompt,
        "--stream",
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
    # Step 1
    ok, raw = _run_gemini_ask(FETCH_PROMPT, timeout=fetch_timeout)
    if not ok:
        return {"success": False, "output": f"❌ 第一步失败: {raw}", "raw": raw}

    # Step 2
    prompt2 = FORMAT_PROMPT_TEMPLATE.format(raw_content=raw[:5000])
    ok2, formatted = _run_gemini_ask(prompt2, timeout=format_timeout)
    if not ok2:
        return {"success": False, "output": f"❌ 第二步失败: {formatted}", "raw": raw}

    final_output = _finalize_output(formatted.strip())
    return {"success": True, "output": final_output, "raw": raw}
