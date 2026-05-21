---
name: aihot-news
description: 从 AIHOT (https://aihot.virxact.com/all) 获取海外 AI 动态，含 Twitter 专家观点（AIHOT·X）和主流科技媒体聚合。支持 LLM 智能过滤非海外 AI 内容，输出中文摘要。
---

# AIHOT News Skill

从 [AIHOT](https://aihot.virxact.com/all) 抓取海外 AI 动态，返回格式化的中文新闻列表。

## 数据源

- **AIHOT·X**：Twitter 上 AI 领域专家/从业者的观点（最高优先级）
- **AIHOT·{domain}**：主流科技媒体、博客的 AI 相关报道

## 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `top_n` | int | 10 | 返回前 N 条 |
| `hours` | int | 48 | 时间窗口（小时），0=不限制 |
| `sent_file` | str | `memory/sent.json` | 记录文件路径，用于去重（默认开启） |
| `push_to_dingtalk` | bool | false | 是否推送到钉钉 |
| `push_sender` | str | `../../shared/push_sender.py` | push_sender.py 路径 |
| `translate` | bool | true | 是否翻译（AIHOT 已含中文摘要，此项保留兼容） |

## 用法

```bash
# 运行 skill（默认开启去重，记录到 memory/sent.json）
skill-service run aihot-news

# 指定参数
skill-service run aihot-news --param top_n=15 --param hours=24

# 推送到钉钉
skill-service run aihot-news --param push_to_dingtalk=true
```

## 输出格式

```
## 🤖 AIHOT 海外 AI 动态

## 1. {标题}
**摘要**：{中文摘要}
**时间**：{北京时间}
**来源**：AIHOT·X：{作者} 或 AIHOT·{域名}
**链接**：[url](url)
```

## 过滤逻辑

1. **LLM 智能过滤**（优先）：判断是否属于"海外 AI 相关新闻"
2. **关键词兜底**：LLM 不可用或失败时，排除明确的中国本土 AI 公司关键词
3. **去重**：URL 规范化 + 指纹去重 + 标题相似度去重

## 优先级

| 来源 | 优先级 |
|------|---------|
| AIHOT·X（Twitter 专家） | 最高 |
| AIHOT·{domain}（媒体聚合） | 中 |
| RSS 补充源（如接入） | 低 |
