---
name: gemini-24-hours-news
description: 使用本地 opencli 调用 Gemini，先抓取最近 24 小时 AI 新闻，再二次整理为标准 Markdown 格式，并通过 shared/push_sender.py 推送。
---

# Gemini 24 Hours News

按固定三步执行：

1. 在 `/Users/renhongyu/data/python/opencli` 下运行：
   `node dist/main.js gemini ask "帮我整理最近24小时..." --stream --timeout 300`
2. 将第一步返回内容再次交给 Gemini 整理为固定格式：
   `## 1.标题 / 摘要 / 时间 / 链接地址`
3. 调用 `../../shared/push_sender.py` 推送内容。

## 输出格式

```markdown
## 🤖 Gemini 24 Hours News

## 1.标题

**摘要**：摘要

**时间**：时间

**链接地址**：[真实链接地址](真实链接地址)
```

## 参数

- `fetch_timeout` (可选): 第一步抓取超时，默认 `300`
- `format_timeout` (可选): 第二步整理超时，默认 `120`
- `push_to_dingtalk` (可选): 是否推送，默认 `true`
- `push_sender` (可选): push_sender.py 路径，默认 `../../shared/push_sender.py`

## 使用示例

```bash
skill-service run gemini-24-hours-news
skill-service run gemini-24-hours-news --param push_to_dingtalk=false
```
