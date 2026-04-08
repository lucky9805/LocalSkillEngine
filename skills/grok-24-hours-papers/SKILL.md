---
name: grok-24-hours-papers
description: 使用本地 opencli 调用 Grok，抓取过去 24 小时内 Twitter 上高互动论文相关推文，整理成固定 Markdown 并通过 shared/push_sender.py 推送。
---

# Grok 24 Hours Papers

按固定流程执行：

1. 在 `/Users/renhongyu/data/python/opencli` 下调用：
   `node dist/main.js grok ask "<论文抓取prompt>" --stream --timeout 300`
2. 将返回内容整理成固定格式：
   `## 1.标题 / 摘要 / 时间 / 论文地址 / x链接`
3. 调用 `../../shared/push_sender.py` 推送内容。

## 输出格式

```markdown
## 1.标题

**摘要**：摘要

**时间**：发布时间

**论文地址**：[论文地址](论文地址)

**x链接**：[真实链接地址](真实链接地址)
```

## 参数

- `fetch_timeout` (可选): 抓取超时，默认 `300`
- `push_to_dingtalk` (可选): 是否推送，默认 `true`
- `push_sender` (可选): push_sender.py 路径，默认 `../../shared/push_sender.py`

## 使用示例

```bash
skill-service run grok-24-hours-papers
skill-service run grok-24-hours-papers --param push_to_dingtalk=false
```
