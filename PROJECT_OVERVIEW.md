# Skill Service 项目概览

## 🚀 项目简介

**Skill Service** 是一个功能强大的本地 Skill 运行服务，支持通过命令行和 HTTP API 运行和管理自定义 skills。

### 核心特性

- 📝 **灵活的 Skill 系统** - 轻松创建和管理自定义 skills
- 🖥️ **命令行接口** - 完整的 CLI 工具，支持所有核心功能
- 🌐 **HTTP API 服务** - RESTful API，易于集成到现有系统
- 🔧 **热更新** - 无需重启即可更新 skills
- 📊 **详细日志** - 完整的执行日志和错误追踪
- 🚀 **高性能** - 基于 FastAPI 的异步处理
- 📚 **自动文档** - Swagger UI 和 ReDoc 自动生成
- 🧪 **完整测试** - 单元测试和集成测试覆盖
- 🤖 **LLM 集成** - 支持多个 LLM 提供商，智能代码生成
- 💬 **智能对话** - 自然语言交互，自动选择并执行 skill（推荐！）

---

## 📁 项目结构

```
localskill/
├── 📄 README.md                    # 项目说明
├── 📄 DESIGN.md                    # 架构设计
├── 📄 setup.py                     # 安装配置
├── 📄 requirements.txt             # 依赖清单
│
├── 📁 skill_service/              # 核心代码包
│   ├── 📄 cli.py                   # CLI 接口
│   ├── 📄 loader.py                # Skill 加载器
│   ├── 📄 runner.py                # Skill 执行器
│   ├── 📄 nl_generator.py         # 自然语言生成器
│   ├── 📁 api/                     # HTTP API
│   ├── 📁 llm/                     # LLM 集成
│   ├── 📁 storage/                 # 存储
│   └── 📁 utils/                   # 工具
│
├── 📁 skills/                      # 示例 Skills (8个)
│   ├── calculator/
│   ├── json-formatter/
│   ├── weather-query/
│   ├── github-daily-rank/
│   ├── self-improve/
│   ├── calculator-nl/
│   ├── blog-writer-nl/
│   └── news-fetcher-nl/
│
├── 📁 tests/                       # 测试代码
│
├── 📁 examples/                    # 文档和示例
│
└── 📁 bak/                         # 备份目录
```

---

## ⚡ 快速开始

### 安装

```bash
# 克隆项目
git clone <repository-url>
cd localskill

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 开发模式安装
pip install -e .
```

### 命令行使用

```bash
# 查看版本
skill-service --version

# 列出所有 skills
skill-service list

# 查看 skill 详情
skill-service info greeting

# 运行 skill
skill-service run calculator --param operation=add --param a=5 --param b=3

# 🤖 智能对话 - 自动选择并执行 skill（推荐！）
skill-service chat "计算 5 加 3"
skill-service chat "帮我格式化这个 JSON"
skill-service chat "查询北京的天气"

# 启动 API 服务
skill-service serve --port 8000

# 重新加载 skills
skill-service reload
```

### API 使用

```bash
# 健康检查
curl http://localhost:8000/health

# 列出所有 skills
curl http://localhost:8000/api/v1/skills

# 运行 skill
curl -X POST http://localhost:8000/api/v1/skills/calculator/run \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"operation": "add", "a": 5, "b": 3}}'

# 🤖 智能对话 - 自动选择并执行 skill
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"user_input": "计算 5 加 3"}'

curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"user_input": "帮我格式化这个 JSON"}'

# 访问 API 文档
open http://localhost:8000/docs
```

---

## 🔧 技术栈

### 核心技术

- **Python** 3.8+ - 编程语言
- **FastAPI** - 现代、快速的 Web 框架
- **Uvicorn** - ASGI 服务器
- **Click** - CLI 框架
- **Pydantic** - 数据验证
- **PyYAML** - YAML 解析

### 依赖库

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
click>=8.1.0
pyyaml>=6.0
aiofiles>=23.2.0
python-dotenv>=1.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
requests>=2.31.0
pytest>=7.4.0
httpx>=0.25.0
```

---

## 📚 内置 Skills

### 1. Calculator
支持基本数学运算的计算器。

```bash
skill-service run calculator \
  --param operation=add \
  --param a=5 \
  --param b=3
```

### 2. JSON Formatter
JSON 格式化和压缩工具。

```bash
skill-service run json-formatter \
  --json-params '{"data":{"name":"Alice"},"mode":"pretty"}'
```

### 3. Weather Query
天气查询技能。

```bash
skill-service run weather-query \
  --param city="Beijing"
```

### 4. GitHub Daily Rank
GitHub 日报生成技能。

```bash
skill-service run github-daily-rank
```

### 5. Natural Language Skills
支持自然语言交互的计算器、博客写作和新闻获取技能。

```bash
# 自然语言计算
skill-service run calculator-nl --param prompt="计算 5 + 3"

# 自然语言博客写作
skill-service run blog-writer-nl --param topic="AI 技术"

# 自然语言新闻获取
skill-service run news-fetcher-nl --param topic="科技"
```

### 6. 🤖 智能对话模式（推荐！）

**智能对话功能**让你可以用自然语言与系统交互，系统会自动理解你的意图，选择合适的 skill 并执行，无需手动指定 skill 名称！

#### CLI 方式

```bash
# 基础对话
skill-service chat "计算 5 加 3"
skill-service chat "帮我格式化这个 JSON"
skill-service chat "查询北京的天气"
skill-service chat "生成今天的 GitHub 日报"

# 显示详细调试信息
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

# Python 示例
import requests

response = requests.post(
    'http://localhost:8000/api/v1/chat',
    json={'user_input': '计算 5 加 3'}
)

result = response.json()
print(f"结果: {result['execution']['result']}")
```

#### Chat 功能特点

- ✅ **智能理解**: 使用 LLM 理解自然语言意图
- ✅ **自动选择**: 自动匹配最合适的 skill
- ✅ **参数提取**: 自动从用户输入中提取参数
- ✅ **灵活对话**: 支持自然语言对话，无需记忆 skill 名称
- ✅ **调试模式**: 可显示详细的技能选择和执行过程

#### 工作流程

```
用户输入 (自然语言)
    ↓
LLM 智能分析意图
    ↓
自动匹配最佳 Skill
    ↓
提取执行参数
    ↓
执行 Skill
    ↓
返回结果
```

#### 配置要求

使用 chat 功能前需要配置 LLM：

```bash
# 配置 OpenAI
skill-service llm add \
  --name openai-gpt4 \
  --provider openai \
  --model gpt-4 \
  --env-var OPENAI_API_KEY

# 配置本地模型（如 Ollama）
skill-service llm add \
  --name local-llm \
  --provider local \
  --model llama2 \
  --base-url http://localhost:11434/v1

# 查看配置状态
skill-service llm status

# 切换模型
skill-service llm use openai-gpt4
```

---

## 🏗️ 架构设计

### 核心模块

```
┌─────────────────────────────────────┐
│          CLI Interface              │
│         (命令行接口)                 │
└────────────┬────────────────────────┘
             │
┌────────────┴────────────────────────┐
│          HTTP API Server           │
│         (FastAPI 服务)              │
└────────────┬────────────────────────┘
             │
┌────────────┴────────────────────────┐
│          Request Router            │
│          (请求路由器)                │
└─────┬───────┬───────┬──────────────┘
      │       │       │
┌─────▼──┐ ┌──▼─────┐ ┌▼──────────┐
│Skill   │ │Skill   │ │ LLM      │
│Loader  │ │Runner  │ │Generator │
└────┬───┘ └──┬─────┘ └───────────┘
     │        │
     └───┬────┘
         ▼
┌──────────────────┐
│  Skill Storage   │
│  (技能库)         │
└──────────────────┘
```

### 数据流

1. **用户请求** → CLI 或 HTTP API
2. **路由解析** → 请求路由器
3. **Skill 加载** → Skill Loader
4. **Skill 执行** → Skill Runner 或 LLM Generator
5. **结果返回** → 格式化输出

---

## 📖 创建自定义 Skill

### 1. 创建 skill 目录

```bash
mkdir skills/my-skill
mkdir skills/my-skill/scripts
```

### 2. 创建 SKILL.md

```markdown
---
name: my-skill
version: 1.0.0
author: Your Name
category: utility
description: My custom skill
---

## 简介

描述你的 skill 功能...

## 脚本

### main.py
\`\`\`python
def execute(parameters):
    return "Hello from my skill!"
\`\`\`
```

### 3. 创建执行脚本

```python
# skills/my-skill/scripts/main.py

def execute(parameters):
    """执行你的 skill 逻辑"""
    name = parameters.get("name", "World")
    return f"Hello, {name}!"
```

### 4. 测试 skill

```bash
skill-service reload
skill-service run my-skill --param name="Test"
```

详细文档请查看 [Skill Template](examples/SKILL_TEMPLATE.md)。

---

## 🧪 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_loader.py -v

# 查看测试覆盖率
pytest tests/ --cov=skill_service

# 运行特定函数
pytest tests/test_runner.py::test_execute_skill -v
```

---

## 📦 打包和发布

### 打包

```bash
# 清理旧文件
rm -rf build/ dist/ *.egg-info/

# 打包
python setup.py sdist bdist_wheel

# 检查结果
ls -lh dist/
```

### 安装测试

```bash
# 创建测试环境
python -m venv test_env
source test_env/bin/activate

# 安装打包文件
pip install dist/skill-service-0.1.0.tar.gz

# 测试
skill-service --version
```

### 发布到 PyPI

```bash
# 安装 twine
pip install twine

# 上传
twine upload dist/*
```

详细打包指南请查看 [Package Checklist](PACKAGE_CHECKLIST.md)。

---

## 📊 项目统计

- **代码文件**: 27 个 Python 文件
- **测试文件**: 4 个测试文件
- **示例 Skills**: 8 个示例
- **文档文件**: 12 个 Markdown 文档
- **依赖库**: 11 个
- **代码行数**: ~3000+ 行

---

## 🎯 使用场景

### 1. 命令行自动化
```bash
# 快速运行一个 skill
skill-service run calculator --param operation=multiply --param a=10 --param b=20

# 🤖 使用智能对话（推荐！）
skill-service chat "计算 10 乘以 20"
skill-service chat "今天的 GitHub 有什么热门项目？"
```

### 2. API 集成
```python
import requests

# 传统方式：指定 skill
response = requests.post(
    'http://localhost:8000/api/v1/skills/calculator/run',
    json={'parameters': {'operation': 'add', 'a': 5, 'b': 3}}
)
print(response.json())

# 🤖 智能对话方式：自然语言输入
response = requests.post(
    'http://localhost:8000/api/v1/chat',
    json={'user_input': '计算 5 加 3'}
)
print(response.json())
```

### 3. 微服务部署
- 通过 HTTP API 集成到现有系统
- 作为微服务部署
- 在 CI/CD 流程中使用

### 4. 自然语言助手
```bash
# 日常任务助手
skill-service chat "帮我查询北京的天气"
skill-service chat "生成一份 GitHub 日报"
skill-service chat "格式化这个 JSON 数据"

# 开发助手
skill-service chat "分析这个项目的结构"
skill-service chat "生成项目文档"
```

---

## 🔒 安全说明

- ⚠️ **不要在代码中硬编码 API 密钥**
- ✅ 使用 `.env` 文件管理敏感信息
- ✅ `.env` 文件已在 `.gitignore` 中排除
- ✅ 使用 `.env.example` 作为模板

---

## 🤝 贡献

欢迎贡献代码！请查看 [Development Guide](examples/DEVELOPMENT.md) 了解详细信息。

### 贡献步骤

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

MIT License - 详见 LICENSE 文件

---

## 📞 联系方式

- **项目地址**: https://github.com/yourusername/skill-service
- **文档**: https://github.com/yourusername/skill-service/wiki
- **问题反馈**: https://github.com/yourusername/skill-service/issues

---

## 📚 相关文档

- [项目结构说明](PROJECT_STRUCTURE.md) - 详细的项目结构
- [打包清单](PACKAGE_CHECKLIST.md) - 打包和发布指南
- [整理总结](CLEANUP_SUMMARY.md) - 项目整理记录
- [快速开始](examples/QUICKSTART.md) - 5 分钟上手教程
- [CLI 使用文档](examples/cli_usage.md) - 命令行工具详细说明
- [API 使用文档](examples/api_usage.md) - HTTP API 完整指南
- [部署指南](examples/DEPLOYMENT.md) - 生产环境部署方案

---

## 🌟 支持

如果觉得这个项目有用，请给个 ⭐ Star！

---

**当前版本**: 0.1.0
**最后更新**: 2026-03-19
**状态**: ✅ 第一阶段完成，已准备好打包
