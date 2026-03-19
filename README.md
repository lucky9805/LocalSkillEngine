# Skill Service 🚀

一个功能强大的本地 Skill 运行服务，支持通过命令行和 HTTP API 运行和管理自定义 skills。

## ✨ 特性

- 📝 **灵活的 Skill 系统** - 轻松创建和管理自定义 skills
- 🖥️ **命令行接口** - 完整的 CLI 工具，支持所有核心功能
- 🌐 **HTTP API 服务** - RESTful API，易于集成到现有系统
- 🔧 **热更新** - 无需重启即可更新 skills
- 📊 **详细日志** - 完整的执行日志和错误追踪
- 🚀 **高性能** - 基于 FastAPI 的异步处理
- 📚 **自动文档** - Swagger UI 和 ReDoc 自动生成
- 🧪 **完整测试** - 单元测试和集成测试覆盖

## 🚀 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/lucky9805/LocalSkillEngine.git
cd skill-service

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 开发模式安装
pip install -e .
```

### 使用

#### 命令行方式

```bash
# 列出所有 skills
skill-service list

# 运行 skill
skill-service run greeting --param name="World"

# 🤖 智能对话 - 自动选择并执行 skill（推荐！）
skill-service chat "计算 5 加 3"
skill-service chat "查询北京的天气"

# 启动 API 服务
skill-service serve
```

#### API 方式

```python
import requests

# 运行 skill
response = requests.post(
    'http://localhost:8000/api/v1/skills/greeting/run',
    json={'parameters': {'name': 'World'}}
)

result = response.json()
print(f"结果: {result['result']}")

# 🤖 智能对话
response = requests.post(
    'http://localhost:8000/api/v1/chat',
    json={'user_input': '计算 5 加 3'}
)

result = response.json()
print(f"结果: {result['execution']['result']}")
```

## 📚 文档

- **[快速开始指南](examples/QUICKSTART.md)** - 5 分钟上手教程
- **[CLI 使用文档](examples/cli_usage.md)** - 命令行工具详细说明
- **[API 使用文档](examples/api_usage.md)** - HTTP API 完整指南
- **[部署指南](examples/DEPLOYMENT.md)** - 生产环境部署方案
- **[开发指南](examples/DEVELOPMENT.md)** - 贡献代码和扩展功能
- **[Skill 模板](examples/SKILL_TEMPLATE.md)** - 创建自定义 skill

## 📁 项目结构

```
skill-service/
├── skill_service/          # 核心代码包
│   ├── api/               # FastAPI 服务
│   ├── storage/           # Skill 存储
│   ├── utils/             # 工具模块
│   ├── models.py          # 数据模型
│   ├── loader.py          # Skill 加载器
│   ├── runner.py          # Skill 执行器
│   └── cli.py             # CLI 接口
├── skills/                # Skills 目录
│   ├── example/           # 示例 skill
│   ├── calculator/        # 计算器 skill
│   └── json-formatter/    # JSON 格式化 skill
├── tests/                 # 测试代码
├── examples/              # 示例和文档
├── DESIGN.md             # 架构设计
├── requirements.txt      # Python 依赖
└── setup.py             # 安装配置
```

## 🎯 内置 Skills

### 1. Greeting
简单的打招呼技能。

```bash
skill-service run greeting --param name="Alice"
```

### 2. Calculator
支持基本数学运算的计算器。

```bash
skill-service run calculator --param operation=add --param a=5 --param b=3
```

### 3. JSON Formatter
JSON 格式化和压缩工具。

```bash
skill-service run json-formatter \
  --json-params '{"data":{"name":"Alice"},"mode":"pretty"}'
```

## 🔧 CLI 命令

```bash
# 列出 skills
skill-service list

# 查看 skill 详情
skill-service info <skill-name>

# 运行 skill
skill-service run <skill-name> [options]

# 启动 API 服务
skill-service serve [--port 8000]

# 重新加载 skills
skill-service reload

# 查看版本
skill-service version
```

## 🌐 API 端点

- `GET /health` - 健康检查
- `GET /api/v1/skills` - 列出所有 skills
- `GET /api/v1/skills/{name}` - 获取 skill 详情
- `POST /api/v1/skills/{name}/run` - 运行 skill
- `POST /api/v1/skills/reload` - 重新加载 skills

访问 http://localhost:8000/docs 查看 API 文档。

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

更多详细信息，请查看 [Skill 模板](examples/SKILL_TEMPLATE.md)。

## 🧪 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_runner.py -v

# 查看测试覆盖率
pytest tests/ --cov=skill_service
```

## 📦 依赖

- **FastAPI** - 现代、快速的 Web 框架
- **Uvicorn** - ASGI 服务器
- **Click** - CLI 框架
- **Pydantic** - 数据验证
- **PyYAML** - YAML 解析
- **aiofiles** - 异步文件操作

完整依赖列表请查看 [requirements.txt](requirements.txt)。

## 🔄 开发模式

```bash
# 启动开发服务器（自动重载）
skill-service serve --reload

# 运行代码格式化
black skill_service/

# 运行类型检查
mypy skill_service/
```

## 📝 贡献

欢迎贡献代码！请查看 [开发指南](examples/DEVELOPMENT.md) 了解详细信息。

## 📄 许可证

MIT License - 详见 LICENSE 文件

## 🤝 社区

- GitHub Issues - 报告 bug 和请求功能
- GitHub Discussions - 讨论和交流
- Pull Requests - 贡献代码

## 🌟 支持

如果觉得这个项目有用，请给个 ⭐ Star！

## 📞 联系方式

- 作者: lucky9805
- 邮箱: lucky9805@163.com
- 项目地址: https://github.com/lucky9805/LocalSkillEngine.git

---

**开始使用 Skill Service，让自动化变得简单！** 🚀

