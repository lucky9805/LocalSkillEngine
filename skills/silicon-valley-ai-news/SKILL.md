---
name: silicon-valley-ai-news
description: 实时监控硅谷 AI 领域热门新闻和产品发布，聚合 OpenAI、Google DeepMind、NVIDIA 等 AI 巨头官方博客以及 TechCrunch、Wired 等权威科技媒体，实时推送 AI 行业动态。
---

# Silicon Valley AI News

实时扫描硅谷 AI 新闻，推送到指定渠道。

## 新闻源

### 一级源（AI 巨头官方）
- OpenAI: https://openai.com/blog/rss.xml
- Google AI: https://blog.google/technology/ai/rss
- DeepMind: https://deepmind.com/blog/feed
- Microsoft AI: https://blogs.microsoft.com/ai/feed/
- NVIDIA: https://blogs.nvidia.com/feed/
- AWS ML Blog: https://aws.amazon.com/blogs/machine-learning/feed/
- Engineering at Meta: https://engineering.fb.com/feed/

### 二级源（权威科技媒体）
- TechCrunch AI: https://techcrunch.com/category/artificial-intelligence/feed/
- Wired AI: https://www.wired.com/feed/tag/ai/latest/rss
- VentureBeat AI: https://venturebeat.com/category/ai/feed/
- MIT Tech Review: https://www.technologyreview.com/feed/
- MIT News AI: https://news.mit.edu/rss/topic/artificial-intelligence2
- IEEE Spectrum AI: https://spectrum.ieee.org/customfeeds/feed/all-topics/rss
- Ars Technica: https://feeds.arstechnica.com/arstechnica/technology-lab
- The Verge AI: https://www.theverge.com/rss/ai-artificial-intelligence/index.xml
- Cloudflare AI: https://blog.cloudflare.com/tag/ai/rss/

### 三级源（技术社区）
- KDnuggets: https://www.kdnuggets.com/feed
- Analytics Vidhya: https://www.analyticsvidhya.com/feed/

## 参数

- `top_n` (可选): 返回前 N 条新闻，默认 `10`
- `hours` (可选): 过滤最近 N 小时的新闻，默认 `24`
- `sent_file` (可选): 已发送新闻记录文件路径（相对路径），默认 `memory/sent.json`（自动开启去重）
  - 设置为空字符串 `""` 可以禁用去重，每次返回所有新闻
- `translate` (可选): 是否翻译成中文，默认 `true`（需要 LLM 支持）
- `model` (可选): 指定 LLM 模型（用于翻译），默认使用系统默认模型
- `push_to_dingtalk` (可选): 是否推送到钉钉，默认 `false`
- `push_sender` (可选): push_sender.py 脚本路径（相对路径），默认 `../../shared/push_sender.py`（共享脚本）

## 执行流程

1. **扫描新闻**：并行获取所有 RSS 源
2. **AI 筛选**：根据关键词筛选 AI 相关新闻
3. **时间过滤**：只保留最近 N 小时的新闻（`hours` 参数）
4. **去重检查**：读取 `sent_file`，过滤已发送的（如配置）
5. **优先级排序**：按来源优先级和时间排序
6. **翻译**：将标题和摘要翻译成中文（`translate` 参数，需要 LLM）
7. **输出结果**：返回 Markdown 格式的新闻列表

## 输出格式

```
## 🤖 硅谷AI最新动态

### 1. 标题
**摘要**：xxx
**时间**：2026年2月25日 xx:xx (北京时间)
**来源**：OpenAI
**链接地址**：[https://xxx](https://xxx)

---
```

## 使用示例

```bash
# 基本使用（默认开启去重）
skill-service run silicon-valley-ai-news

# 自定义参数（去重自动开启）
skill-service run silicon-valley-ai-news --param top_n=5 --param hours=12

# 推送到钉钉
skill-service run silicon-valley-ai-news --param push_to_dingtalk=true

# 禁用去重（每次返回所有新闻）
skill-service run silicon-valley-ai-news --param sent_file=""

# 自定义去重文件路径
skill-service run silicon-valley-ai-news --param sent_file=cache/news.json
```

## Cron 定时任务

推荐配置：
- 每 6 小时执行一次：`top_n=10 hours=6 push_to_dingtalk=true`
- 每天早上 9 点执行：`top_n=20 hours=24 push_to_dingtalk=true`

> **注意**：
> - 去重已默认开启，无需手动配置 `sent_file` 参数
> - 钉钉推送需要 `../../tools/push_sender.py` 配置好 WEBHOOK_URL 和 SECRET
