# 本地 Skill 运行服务 - 整体架构设计

## 1. 项目概述

创建一个可以在本地通过命令行或 HTTP API 运行 skill 的服务。该服务将支持：
- 📝 加载和解析 SKILL.md 文件
- 🖥️ 通过命令行直接运行 skill
- 🌐 通过 HTTP API 接口调用 skill
- 🔧 支持动态加载和热更新 skill
- 📊 提供执行结果返回和日志记录

## 2. 技术架构

### 2.1 技术栈选择

**后端框架**: Python + FastAPI
- FastAPI: 现代、快速的 Web 框架
- 自动生成 API 文档
- 异步支持
- 类型提示友好

**核心组件**:
- **Skill Loader**: 负责加载和解析 SKILL.md 文件
- **Skill Runner**: 执行 skill 逻辑
- **CLI Interface**: 命令行接口
- **API Server**: FastAPI HTTP 服务
- **Config Manager**: 配置管理

**依赖库**:
```
fastapi>=0.104.0
uvicorn>=0.24.0
click>=8.1.0
pyyaml>=6.0
aiofiles>=23.2.0
python-dotenv>=1.0.0
```

## 3. 系统架构设计

```
┌───────────────────────────────────────────────────────────┐
│                    本地 Skill 运行服务                      │
├─────────────────────────────────────────────────────────  ┤
│                                                           │
│  ┌──────────────┐      ┌──────────────┐                   │
│  │ CLI Interface │      │  HTTP API    │                  │
│  │  (命令行)     │      │   Server     │                   │
│  └──────┬───────┘      └──────┬───────┘                   │
│         │                     │                           │
│         └──────────┬──────────┘                           │
│                    │                                      │
│         ┌──────────▼──────────┐                           │
│         │  Request Router     │                           │
│         │   (请求路由」         │                           │
│         └──────────┬──────────┘                           │
│                    │                                      │
│    ┌───────────────┼───────────────┐                      │
│    ▼               ▼               ▼                      │
│  ┌─────┐       ┌─────────┐   ┌──────────┐                 │
│  │Skill│       │ Skill   │   │  Skill   │                 │
│  │Pool │       │ Loader  │   │  Runner  │                 │
│  │ 池   │       │ (加载器) │   │ (执行器)  │                 │
│  └──┬──┘       └────┬────┘   └────┬─────┘                 │
│     │               │            │                        │
│     └───────────────┴────────────┘                        │
│                    │                                      │
│         ┌──────────▼──────────┐                           │
│         │  Skill Storage      │                           │
│         │  (本地技能库)        │                            │
│         │  /skills/           │                           │
│         └─────────────────────┘                           │
│                                                           │
│  ┌──────────────┐      ┌──────────────┐                   │
│  │ Log Manager  │      │ Config       │                   │
│  │  (日志管理)    │      │ Manager      │                   │
│  └──────────────┘      └──────────────┘                   │
│                                                           │
└───────────────────────────────────────────────────────────┘


```

## 4. 核心模块设计

### 4.1 Skill Loader (技能加载器)

**职责**:
- 扫描技能目录
- 解析 SKILL.md 文件
- 提取 skill 元数据
- 验证 skill 格式

**数据结构**:
```python
@dataclass
class Skill:
    name: str                      # Skill 名称
    version: str                   # 版本号
    description: str               # 描述
    author: str                    # 作者
    instructions: str             # 执行指令
    tools: List[str]               # 所需工具列表
    scripts: Dict[str, str]        # 脚本文件路径
    category: str                  # 分类
    enabled: bool = True           # 是否启用
```

### 4.2 Skill Runner (技能执行器)

**职责**:
- 解析 skill 执行逻辑
- 执行脚本或调用 API
- 处理执行结果
- 错误处理和重试

**执行流程**:
1. 加载 skill 配置
2. 检查依赖和环境
3. 执行前置脚本
4. 执行主逻辑
5. 执行后置脚本
6. 返回执行结果

### 4.3 CLI Interface (命令行接口)

**命令设计**:
```bash
# 列出所有 skills
skill-service list

# 显示 skill 详情
skill-service info <skill-name>

# 运行 skill
skill-service run <skill-name> [args...]

# 启动 API 服务
skill-service serve --port 8000

# 安装新 skill
skill-service install <skill-path>
```

### 4.4 HTTP API Server

**API 端点设计**:
```
GET    /api/v1/skills              # 列出所有 skills
GET    /api/v1/skills/{name}       # 获取 skill 详情
POST   /api/v1/skills/{name}/run   # 运行 skill
POST   /api/v1/skills/install      # 安装新 skill
DELETE /api/v1/skills/{name}       # 卸载 skill
GET    /api/v1/health              # 健康检查
GET    /docs                       # API 文档
```

**请求/响应示例**:
```json
// 运行 skill 请求
POST /api/v1/skills/greeting/run
{
  "parameters": {
    "name": "Alice"
  }
}

// 响应
{
  "success": true,
  "result": "Hello, Alice!",
  "execution_time": 0.123,
  "logs": [...]
}
```

## 5. 项目目录结构

```
localskill/
├── README.md                      # 项目说明
├── requirements.txt               # Python 依赖
├── setup.py                       # 安装配置
├── .env.example                   # 环境变量示例
├── skill_service/                 # 核心代码包
│   ├── __init__.py
│   ├── main.py                    # CLI 入口
│   ├── config.py                  # 配置管理
│   ├── models.py                  # 数据模型
│   ├── loader.py                  # Skill 加载器
│   ├── runner.py                  # Skill 执行器
│   ├── cli.py                     # 命令行接口
│   ├── api/                       # API 模块
│   │   ├── __init__.py
│   │   ├── server.py              # FastAPI 应用
│   │   ├── routes.py              # 路由定义
│   │   └── schemas.py             # API 数据结构
│   ├── utils/                     # 工具模块
│   │   ├── __init__.py
│   │   ├── logger.py              # 日志工具
│   │   └── validator.py           # 验证工具
│   └── storage/                   # 存储模块
│       ├── __init__.py
│       └── skill_store.py         # Skill 存储
├── skills/                        # Skills 目录
│   ├── example/                   # 示例 skill
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── hello.py
│   └── README.md
├── tests/                         # 测试代码
│   ├── __init__.py
│   ├── test_loader.py
│   ├── test_runner.py
│   └── test_api.py
└── examples/                      # 使用示例
    ├── cli_usage.md
    └── api_usage.md
```

## 6. SKILL.md 格式规范

```markdown
---
name: skill-name
version: 1.0.0
author: Your Name
category: utility
description: 简短描述
---

## 简介

详细描述 skill 的功能和用途。

## 执行逻辑

描述执行步骤...

## 脚本

### main.py
\`\`\`python
def execute(parameters):
    # 执行逻辑
    return result
\`\`\`

## 工具依赖

列出需要的工具...
```

## 7. 实现计划

### Phase 1: 基础架构 ✅
- [x] 项目结构设计
- [ ] 创建基础目录和配置文件
- [ ] 实现配置管理模块
- [ ] 实现数据模型

### Phase 2: 核心功能
- [ ] 实现 Skill Loader
- [ ] 实现 Skill Runner
- [ ] 实现本地存储

### Phase 3: 接口层
- [ ] 实现 CLI 接口
- [ ] 实现 HTTP API 服务

### Phase 4: 示例和文档
- [ ] 创建示例 skill
- [ ] 编写使用文档
- [ ] 编写测试用例

### Phase 5: 优化和增强
- [ ] 性能优化
- [ ] 错误处理增强
- [ ] 日志系统完善

## 8. 使用场景

1. **命令行使用**
   ```bash
   # 快速运行一个 skill
   skill-service run greeting --name "World"

   # 列出可用 skills
   skill-service list
   ```

2. **API 使用**
   ```python
   import requests

   response = requests.post('http://localhost:8000/api/v1/skills/greeting/run', json={
       'parameters': {'name': 'World'}
   })

   print(response.json())
   ```

3. **集成到其他项目**
   - 通过 HTTP API 集成到现有系统
   - 作为微服务部署
   - 在 CI/CD 流程中使用

## 9. 扩展性设计

- **插件系统**: 支持自定义 skill 类型
- **分布式执行**: 未来可支持远程 skill 执行
- **技能市场**: 支持从远程仓库安装 skill
- **版本管理**: skill 版本管理和回滚
- **权限控制**: API 访问控制

## 10. 技术亮点

1. **灵活的加载机制**: 支持热加载和动态更新
2. **统一的接口**: CLI 和 API 共享核心逻辑
3. **类型安全**: 完整的类型提示
4. **异步支持**: FastAPI 异步处理
5. **易于扩展**: 模块化设计
6. **完整的文档**: 自动生成 API 文档

---

这个设计提供了一个完整、可扩展的本地 skill 运行服务方案。你觉得这个架构如何？有什么需要调整的地方吗？
