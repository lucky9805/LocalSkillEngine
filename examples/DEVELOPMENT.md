# 开发指南

本指南面向想要贡献代码或扩展 Skill Service 功能的开发者。

## 🛠️ 开发环境设置

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/skill-service.git
cd skill-service
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装开发依赖

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 如果有的话
```

### 4. 配置开发环境

```bash
# 复制配置文件
cp .env.example .env

# 修改开发配置
# DEBUG=True
# LOG_LEVEL=DEBUG
```

## 📁 项目结构

```
skill-service/
├── skill_service/          # 核心代码包
│   ├── api/               # API 模块
│   │   ├── __init__.py
│   │   ├── server.py      # FastAPI 服务器
│   │   ├── routes.py      # API 路由
│   │   └── schemas.py     # Pydantic schemas
│   ├── storage/           # 存储模块
│   │   ├── __init__.py
│   │   └── skill_store.py # Skill 存储
│   ├── utils/             # 工具模块
│   │   ├── __init__.py
│   │   ├── logger.py      # 日志工具
│   │   └── validator.py   # 验证工具
│   ├── __init__.py
│   ├── config.py          # 配置管理
│   ├── models.py          # 数据模型
│   ├── loader.py          # Skill 加载器
│   ├── runner.py          # Skill 执行器
│   ├── cli.py             # CLI 接口
│   └── main.py           # 主入口
├── skills/                # Skills 目录
│   ├── example/
│   ├── calculator/
│   └── json-formatter/
├── tests/                 # 测试代码
│   ├── test_loader.py
│   ├── test_runner.py
│   ├── test_cli.py
│   └── test_api.py
├── examples/              # 示例和文档
│   ├── cli_usage.md
│   ├── api_usage.md
│   ├── QUICKSTART.md
│   └── DEPLOYMENT.md
├── requirements.txt       # 运行时依赖
├── setup.py              # 安装配置
├── DESIGN.md             # 架构设计
└── README.md             # 项目说明
```

## 🧪 运行测试

### 运行所有测试

```bash
pytest tests/ -v
```

### 运行特定测试

```bash
# 测试 loader
pytest tests/test_loader.py -v

# 测试 runner
pytest tests/test_runner.py -v

# 测试 CLI
pytest tests/test_cli.py -v

# 测试 API
pytest tests/test_api.py -v
```

### 运行测试并查看覆盖率

```bash
pytest tests/ --cov=skill_service --cov-report=html
```

### 运行特定测试函数

```bash
pytest tests/test_runner.py::test_execute_skill -v -s
```

## 🐛 调试

### 调试 API

```bash
# 启动开发服务器（带自动重载）
skill-service serve --reload

# 或使用 uvicorn 直接启动
uvicorn skill_service.api.server:app --reload --log-level debug
```

### 调试 CLI

```bash
# 查看详细日志
skill-service --verbose run greeting --param name="Debug"

# 或使用 Python 调试器
python -m pdb -c continue skill_service.main.py run greeting --param name="Debug"
```

### 使用断点

在代码中添加断点：

```python
def execute(parameters):
    import pdb; pdb.set_trace()  # 设置断点
    # 你的代码
```

## 🔧 代码风格

### 使用 Black 格式化

```bash
# 格式化所有代码
black skill_service/

# 检查格式（不修改）
black skill_service/ --check
```

### 使用 isort 排序导入

```bash
# 排序导入
isort skill_service/

# 检查导入（不修改）
isort skill_service/ --check-only
```

### 使用 mypy 类型检查

```bash
# 类型检查
mypy skill_service/

# 生成报告
mypy skill_service/ --html-report ./mypy-report
```

### 使用 pylint

```bash
# 代码检查
pylint skill_service/
```

## 📝 添加新功能

### 示例 1: 添加新的 API 端点

1. 在 `skill_service/api/routes.py` 中添加路由：

```python
@router.get("/skills/{skill_name}/history")
async def get_skill_history(skill_name: str):
    """获取 skill 执行历史"""
    # 实现逻辑
    pass
```

2. 在 `tests/test_api.py` 中添加测试：

```python
def test_get_skill_history():
    """测试获取 skill 执行历史"""
    response = client.get("/api/v1/skills/greeting/history")
    assert response.status_code == 200
```

### 示例 2: 添加新的 CLI 命令

1. 在 `skill_service/cli.py` 中添加命令：

```python
@cli.command()
@click.argument('name')
def export(name):
    """导出 skill 配置"""
    # 实现逻辑
    pass
```

2. 测试命令：

```bash
skill-service export greeting
```

### 示例 3: 扩展 Skill 功能

在 `skill_service/models.py` 中添加新字段：

```python
@dataclass
class Skill:
    # 现有字段
    name: str
    version: str
    # ...

    # 新字段
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
```

## 🔄 贡献流程

### 1. Fork 项目

在 GitHub 上 fork 项目到你的账户。

### 2. 创建分支

```bash
git checkout -b feature/your-feature-name
```

### 3. 进行更改

编写代码、添加测试、更新文档。

### 4. 运行测试

```bash
pytest tests/ -v
```

确保所有测试通过。

### 5. 格式化代码

```bash
black skill_service/
isort skill_service/
mypy skill_service/
```

### 6. 提交更改

```bash
git add .
git commit -m "feat: 添加新功能描述"
```

使用约定式提交：
- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `style:` 代码格式
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 构建/工具相关

### 7. 推送分支

```bash
git push origin feature/your-feature-name
```

### 8. 创建 Pull Request

在 GitHub 上创建 Pull Request，描述你的更改。

## 📚 文档

### 添加新功能的文档

1. 在 `README.md` 中添加使用说明
2. 在 `examples/` 中添加示例代码
3. 更新 `DESIGN.md`（如果是架构变更）
4. 添加 JSDoc/Docstring 注释

### 文档示例

```python
def execute(parameters):
    """
    执行 skill

    Args:
        parameters (Dict[str, Any]): 包含参数的字典
            - name (str): 名称参数
            - count (int): 数量参数，默认为 1

    Returns:
        Dict[str, Any]: 执行结果
            - success (bool): 是否成功
            - result (str): 结果字符串

    Raises:
        ValueError: 参数无效时抛出

    Examples:
        >>> execute({"name": "Alice"})
        {"success": True, "result": "Hello, Alice!"}
    """
    pass
```

## 🔍 性能优化

### 1. 使用异步

```python
import asyncio

async def execute(parameters):
    """异步执行"""
    # 使用异步 IO 操作
    result = await async_operation()
    return result
```

### 2. 缓存结果

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_operation(param):
    """缓存昂贵操作"""
    # 耗时操作
    return result
```

### 3. 批量处理

```python
def batch_process(items, batch_size=100):
    """批量处理"""
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        process_batch(batch)
```

## 🧪 编写测试

### 单元测试示例

```python
import pytest
from skill_service.runner import SkillRunner

@pytest.mark.asyncio
async def test_skill_execution():
    """测试 skill 执行"""
    runner = SkillRunner()
    request = SkillExecutionRequest(
        skill_name="greeting",
        parameters={"name": "Test"}
    )

    result = await runner.execute(request)

    assert result.success is True
    assert "Hello, Test!" in result.result
```

### 集成测试示例

```python
from fastapi.testclient import TestClient
from skill_service.api.server import app

client = TestClient(app)

def test_api_integration():
    """API 集成测试"""
    response = client.post(
        "/api/v1/skills/greeting/run",
        json={"parameters": {"name": "Test"}}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
```

### 测试夹具

```python
@pytest.fixture
def runner():
    """创建 runner 实例"""
    return SkillRunner()

@pytest.fixture
def sample_skill():
    """创建测试 skill"""
    return Skill(
        name="test",
        version="1.0.0",
        author="Test",
        category="test",
        description="Test skill",
        instructions="Test"
    )
```

## 📦 发布新版本

### 1. 更新版本号

编辑 `skill_service/__init__.py`:

```python
__version__ = "0.2.0"
```

### 2. 创建 CHANGELOG

在 `CHANGELOG.md` 中记录变更：

```markdown
## [0.2.0] - 2024-01-01

### Added
- 新功能 1
- 新功能 2

### Fixed
- 修复 bug 1
```

### 3. 构建和发布

```bash
# 构建
python setup.py sdist bdist_wheel

# 上传到 PyPI
twine upload dist/*
```

## 🤝 社区

- GitHub Issues: 报告 bug 和请求功能
- GitHub Discussions: 讨论和提问
- Pull Requests: 贡献代码

## 📖 相关资源

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Click 文档](https://click.palletsprojects.com/)
- [Pydantic 文档](https://docs.pydantic.dev/)
- [pytest 文档](https://docs.pytest.org/)

祝开发愉快！🚀
