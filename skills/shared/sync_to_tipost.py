# -*- coding: utf-8 -*-
"""
sync_to_tipost.py
钛媒体打分系统 → 钛媒体内容平台，文章同步发布 CLI 工具。

用法：
    # 直接发布内容
    python sync_to_tipost.py --title "标题" --summary "摘要" --main "正文"

    # 从数据库同步今日最高分文章
    python sync_to_tipost.py

    # 同步指定 ID 文章
    python sync_to_tipost.py --id 42

    # 同步高分前 N 篇（近 N 天）
    python sync_to_tipost.py --top 5 --days 3 --min-score 7.0

    # 预览模式（不实际发送）
    python sync_to_tipost.py --top 3 --dry-run
"""

import argparse
import json
import sys
import os
import time
import requests
from datetime import datetime, timedelta

# ── API 配置 ──
API_URL    = "https://demobtm.tipost.com/api/sync_ai_article"
APP_KEY    = "TMT-AI-APP-20250101"
APP_SECRET = "7f4a30dcd8d94f0c9bd1d868d7f7f3b8"

HEADERS = {
    "App-Key":    APP_KEY,
    "App-Secret": APP_SECRET,
}


# ── 发送文章 ──

def sync_article(title: str, summary: str, main: str, dry_run: bool = False) -> dict:
    """向钛媒体 API 发布一篇文章，返回 API 响应 dict。"""
    payload = {"title": title, "summary": summary, "main": main}

    print(f"[同步] {title[:60]}{'...' if len(title) > 60 else ''}")
    print(f"       摘要 {len(summary)} 字 | 正文 {len(main)} 字")

    if dry_run:
        print("       [dry-run] 预览模式，未发送")
        return {"dry_run": True, "payload": payload}

    try:
        resp = requests.post(API_URL, headers=HEADERS, data=payload, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        print(f"       -> HTTP {resp.status_code} OK")
        return result
    except requests.exceptions.Timeout:
        print("       -> 错误：请求超时（30s）")
        return {"error": "timeout"}
    except requests.exceptions.HTTPError:
        print(f"       -> 错误：HTTP {resp.status_code}  {resp.text[:200]}")
        return {"error": f"http_{resp.status_code}", "detail": resp.text}
    except Exception as e:
        print(f"       -> 错误：{e}")
        return {"error": str(e)}


# ── 数据库读取 ──

def build_article_content(article) -> dict:
    """将 Article 对象拼装为发布所需的 title/summary/main。"""
    title       = article.title or ""
    description = article.description or ""
    content     = article.content or description

    summary = description[:300] if description else (content[:300] if content else title)

    parts = []
    if article.score:
        parts.append(f"【综合评分：{article.score:.1f}/10"
                      + (f"  微信适配分：{article.wx_total:.0f}/100" if article.wx_total else "")
                      + "】")
        if article.score_reason:
            parts.append(f"打分说明：{article.score_reason[:200]}")
    if article.author:
        parts.append(f"作者：{article.author}")
    if article.pub_date:
        parts.append(f"发布时间：{article.pub_date.strftime('%Y-%m-%d')}")
    if article.link:
        parts.append(f"原文链接：{article.link}")
    parts.append("\n" + content)

    return {"title": title, "summary": summary, "main": "\n".join(parts).strip()}


def sync_from_db(
    article_ids: list = None,
    top_n: int = 1,
    source: str = "tmtpost",
    min_score: float = 0.0,
    days: int = 1,
    dry_run: bool = False,
) -> list:
    """从本地数据库读取文章并同步。"""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from app import create_app
        from models import db, Article
        from sqlalchemy import func
    except ImportError as e:
        print(f"[错误] 无法导入 Flask 应用：{e}")
        sys.exit(1)

    app = create_app()
    results = []

    with app.app_context():
        if article_ids:
            articles = Article.query.filter(Article.id.in_(article_ids)).all()
        else:
            cutoff = datetime.utcnow() - timedelta(days=days)
            articles = (
                Article.query
                .filter(Article.source == source)
                .filter(Article.pub_date >= cutoff)
                .filter(Article.score >= min_score)
                .order_by(func.date(Article.pub_date).desc(), Article.score.desc())
                .limit(top_n)
                .all()
            )

        if not articles:
            print(f"[提示] 无符合条件文章 (source={source}, days={days}, min_score={min_score})")
            return []

        print(f"[提示] 找到 {len(articles)} 篇待同步")
        for idx, article in enumerate(articles, 1):
            content = build_article_content(article)
            result  = sync_article(
                title=content["title"],
                summary=content["summary"],
                main=content["main"],
                dry_run=dry_run,
            )
            results.append({"article_id": article.id, "title": article.title, "result": result})
            if idx < len(articles) and not dry_run:
                time.sleep(1)

    return results


# ── CLI 入口 ──

def main():
    p = argparse.ArgumentParser(description="钛媒体文章同步发布工具")
    p.add_argument("--title",   type=str, help="文章标题（直接发布模式）")
    p.add_argument("--summary",  type=str, help="文章摘要")
    p.add_argument("--main",     type=str, help="文章正文")
    p.add_argument("--id",       type=int, nargs="+", help="指定文章 ID（可多个）")
    p.add_argument("--top",      type=int, default=1,  help="同步高分前 N 篇（默认 1）")
    p.add_argument("--days",     type=int, default=1,  help="查询近几天（默认 1）")
    p.add_argument("--source",   type=str, default="tmtpost",
                   choices=["tmtpost", "original"], help="数据源（默认 tmtpost）")
    p.add_argument("--min-score", type=float, default=0.0, dest="min_score",
                   help="最低综合分过滤（默认 0）")
    p.add_argument("--dry-run",  action="store_true", help="预览模式，不实际发送")
    args = p.parse_args()

    # 直接发布
    if args.title or args.summary or args.main:
        result = sync_article(
            title=args.title   or "",
            summary=args.summary or "",
            main=args.main     or "",
            dry_run=args.dry_run,
        )
        ok = "error" not in result
        print(f"\n{'='*55}")
        print(f"{'✅ 发布成功' if ok else '❌ 发布失败'}")
        return

    # 数据库模式
    results = sync_from_db(
        article_ids=args.id,
        top_n=args.top,
        source=args.source,
        min_score=args.min_score,
        days=args.days,
        dry_run=args.dry_run,
    )

    ok = sum(1 for r in results if "error" not in r["result"])
    print(f"\n{'='*55}")
    print(f"共 {len(results)} 篇，✅ 成功 {ok} | ❌ 失败 {len(results) - ok}")


if __name__ == "__main__":
    main()
