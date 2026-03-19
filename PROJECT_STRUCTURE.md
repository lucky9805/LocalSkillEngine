# Skill Service 项目结构说明

## 📦 项目整理完成

经过整理，项目已清理干净，保留了所有核心文件，临时文件已移动到 `bak/` 目录。

## 📁 最终项目结构

```
localskill/
├── 📄 README.md                    # 项目说明文档
├── 📄 DESIGN.md                    # 架构设计文档
├── 📄 requirements.txt             # Python 依赖清单
├── 📄 setup.py                     # 安装配置文件
├── 📄 .env                         # 环境变量配置
├── 📄 .env.example                 # 环境变量示例
├── 📄 .gitignore                   # Git 忽略规则
│
├── 📁 skill_service/              # 核心代码包
│   ├── 📄 __init__.py
│   ├── 📄 __main__.py
│   ├── 📄 cli.py                   # CLI 命令行接口
│   ├── 📄 config.py                # 配置管理
│   ├── 📄 loader.py                # Skill 加载器
│   ├── 📄 runner.py                # Skill 执行器
│   ├── 📄 models.py                # 数据模型定义
│   ├── 📄 migrator.py             # 数据迁移工具
│   ├── 📄 nl_generator.py         # 自然语言生成器
│   ├── 📄 scanner.py               # Skill 扫描器
│   ├── 📄 main.py                  # CLI 入口文件
│   │
│   ├── 📁 api/                     # HTTP API 服务
│   │   ├── 📄 __init__.py
│   │   ├── 📄 server.py           # FastAPI 服务器
│   │   ├── 📄 routes.py           # API 路由定义
│   │   └── 📄 schemas.py          # API 数据结构
│   │
│   ├── 📁 llm/                     # LLM 集成模块
│   │   ├── 📄 __init__.py
│   │   ├── 📄 config.py           # LLM 配置
│   │   ├── 📄 generator.py        # 代码生成器
│   │   ├── 📄 multi_model_config.py  # 多模型配置
│   │   ├── 📄 provider.py         # LLM 提供商接口
│   │   └── 📄 selector.py         # 模型选择器
│   │
│   ├── 📁 storage/                 # 存储模块
│   │   ├── 📄 __init__.py
│   │   └── 📄 skill_store.py      # Skill 存储管理
│   │
│   └── 📁 utils/                   # 工具模块
│       ├── 📄 __init__.py
│       ├── 📄 logger.py           # 日志工具
│       ├── 📄 validator.py        # 验证工具
│       └── 📄 validator_new.py    # 新版验证工具
│
├── 📁 skills/                      # 示例 Skills
│   ├── 📄 README.md               # Skills 说明文档
│   ├── 📁 calculator/             # 计算器 Skill
│   ├── 📁 json-formatter/         # JSON 格式化 Skill
│   ├── 📁 weather-query/          # 天气查询 Skill
│   ├── 📁 github-daily-rank/     # GitHub 日报 Skill
│   ├── 📁 self-improve/           # 自我改进 Skill
│   ├── 📁 calculator-nl/         # 自然语言计算器
│   ├── 📁 blog-writer-nl/         # 自然语言博客写作
│   └── 📁 news-fetcher-nl/        # 自然语言新闻获取
│
├── 📁 tests/                       # 测试代码
│   ├── 📄 __init__.py
│   ├── 📄 test_api.py            # API 测试
│   ├── 📄 test_cli.py            # CLI 测试
│   ├── 📄 test_loader.py         # 加载器测试
│   └── 📄 test_runner.py         # 执行器测试
│
├── 📁 examples/                    # 使用示例和文档
│   ├── 📄 QUICKSTART.md          # 快速开始指南
│   ├── 📄 cli_usage.md           # CLI 使用文档
│   ├── 📄 api_usage.md           # API 使用文档
│   ├── 📄 DEPLOYMENT.md          # 部署指南
│   ├── 📄 DEVELOPMENT.md         # 开发指南
│   ├── 📄 SKILL_TEMPLATE.md      # Skill 模板
│   ├── 📄 API_REFERENCE.md       # API 参考文档
│   ├── 📄 CONFIGURATION.md       # 配置说明
│   └── 📄 example_skill.py       # 示例代码
│
└── 📁 bak/                         # 备份目录（临时文件）
    ├── 📁 agentskills/            # 旧版 agentskills
    ├── 📄 article.txt             # 临时文章
    ├── 📄 python3                 # 临时文件
    ├── 📁 skill_service.egg-info  # 构建缓存
    └── 📄 *.md                    # 其他临时文档
```

## ✨ 核心功能模块

### 1. Skill Loader (加载器)
- 扫描 skills 目录
- 解析 SKILL.md 文件
- 提取 skill 元数据
- 验证 skill 格式

### 2. Skill Runner (执行器)
- 解析 skill 执行逻辑
- 执行脚本或调用 LLM
- 处理执行结果
- 错误处理和重试

### 3. CLI Interface (命令行接口)
```bash
skill-service list              # 列出所有 skills
skill-service info <name>        # 查看 skill 详情
skill-service run <name>         # 运行 skill
skill-service serve              # 启动 API 服务
skill-service reload             # 重新加载 skills
skill-service version            # 查看版本信息
```

### 4. HTTP API Server
- `GET /health` - 健康检查
- `GET /api/v1/skills` - 列出所有 skills
- `GET /api/v1/skills/{name}` - 获取 skill 详情
- `POST /api/v1/skills/{name}/run` - 运行 skill
- `POST /api/v1/skills/reload` - 重新加载 skills
- `GET /docs` - API 文档（Swagger UI）

### 5. LLM Integration
- 支持多个 LLM 提供商
- 自然语言生成器
- 多模型配置管理
- 自动模型选择

## 📦 打包准备

### 核心文件清单

**必须包含的文件：**
- ✅ `setup.py` - 安装配置
- ✅ `requirements.txt` - 依赖清单
- ✅ `README.md` - 项目说明
- ✅ `skill_service/` - 核心代码包
- ✅ `skills/` - 示例 skills
- ✅ `tests/` - 测试代码
- ✅ `.gitignore` - Git 忽略规则
- ✅ `.env.example` - 环境变量示例

**可选包含的文件：**
- 📝 `DESIGN.md` - 架构设计文档
- 📝 `examples/` - 使用示例和文档

**不需要包含的文件：**
- ❌ `bak/` - 备份目录
- ❌ `.env` - 环境变量配置（应使用 .env.example）
- ❌ `__pycache__/` - Python 字节码缓存
- ❌ `*.pyc` - Python 编译文件
- ❌ `.DS_Store` - macOS 系统文件
- ❌ `skill_service.egg-info/` - 构建缓存

### 打包命令

```bash
# 源码打包
python setup.py sdist

# 二进制打包
python setup.py bdist_wheel

# 同时生成源码包和二进制包
python setup.py sdist bdist_wheel
```

### 安装测试

```bash
# 从源码安装
pip install -e .

# 从打包文件安装
pip install dist/skill-service-0.1.0.tar.gz

# 运行测试
pytest tests/ -v
```

## 🚀 快速开始

### 安装

```bash
# 克隆项目
git clone <repository-url>
cd localskill

# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 开发模式安装
pip install -e .
```

### 使用

```bash
# 列出所有 skills
skill-service list

# 运行 skill
skill-service run greeting --param name="World"

# 启动 API 服务
skill-service serve

# 访问 API 文档
open http://localhost:8000/docs
```

## 📝 注意事项

1. **环境变量**: 使用前需要配置 `.env` 文件，参考 `.env.example`
2. **LLM 配置**: 如果需要使用 LLM 功能，需要在 `.env` 中配置相应的 API 密钥
3. **Skills 目录**: 默认 skills 目录在项目根目录下的 `skills/` 文件夹
4. **热加载**: 使用 `skill-service reload` 命令可以重新加载 skills，无需重启服务

## 📊 项目统计

- **核心代码文件**: 27 个 Python 文件
- **测试文件**: 4 个测试文件
- **示例 Skills**: 8 个示例
- **文档文件**: 9 个 Markdown 文档
- **依赖库**: 11 个

---

**整理完成时间**: 2026-03-19
**项目版本**: 0.1.0
