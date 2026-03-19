---
name: blog-writer-nl
description: 博客长文写作技能，支持选题研究、大纲规划、深度写作3000-10000字、SEO优化、人性化处理去掉AI味。具备Self-Improve能力，可收集反馈持续优化。当用户需要撰写博客文章、长文内容、SEO优化文章时使用此skill。
license: MIT
compatibility: Requires Python 3.9+
metadata:
  version: "1.1.0"
  author: Skill Service Team
  category: content_creation
  keywords:
    - blog
    - writing
    - SEO
    - content
    - article
    - self-improve
    - 博客
    - 写作
    - 文章
    - 自我改进
---

# 博客长文写作 (Blog Writer)

专业的博客长文写作工具，支持从选题到成稿的完整 workflow。

## When to use this skill

使用此 skill 当用户需要：
- 撰写博客文章或长文内容
- 进行选题研究和资料收集
- 创建文章大纲和结构规划
- 生成SEO优化的文章
- 去除AI写作痕迹，增加人性化表达
- 需要3000-10000字的深度内容
- 需要具备自我学习和改进能力的写作工具

## Features

### 核心功能
- ✅ **选题研究**: 自动分析话题类型和目标受众
- ✅ **大纲规划**: 智能生成文章结构和章节分配
- ✅ **深度写作**: 基于知识库生成高质量内容
- ✅ **SEO优化**: 自动生成标题、描述和关键词
- ✅ **人性化处理**: 去除AI痕迹，增加自然表达
- ✅ **文件保存**: 自动保存到本地 Markdown 文件

### Self-Improve 功能
- 📊 **执行分析**: 自动记录每次执行的性能指标
- 💡 **智能优化**: 基于历史数据优化写作策略
- 📈 **趋势追踪**: 监控成功率和用户满意度趋势
- 🔄 **持续学习**: 根据用户反馈不断改进输出质量
- 📋 **改进报告**: 生成详细的性能分析和优化建议

## How to use

### Parameters

- `topic` (required): 文章主题或标题
- `word_count` (optional): 目标字数，默认 3000，可选 3000/5000/8000/10000
- `style` (optional): 写作风格，默认 "professional"，可选 professional/casual/technical/storytelling
- `keywords` (optional): SEO关键词，多个用逗号分隔
- `outline` (optional): 是否只生成大纲，默认 "false"
- `humanize` (optional): 是否进行人性化处理，默认 "true"
- `save_to_file` (optional): 是否保存到文件，默认 "true"
- `output_dir` (optional): 文件保存目录，默认当前目录
- `enable_self_improve` (optional): 是否启用自我改进，默认 "true"

### Example

```bash
# 基础用法
skill-service run blog-writer-nl --param topic="人工智能在医疗领域的应用"

# 指定字数和风格
skill-service run blog-writer-nl \
  --param topic="Python异步编程指南" \
  --param word_count=5000 \
  --param style=technical

# 带SEO关键词
skill-service run blog-writer-nl \
  --param topic="云原生架构实践" \
  --param keywords="Kubernetes,微服务,容器化,DevOps" \
  --param word_count=8000

# 只生成大纲
skill-service run blog-writer-nl \
  --param topic="区块链技术与应用" \
  --param outline=true
```

## 写作流程

1. **选题研究**: 分析话题热度，收集相关资料
2. **大纲规划**: 结构化分段，确保逻辑清晰
3. **深度写作**: 按大纲逐段撰写，3000-10000字
4. **SEO优化**: 优化标题、关键词、meta描述
5. **人性化处理**: 调整语气，去除AI痕迹

## 输出格式

- 文章标题（SEO优化）
- Meta描述
- 关键词标签
- 正文内容（Markdown格式）
- 阅读时长估计
- 执行ID（用于提交反馈）
- 性能指标（成功率、字数精度等）

## Self-Improve 使用指南

### 1. 自动收集数据
每次执行时，Skill 会自动记录：
- 执行参数和结果
- 字数控制精度
- 执行耗时
- 成功/失败状态

### 2. 提交用户反馈
执行后会返回 `execution_id`，使用它来提交反馈：

```bash
# 提交评分（1-5分）
python scripts/main.py --feedback --execution-id exec_123456 --rating 5

# 提交评分和文字反馈
python scripts/main.py --feedback \
  --execution-id exec_123456 \
  --rating 4 \
  --feedback-text "内容很好，但希望能增加更多案例"
```

### 3. 查看改进报告
```bash
python scripts/main.py --report
```

报告包含：
- 📊 当前性能指标（成功率、字数精度、用户满意度）
- 📈 性能趋势（与历史数据对比）
- 💡 优化建议（基于数据分析的改进方向）
- 📋 常见错误分析

### 4. 优化策略说明
Skill 会根据历史数据自动优化：
- **字数控制**: 根据历史准确率动态调整缓冲因子
- **风格推荐**: 基于相似主题的历史评分推荐最佳风格
- **人性化处理**: 根据用户反馈调整人性化强度
