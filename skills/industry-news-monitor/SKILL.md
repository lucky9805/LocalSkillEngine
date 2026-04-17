---
name: industry-news-monitor
description: "监控新消费、3C电子、汽车三大领域的最新资讯。当用户需要获取这些行业的最新动态、新闻资讯、行业趋势时说动使用。触发场景：'监控新消费新闻'、'3C电子最新资讯'、'汽车行业新闻'、'给我看看今天的行业新闻'、'行业资讯推送'等。"
---

# 行业资讯监控 Skill

## 目的

全网覆盖「新消费」「3C电子」「汽车」三大领域的最新 24 小时资讯，多源抓取、智能分类、去重推送。

## 监控领域

| 领域 | 说明 | 覆盖范围 |
|------|------|----------|
| 新消费 | 新零售、品牌、电商、消费趋势 | 36kr、虎嗅、第一财经等 |
| 3C电子 | 手机、电脑、数码、智能硬件 | IT之家、爱范儿、极客公园等 |
| 汽车 | 新车发布、行业动态、技术趋势 | 汽车之家、太平洋汽车等 |

## 数据源

### RSS 源配置

可在 `scripts/main.py` 的 `RSS_SOURCES` 中增删源。

### 抓取策略

1. 并行抓取所有 RSS 源（超时 15s/源，单源失败不影响整体）
2. 时间窗口过滤：只保留 24 小时内的条目
3. URL 去重：同一条新闻多源报道只保留一条
4. LLM 智能分类：判断条目属于哪个领域，过滤无关内容
5. 分领域输出，每个领域独立 Markdown 输出

## 执行方式

### CLI 方式

```bash
skill-service run industry-news-monitor --param push_to_dingtalk=true --param top_n=20
skill-service run industry-news-monitor --param domains=3C电子 --param top_n=10
skill-service run industry-news-monitor --param hours=12 --param dry_run=true
```

### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| top_n | int | 20 | 每领域最多推送条数 |
| hours | int | 24 | 抓取时间窗口（小时） |
| domains | str | all | 监控领域，`all`/新消费/3C电子/汽车，逗号分隔 |
| push_to_dingtalk | bool | false | 是否推送到钉钉 |
| dry_run | bool | true | dry_run 模式，只输出不推送 |
| sent_file | str | memory/sent.json | 去重记录文件 |

## 输出格式

```
## 【新消费】今日资讯（3条）

1. [标题]
   **摘要**：...
   **来源**：36kr · 2小时前
   **链接**：url

## 【3C电子】今日资讯（5条）
...

## 【汽车】今日资讯（2条）
...
```

## 去重机制

- 基于 URL 精确去重，已推送的 URL 不会重复推送
- 状态文件：`memory/sent.json`
