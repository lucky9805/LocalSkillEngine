#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import time
import subprocess
import tempfile
from urllib.parse import urlsplit, urlunsplit

_LOCAL_OPENCLI = "/Users/renhongyu/data/python/opencli"
_GLOBAL_OPENCLI = "/Users/renhongyu/.nvm/versions/node/v22.12.0/lib/node_modules/@jackwener/opencli"
OPENCLI_DIR = _LOCAL_OPENCLI if os.path.exists(f"{_LOCAL_OPENCLI}/dist/main.js") else _GLOBAL_OPENCLI


def _build_fetch_prompt() -> str:
    return (
        "过去 24 小时内，抓取 Twitter 上包含「arxiv.org/abs/」或「paperswithcode.com」的推文，"
        "筛选点赞≥100、按「论文标题、链接、核心观点、互动量、发布账号」整理成markdown格式的文件，推送到我的通知。\n"
        "请以Markdown源代码格式输出\n\n"
        "输出格式如下：\n"
        "## 1.标题\n\n"
        "**摘要**：摘要\n\n"
        "**时间**：发布时间\n\n"
        "**论文地址**：[论文地址](论文地址)\n\n"
        "**x链接**：[真实链接地址](真实链接地址)"
    )


def _get_main_js() -> str:
    new_path = os.path.join(OPENCLI_DIR, "dist", "src", "main.js")
    old_path = os.path.join(OPENCLI_DIR, "dist", "main.js")
    if os.path.exists(new_path):
        return new_path
    return old_path


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1B\[[0-?]*[ -/]*[@-~]", "", text or "")


def _extract_json_response(raw: str) -> str:
    text = _strip_ansi(raw).strip()
    if not text:
        return ""

    # 兼容 opencli 在 JSON 前后追加提示行的情况，优先提取主体 JSON 片段
    candidates = [text]
    m_arr = re.search(r"(\[\s*\{.*\}\s*\])", text, re.DOTALL)
    m_obj = re.search(r"(\{\s*\".*\}\s*)", text, re.DOTALL)
    if m_arr:
        candidates.insert(0, m_arr.group(1))
    if m_obj:
        candidates.insert(0, m_obj.group(1))

    for c in candidates:
        try:
            obj = json.loads(c)
        except Exception:
            continue
        if isinstance(obj, list) and obj:
            first = obj[0]
            if isinstance(first, dict):
                for k in ("response", "content", "output", "text"):
                    v = first.get(k)
                    if isinstance(v, str) and v.strip():
                        return v.strip()
        if isinstance(obj, dict):
            for k in ("response", "content", "output", "text"):
                v = obj.get(k)
                if isinstance(v, str) and v.strip():
                    return v.strip()
    return ""


def _extract_assistant_output(raw: str) -> str:
    text = _strip_ansi(raw).strip()
    for marker in ("  grok/ask", "\ngrok/ask", "┌───"):
        idx = text.find(marker)
        if idx > 0:
            text = text[:idx].strip()
            break
    # 清理 opencli 可能输出的占位行，避免把 "grok/ask" 误当正文
    lines = [ln for ln in text.splitlines() if ln.strip().lower() not in {"grok/ask", "grok ask"}]
    return "\n".join(lines).strip()


def _extract_url(value: str) -> str:
    if not value:
        return "N/A"
    md = re.search(r"\(((?:https?://)?[^)\s]+)\)", value)
    if md:
        u = md.group(1).strip()
        if re.match(r"^https?://", u, re.IGNORECASE):
            return u
        if re.match(r"^(?:x\.com|twitter\.com|arxiv\.org/abs/|paperswithcode\.com/)", u, re.IGNORECASE):
            return "https://" + u
    raw = re.search(r"(?:https?://)?(?:x\.com|twitter\.com|arxiv\.org/abs/|paperswithcode\.com/)[^\s\]）)\"']+", value, re.IGNORECASE)
    if raw:
        u = raw.group(0).rstrip(".,;）)")
        if not re.match(r"^https?://", u, re.IGNORECASE):
            u = "https://" + u
        return u
    return "N/A"


def _canonicalize_url(url: str) -> str:
    if not url or url.upper() == "N/A":
        return "N/A"
    try:
        u = url.strip().rstrip(".,;")
        if not re.match(r"^https?://", u, re.IGNORECASE):
            if re.match(r"^(?:x\.com|twitter\.com|arxiv\.org/abs/|paperswithcode\.com/)", u, re.IGNORECASE):
                u = "https://" + u
        p = urlsplit(u)
        scheme = (p.scheme or "https").lower()
        netloc = p.netloc.lower()
        path = (p.path or "/").rstrip("/") or "/"
        return urlunsplit((scheme, netloc, path, p.query, ""))
    except Exception:
        return url.strip()


def _extract_entries(text: str):
    text = text.replace("\r\n", "\n")
    blocks = re.split(r"\n(?=\s*(?:##\s*)?\d+[\.\、]\s)", text)
    entries = []

    for block in blocks:
        header = re.search(r"^\s*(?:##\s*)?(\d+)[\.\、]\s*\**(.+?)\**\s*$", block, re.MULTILINE)
        if not header:
            continue

        title = re.sub(r"\s+", " ", header.group(2)).strip().strip("*")

        summary_match = re.search(
            r"(?:\*\*)?(?:摘要|核心观点|总结|Summary)(?:\*\*)?[：:]\s*(.+)",
            block,
            re.IGNORECASE,
        )
        time_match = re.search(
            r"(?:\*\*)?(?:时间|发布时间|日期|Time|Date|Published)(?:\*\*)?[：:]\s*(.+)",
            block,
            re.IGNORECASE,
        )
        paper_match = re.search(
            r"(?:\*\*)?(?:论文地址|论文链接|论文URL|Paper|Paper URL)(?:\*\*)?[：:]\s*(.+)",
            block,
            re.IGNORECASE,
        )
        x_match = re.search(
            r"(?:\*\*)?(?:x链接|X链接|推文链接|Twitter链接|Tweet URL|X URL)(?:\*\*)?[：:]\s*(.+)",
            block,
            re.IGNORECASE,
        )

        summary = re.sub(r"\s+", " ", summary_match.group(1)).strip() if summary_match else "N/A"
        when = re.sub(r"\s+", " ", time_match.group(1)).strip() if time_match else "N/A"
        paper = _extract_url(paper_match.group(1) if paper_match else "")
        x_link = _extract_url(x_match.group(1) if x_match else "")

        if paper == "N/A" or x_link == "N/A":
            urls = re.findall(r"(?:https?://)?(?:x\.com|twitter\.com|arxiv\.org/abs/|paperswithcode\.com/)[^\s\]）)\"']+", block, re.IGNORECASE)
            if paper == "N/A":
                for u in urls:
                    uu = u.rstrip(".,;）)")
                    if "arxiv.org/abs/" in uu or "paperswithcode.com" in uu:
                        paper = uu if uu.startswith("http") else ("https://" + uu)
                        break
            if x_link == "N/A":
                for u in urls:
                    uu = u.rstrip(".,;）)")
                    if "x.com/" in uu or "twitter.com/" in uu:
                        x_link = uu if uu.startswith("http") else ("https://" + uu)
                        break

        entries.append(
            {
                "title": title or "N/A",
                "summary": summary or "N/A",
                "time": when or "N/A",
                "paper": paper or "N/A",
                "x_link": x_link or "N/A",
            }
        )

    return entries


def _dedupe_entries(entries):
    seen = set()
    out = []
    for e in entries:
        key = (
            _canonicalize_url(e.get("x_link", "N/A")),
            _canonicalize_url(e.get("paper", "N/A")),
            re.sub(r"\s+", " ", (e.get("title") or "").lower()).strip(),
        )
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
        paper = e.get("paper", "N/A")
        x_link = e.get("x_link", "N/A")

        lines.append(f"## {i}.{title}")
        lines.append("")
        lines.append(f"**摘要**：{summary}")
        lines.append("")
        lines.append(f"**时间**：{when}")
        lines.append("")
        if paper.upper() == "N/A":
            lines.append("**论文地址**：N/A")
        else:
            lines.append(f"**论文地址**：[{paper}]({paper})")
        lines.append("")
        if x_link.upper() == "N/A":
            lines.append("**x链接**：N/A")
        else:
            lines.append(f"**x链接**：[{x_link}]({x_link})")
        lines.append("")

    return "\n".join(lines).strip()


def _finalize_output(content: str):
    entries = _extract_entries(content)
    entries = _dedupe_entries(entries)
    if entries:
        return _render_markdown(entries[:20])
    return ""


def _is_invalid_or_placeholder(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return True
    if t.lower() in {"grok/ask", "grok ask"}:
        return True
    if len(t) < 40:
        return True
    if not re.search(r"(?:https?://)?(?:x\.com|twitter\.com|arxiv\.org/abs/|paperswithcode\.com/)", t, re.IGNORECASE):
        return True
    return False


def _run_cmd(cmd, timeout: int):
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

        # 先尝试 JSON 提取，再回退到纯文本提取
        out = _extract_json_response(raw) or _extract_assistant_output(raw)
        return proc.returncode, out
    except subprocess.TimeoutExpired:
        return 124, f"grok ask 超时（>{timeout}s）"
    except Exception as e:
        return 1, str(e)
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def _run_grok_ask(prompt: str, timeout: int):
    base = ["node", _get_main_js(), "grok", "ask", prompt, "--timeout", str(timeout)]
    cmd_variants = [
        # 优先贴近你手工可运行的默认路径
        base + ["-f", "json"],
        base + ["-f", "md"],
        base + ["--web", "true", "-f", "json"],
        base,
    ]
    rc, out = 1, ""
    for cmd in cmd_variants:
        # 每种命令最多重试 2 次，缓解页面偶发 blocked
        for attempt in range(2):
            rc, out = _run_cmd(cmd, timeout)
            low_out = (out or "").lower()
            blocked = "[blocked]" in low_out or "submit button did not reach a clickable ready state" in low_out
            if out.strip() and not blocked:
                break
            if blocked and attempt == 0:
                time.sleep(2)
                continue
            break
        if out.strip() and "[blocked]" not in (out or "").lower():
            break

    if rc != 0 and not out:
        return False, f"grok ask 失败，exit={rc}"
    if not out:
        return False, "grok ask 返回空内容"
    fatal_markers = (
        "failed to start opencli daemon",
        "unexpected error:",
        "make sure port 19825 is available",
        "error: unknown option",
    )
    low = (out or "").lower()
    if any(m in low for m in fatal_markers):
        return False, out.strip()
    if rc != 0 and re.search(r"^error:", out.strip(), re.IGNORECASE):
        return False, out.strip()
    return True, out


def fetch_and_format(fetch_timeout: int = 300):
    ok, raw = _run_grok_ask(_build_fetch_prompt(), timeout=fetch_timeout)
    if not ok:
        return {"success": False, "output": f"❌ 获取失败: {raw}", "raw": raw}

    if _is_invalid_or_placeholder(raw):
        return {
            "success": False,
            "output": "❌ 获取失败: Grok 返回内容为空或无效（未包含可用新闻链接）。",
            "raw": raw,
        }

    final_output = _finalize_output(raw.strip())
    if _is_invalid_or_placeholder(final_output):
        return {
            "success": False,
            "output": "❌ 获取失败: 未能从 Grok 输出中解析到有效论文条目（需包含论文地址和 x 链接）。",
            "raw": raw,
        }
    return {"success": True, "output": final_output, "raw": raw}
