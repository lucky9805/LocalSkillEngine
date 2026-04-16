---
name: todayhub-monitor
description: 监控今日热榜（tophub.today/topics）上的 AI 相关新闻，过滤股票/广告类内容，去重后推送到钉钉。
---

# TodayHub AI 新闻监控

抓取今日热榜话题页，提取 AI 相关新闻，去重推送到钉钉。

## 功能

1. **抓取**：从 `https://tophub.today/topics?orderby=time` 抓取最新话题
2. **过滤**：保留 AI 相关新闻，排除 AI 股票/广告/财报类
3. **去重**：记录已推送新闻，避免重复推送
4. **推送**：通过 `../shared/push_sender.py` 推送到钉钉

## 参数

- `top_n` (可选): 最多推送 N 条，默认 `10`
- `sent_file` (可选): 去重记录文件路径，默认 `memory/sent.json`
- `push_to_dingtalk` (可选): 是否推送到钉钉，默认 `false`
- `push_sender` (可选): push_sender.py 路径，默认 `../../shared/push_sender.py`
- `dry_run` (可选): 只输出不推送，默认 `false`

## 输出格式

```
## 今日热榜 AI 动态（N条）

## 1. 标题
**摘要**：xxx
**时间**：发布时间
**链接**：[url](url)
```

## 使用示例

```bash
# 基本使用
skill-service run todayhub-monitor

# 推送到钉钉
skill-service run todayhub-monitor --param push_to_dingtalk=true

# 只测试不推送
skill-service run todayhub-monitor --param dry_run=true --param top_n=5
```

## Cron 定时任务

推荐每 2 小时运行一次：
- `top_n=10 push_to_dingtalk=true`
