# 智能对话 (Chat) 功能使用指南

## 📖 简介

**智能对话功能**是 Skill Service 的核心特性之一，让你可以用自然语言与系统交互，系统会自动理解你的意图，选择合适的 skill 并执行，无需手动指定 skill 名称！

### 核心优势

- ✅ **自然交互** - 无需记忆 skill 名称，用日常语言描述需求
- ✅ **智能匹配** - LLM 自动理解意图，选择最合适的 skill
- ✅ **参数提取** - 自动从输入中提取执行参数
- ✅ **灵活扩展** - 添加新 skill 后，chat 功能自动支持
- ✅ **调试友好** - 支持详细的执行过程调试

---

## 🚀 快速开始

### 1. 配置 LLM

使用 chat 功能前需要先配置 LLM（支持 OpenAI、Anthropic、本地模型等）：

#### OpenAI

```bash
# 添加 OpenAI 模型配置
skill-service llm add \
  --name openai-gpt4 \
  --provider openai \
  --model gpt-4 \
  --env-var OPENAI_API_KEY \
  --description "OpenAI GPT-4 模型"

# 查看配置状态
skill-service llm status

# 设置为当前模型
skill-service llm use openai-gpt4
```

#### 本地模型 (Ollama)

```bash
# 添加本地 Ollama 模型
skill-service llm add \
  --name local-llama2 \
  --provider local \
  --model llama2 \
  --base-url http://localhost:11434/v1 \
  --description "本地 Llama2 模型"

# 设置为当前模型
skill-service llm use local-llama2
```

#### Anthropic

```bash
# 添加 Anthropic Claude 模型
skill-service llm add \
  --name anthropic-claude \
  --provider anthropic \
  --model claude-3-sonnet-20240229 \
  --env-var ANTHROPIC_API_KEY \
  --description "Anthropic Claude 3"
```

### 2. 使用 Chat

配置完成后，就可以开始使用 chat 功能了！

#### CLI 方式

```bash
# 基础对话
skill-service chat "计算 5 加 3"

# 查看详细调试信息
skill-service chat "计算 5 加 3" --verbose

# JSON 格式输出
skill-service chat "计算 5 加 3" --format json
```

#### API 方式

```bash
# 发送对话请求
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "计算 5 加 3"
  }'
```

```python
# Python 示例
import requests

response = requests.post(
    'http://localhost:8000/api/v1/chat',
    json={'user_input': '计算 5 加 3'}
)

result = response.json()
print(f"执行结果: {result['execution']['result']}")
```

---

## 💬 使用示例

### 计算类任务

```bash
# 基础计算
skill-service chat "计算 5 加 3"
skill-service chat "10 乘以 20 等于多少"
skill-service chat "100 除以 4"

# 复杂计算
skill-service chat "计算 (5 + 3) * 2"
```

### 数据处理

```bash
# JSON 格式化
skill-service chat "帮我格式化这个 JSON: {\"name\":\"Alice\",\"age\":25}"

# 数据查询
skill-service chat "查询北京的天气"
skill-service chat "GitHub 今天有什么热门项目？"
```

### 内容生成

```bash
# 生成日报
skill-service chat "生成今天的 GitHub 日报"

# 博客写作
skill-service chat "写一篇关于 AI 技术的博客"
```

### 自然语言计算器

```bash
# 使用自然语言描述计算需求
skill-service chat "我买了3个苹果，每个5元，一共多少钱？"
skill-service chat "如果我有100元，买4本书，每本15元，还剩多少钱？"
```

---

## 🔧 高级功能

### 1. 详细调试模式

使用 `--verbose` 选项查看详细的执行过程：

```bash
skill-service chat "计算 5 加 3" --verbose
```

输出示例：

```
👤 用户: 计算 5 加 3
================================================================================

🔧 调试信息:
  current_model: openai-gpt4
  provider: openai
  model: gpt-4

🤖 选择分析:
  Skill: calculator
  置信度: 0.95
  理由: 用户要求执行数学计算操作，calculator skill 可以完成
  参数: {'operation': 'add', 'a': 5, 'b': 3}

🚀 执行 skill: calculator

✅ 执行成功!

📝 输出内容:
--------------------------------------------------------------------------------
8
================================================================================
```

### 2. JSON 格式输出

使用 `--format json` 选项获取结构化的 JSON 输出：

```bash
skill-service chat "计算 5 加 3" --format json
```

输出示例：

```json
{
  "user_input": "计算 5 加 3",
  "success": true,
  "selection": {
    "skill_name": "calculator",
    "confidence": 0.95,
    "reasoning": "用户要求执行数学计算操作",
    "parameters": {
      "operation": "add",
      "a": 5,
      "b": 3
    },
    "direct_response": null
  },
  "execution": {
    "success": true,
    "result": {
      "output": "8",
      "data": {
        "operation": "add",
        "a": 5,
        "b": 3
      }
    },
    "execution_time": 0.123,
    "logs": []
  }
}
```

### 3. 多模型切换

可以配置多个 LLM 模型，根据需要切换：

```bash
# 列出所有配置的模型
skill-service llm list

# 切换到另一个模型
skill-service llm use local-llama2

# 再次执行 chat
skill-service chat "计算 5 加 3"  # 现在使用本地模型
```

---

## 🏗️ 工作原理

### 处理流程

```
┌─────────────────────────────────────────────────────────┐
│                    1. 用户输入                          │
│              "计算 5 加 3"                              │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│              2. LLM 智能分析                          │
│         - 理解用户意图                                  │
│         - 识别关键信息                                  │
│         - 提取参数                                      │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│              3. Skill 匹配                              │
│    - 遍历所有可用 skills                                 │
│    - 计算匹配度                                         │
│    - 选择最佳 skill                                     │
│    - Skill: calculator (置信度: 0.95)                   │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│              4. 参数提取                                │
│    - operation: "add"                                  │
│    - a: 5                                              │
│    - b: 3                                              │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│              5. 执行 Skill                             │
│         calculator.add(5, 3) = 8                        │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│              6. 返回结果                                │
│         ✅ 执行成功! 结果: 8                            │
└─────────────────────────────────────────────────────────┘
```

### Skill 选择策略

LLM 会根据以下因素选择最合适的 skill：

1. **意图匹配** - 理解用户的真实需求
2. **关键词识别** - 识别关键术语和实体
3. **上下文理解** - 考虑对话上下文（如果支持）
4. **置信度评分** - 为每个候选 skill 计算置信度
5. **最佳选择** - 选择置信度最高的 skill

如果没有任何 skill 匹配，LLM 会返回直接回复而不是执行 skill。

---

## 📊 API 参考

### CLI 命令

```bash
skill-service chat [OPTIONS] USER_INPUT

选项:
  -v, --verbose    显示详细的调试信息
  -f, --format     输出格式 [text|json]
  --help          显示帮助信息
```

### HTTP API

**端点**: `POST /api/v1/chat`

**请求体**:

```json
{
  "user_input": "计算 5 加 3"
}
```

**响应体**:

```json
{
  "success": true,
  "user_input": "计算 5 加 3",
  "selection": {
    "skill_name": "calculator",
    "confidence": 0.95,
    "reasoning": "用户要求执行数学计算操作",
    "parameters": {
      "operation": "add",
      "a": 5,
      "b": 3
    },
    "direct_response": null
  },
  "execution": {
    "success": true,
    "result": {
      "output": "8",
      "data": {
        "operation": "add",
        "a": 5,
        "b": 3
      }
    },
    "execution_time": 0.123,
    "logs": []
  },
  "timestamp": "2026-03-19T10:30:00"
}
```

**响应字段说明**:

- `success` - 请求是否成功
- `user_input` - 用户输入的文本
- `selection` - skill 选择信息
  - `skill_name` - 选择的 skill 名称（如果没有匹配则为 null）
  - `confidence` - 匹配置信度（0-1）
  - `reasoning` - 选择理由
  - `parameters` - 提取的参数
  - `direct_response` - 直接回复（如果没有匹配 skill）
- `execution` - 执行结果（如果选择了 skill）
  - `success` - 执行是否成功
  - `result` - 执行结果
  - `error` - 错误信息（如果失败）
  - `execution_time` - 执行时间（秒）
  - `logs` - 执行日志
- `error` - 错误信息（如果请求失败）
- `timestamp` - 响应时间戳

---

## ⚙️ 配置说明

### LLM 配置

Chat 功能依赖 LLM 进行智能理解和选择。支持以下 LLM 提供商：

1. **OpenAI**
   - 模型: gpt-3.5-turbo, gpt-4, gpt-4-turbo
   - 需要环境变量: `OPENAI_API_KEY`

2. **Anthropic**
   - 模型: claude-3-opus, claude-3-sonnet
   - 需要环境变量: `ANTHROPIC_API_KEY`

3. **本地模型**
   - 支持 Ollama、LocalAI 等本地 LLM 服务
   - 需要提供 base_url

4. **Azure OpenAI**
   - 支持 Azure 托管的 OpenAI 模型
   - 需要 API Key 和 Endpoint

### 环境变量配置

在 `.env` 文件中配置 API 密钥：

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Azure OpenAI
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://...

# 本地模型（如果需要认证）
LOCAL_LLM_KEY=...
```

---

## 🎯 最佳实践

### 1. 清晰的表达

使用清晰、明确的语言描述需求：

```bash
# ✅ 好
skill-service chat "计算 5 加 3"

# ❌ 不好
skill-service chat "5 3"
```

### 2. 合理的参数

在输入中明确提供所需参数：

```bash
# ✅ 好
skill-service chat "查询北京的天气"

# ❌ 不好
skill-service chat "查询天气"  # 不知道查询哪个城市
```

### 3. 利用调试模式

开发或调试时使用 `--verbose` 查看详细过程：

```bash
skill-service chat "计算 5 加 3" --verbose
```

### 4. 合理选择模型

- **简单任务** - 使用较便宜的模型（gpt-3.5-turbo）
- **复杂任务** - 使用更强大的模型（gpt-4）
- **本地测试** - 使用本地模型节省成本

### 5. 错误处理

如果 chat 功能无法理解你的需求：

1. 使用 `--verbose` 查看分析过程
2. 尝试更明确的表达
3. 考虑直接使用 `skill-service run` 命令

---

## 🔍 常见问题

### Q1: Chat 功能无法工作？

**可能原因**:
- 未配置 LLM
- LLM API Key 无效
- 网络连接问题

**解决方案**:
```bash
# 检查 LLM 配置
skill-service llm status

# 配置 LLM
skill-service llm add --name my-model --provider openai --model gpt-4

# 测试 API 连接
skill-service chat "你好"
```

### Q2: 选择的 skill 不正确？

**可能原因**:
- 输入描述不够清晰
- skills 之间功能重叠

**解决方案**:
- 使用更明确的描述
- 查看详细分析过程 `--verbose`
- 直接使用 `skill-service run` 命令

### Q3: 参数提取不准确？

**可能原因**:
- 输入格式不规范
- 复杂的参数结构

**解决方案**:
- 使用标准格式描述参数
- 使用 `--verbose` 查看提取的参数
- 直接使用 `skill-service run` 并手动指定参数

### Q4: 响应速度慢？

**可能原因**:
- 使用了较慢的 LLM 模型
- 网络延迟

**解决方案**:
- 切换到更快的模型（gpt-3.5-turbo）
- 使用本地模型
- 检查网络连接

### Q5: 如何支持连续对话？

当前版本的 chat 功能是无状态的，每次对话都是独立的。如需支持连续对话，可以在应用层维护对话历史。

---

## 📚 相关文档

- [快速开始指南](QUICKSTART.md)
- [CLI 使用文档](cli_usage.md)
- [API 使用文档](api_usage.md)
- [LLM 配置指南](../README.md#llm-配置)

---

## 🤝 贡献

如果你对 chat 功能有任何改进建议，欢迎提交 Issue 或 Pull Request！

---

**最后更新**: 2026-03-19
