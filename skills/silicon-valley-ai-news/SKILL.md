---
name: silicon-valley-ai-news
description: 实时监控硅谷 AI 领域热门新闻和产品发布，聚合 RSS 官方/媒体源 + AIHOT 补充源，覆盖 AI 巨头官方博客、权威科技媒体、Twitter 专家观点等，实时推送 AI 行业动态。
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

### 补充源（AIHOT）
- AIHOT: https://aihot.virxact.com/all
  - 聚合 X（Twitter）AI 专家观点、RSS 新闻、论文等
  - 来源标记：`AIHOT·X：{author}`（Twitter）、`AIHOT·{source_name}`（其他）
  - 自动 LLM 过滤：仅保留海外 AI 相关，排除中国本土内容
  - AIHOT 条目最多占输出总数的 60%

## 优先级排序

1. **AIHOT·X**（Twitter 专家观点）— 最高优先
2. **二级科技媒体**（TechCrunch、Wired 等）
3. **AIHOT 其他来源**（RSS/论文/网页聚合）
4. **三级技术社区**
5. **一级官方博客**（OpenAI/Google/DeepMind 等）— 降权，无重大新闻时不占位

## 参数

- `top_n` (可选): 返回前 N 条新闻，默认 `10`
- `hours` (可选): 过滤最近 N 小时的新闻，默认 `24`
- `sent_file` (可选): 已发送新闻记录文件路径（相对路径），默认 `memory/sent.json`（自动开启去重）
  - 设置为空字符串 `""` 可以禁用去重，每次返回所有新闻
- `translate` (可选): 是否翻译成中文，默认 `true`（需要 LLM 支持）
- `model` (可选): 指定 LLM 模型（用于翻译和 AIHOT 过滤），默认使用系统默认模型
- `push_to_dingtalk` (可选): 是否推送到钉钉，默认 `false`
- `push_sender` (可选): push_sender.py 脚本路径（相对路径），默认 `../../shared/push_sender.py`（共享脚本）

## 执行流程

1. **并行抓取**：RSS 源 + AIHOT 补充源同时获取
2. **AIHOT 过滤**：LLM 智能判断海外 AI 相关（降级到关键词兜底）
3. **URL 去重**：AIHOT 与 RSS 之间 URL 去重
4. **AI 筛选**：RSS 条目根据关键词筛选 AI 相关新闻
5. **时间过滤**：只保留最近 N 小时的新闻
6. **去重检查**：读取 `sent_file`，过滤已发送/已选中的
7. **标题相似度去重**：同一新闻多来源报道
8. **优先级排序**：按来源优先级和时间排序
9. **AIHOT 比例限制**：AIHOT 最多占 60%
10. **翻译**：RSS 条目标题和摘要翻译成中文（AIHOT 已是中文，跳过）
11. **生成摘要**：为缺少摘要的新闻生成一句话摘要
12. **输出结果**：返回 Markdown 格式的新闻列表

## 输出格式

```
## 🤖 硅谷AI最新动态

## 1.标题
**摘要**：xxx
**时间**：2026年2月25日 xx:xx (北京时间)
**来源**：AIHOT·X：swyx
**链接**：[https://xxx](https://xxx)

## 2.标题
**摘要**：xxx
**时间**：2026年2月25日 xx:xx (北京时间)
**来源**：TechCrunch AI
**链接**：[https://xxx](https://xxx)
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
> - 钉钉推送需要 `../../shared/push_sender.py` 配置好 WEBHOOK_URL 和 SECRET
> - AIHOT 过滤需要 LLM 支持，无 LLM 时自动降级到关键词过滤
