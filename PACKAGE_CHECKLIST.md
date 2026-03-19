# Skill Service 打包清单

## ✅ 打包前检查清单

### 1. 环境检查
- [ ] Python 版本 >= 3.8
- [ ] 虚拟环境已激活
- [ ] 依赖已安装: `pip install -r requirements.txt`
- [ ] 测试全部通过: `pytest tests/ -v`

### 2. 配置文件检查
- [ ] `setup.py` 中的版本号已更新
- [ ] `setup.py` 中的作者信息已更新
- [ ] `README.md` 内容完整且准确
- [ ] `.env.example` 包含所有必要的环境变量
- [ ] `.gitignore` 包含所有不需要打包的文件

### 3. 代码检查
- [ ] 所有 `.pyc` 文件已删除
- [ ] 所有 `__pycache__` 目录已删除
- [ ] `.DS_Store` 文件已删除
- [ ] 代码无语法错误: `python -m py_compile skill_service/**/*.py`
- [ ] 无未使用的导入（可选）

### 4. 文档检查
- [ ] README.md 更新完整
- [ ] API 文档可以正常生成
- [ ] 示例代码可以正常运行
- [ ] CHANGELOG.md（如果有）已更新

## 📦 打包步骤

### 方式 1: 源码打包 (sdist)

```bash
# 清理旧的构建文件
rm -rf build/ dist/ *.egg-info/

# 打包源码
python setup.py sdist

# 检查打包结果
ls -lh dist/
```

**输出文件**: `dist/skill-service-0.1.0.tar.gz`

### 方式 2: 二进制打包 (bdist_wheel)

```bash
# 清理旧的构建文件
rm -rf build/ dist/ *.egg-info/

# 打包二进制包
python setup.py bdist_wheel

# 检查打包结果
ls -lh dist/
```

**输出文件**: `dist/skill_service-0.1.0-py3-none-any.whl`

### 方式 3: 同时生成源码包和二进制包（推荐）

```bash
# 清理旧的构建文件
rm -rf build/ dist/ *.egg-info/

# 同时打包
python setup.py sdist bdist_wheel

# 检查打包结果
ls -lh dist/
```

**输出文件**:
- `dist/skill-service-0.1.0.tar.gz` (源码包)
- `dist/skill_service-0.1.0-py3-none-any.whl` (二进制包)

### 方式 4: 使用 build 模块（现代方式）

```bash
# 安装 build 模块
pip install build

# 清理旧的构建文件
rm -rf build/ dist/ *.egg-info/

# 打包
python -m build

# 检查打包结果
ls -lh dist/
```

## 🧪 打包后验证

### 1. 安装测试

```bash
# 创建新的虚拟环境
python -m venv test_env
source test_env/bin/activate

# 安装打包的文件
pip install dist/skill-service-0.1.0.tar.gz

# 或者安装二进制包
pip install dist/skill_service-0.1.0-py3-none-any.whl
```

### 2. 功能测试

```bash
# 测试 CLI 命令
skill-service --version
skill-service list

# 测试 API 服务
skill-service serve &
sleep 2
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/skills

# 测试运行 skill
skill-service run greeting --param name="Test"
```

### 3. 测试导入

```bash
python -c "import skill_service; print('导入成功')"
python -c "from skill_service import cli; print('CLI 导入成功')"
python -c "from skill_service.loader import SkillLoader; print('Loader 导入成功')"
```

### 4. 运行测试套件

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_cli.py -v
pytest tests/test_api.py -v
```

## 🚀 发布到 PyPI

### 1. 注册 PyPI 账号
- 访问 https://pypi.org/account/register/
- 注册账号并验证邮箱

### 2. 安装发布工具

```bash
pip install twine
```

### 3. 检查包的元数据

```bash
twine check dist/*
```

### 4. 上传到 TestPyPI（测试）

```bash
# 上传到 TestPyPI
twine upload --repository-url https://test.pypi.org/legacy/ dist/*

# 从 TestPyPI 安装测试
pip install --index-url https://test.pypi.org/simple/ skill-service
```

### 5. 上传到 PyPI（正式发布）

```bash
# 上传到 PyPI
twine upload dist/*

# 从 PyPI 安装
pip install skill-service
```

## 📋 打包文件内容检查

### 必须包含的文件

```
skill-service/
├── setup.py
├── README.md
├── requirements.txt
├── LICENSE (如果有)
├── skill_service/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── loader.py
│   ├── runner.py
│   ├── models.py
│   ├── main.py
│   ├── api/
│   ├── llm/
│   ├── storage/
│   └── utils/
├── skills/
│   └── (示例 skills)
└── tests/
    └── (测试文件)
```

### 不应该包含的文件

- ❌ `.env` (包含敏感信息)
- ❌ `.DS_Store`
- ❌ `__pycache__/`
- ❌ `*.pyc`
- ❌ `.git/`
- ❌ `bak/`
- ❌ `build/`
- ❌ `dist/`
- ❌ `*.egg-info/`

## 🔧 常见问题

### 1. 打包时包含不需要的文件

**解决方案**: 在 `MANIFEST.in` 中明确指定要包含/排除的文件

```ini
# MANIFEST.in
include README.md
include LICENSE
include requirements.txt
recursive-include skill_service *.py
recursive-include skills *.py *.md
recursive-include tests *.py
global-exclude __pycache__
global-exclude *.pyc
global-exclude .DS_Store
global-exclude .env
global-exclude bak/*
```

### 2. 安装后找不到命令

**解决方案**: 检查 `setup.py` 中的 `entry_points` 配置

```python
entry_points={
    "console_scripts": [
        "skill-service=skill_service.main:cli",
    ],
}
```

### 3. 导入错误

**解决方案**: 检查 `setup.py` 中的 `packages` 配置

```python
from setuptools import setup, find_packages

setup(
    packages=find_packages(),
    # ...
)
```

### 4. 依赖问题

**解决方案**: 确保 `requirements.txt` 和 `setup.py` 中的 `install_requires` 保持一致

## 📝 版本管理

### 语义化版本 (Semantic Versioning)

```
主版本号.次版本号.修订号 (MAJOR.MINOR.PATCH)

示例:
0.1.0  - 初始版本
0.1.1  - Bug 修复
0.2.0  - 新增功能（向后兼容）
1.0.0  - 重大更新（可能不兼容）
```

### 更新版本号

```bash
# 在 setup.py 中更新版本号
version="0.1.0" -> version="0.2.0"
```

### 创建 Git 标签（推荐）

```bash
git tag v0.1.0
git push origin v0.1.0
```

## 🎯 打包脚本

创建一个自动化打包脚本 `build.sh`:

```bash
#!/bin/bash

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}开始打包...${NC}"

# 1. 清理旧文件
echo -e "${GREEN}清理旧文件...${NC}"
rm -rf build/ dist/ *.egg-info/

# 2. 运行测试
echo -e "${GREEN}运行测试...${NC}"
if ! pytest tests/ -v; then
    echo -e "${RED}测试失败，终止打包${NC}"
    exit 1
fi

# 3. 打包
echo -e "${GREEN}打包中...${NC}"
python setup.py sdist bdist_wheel

# 4. 检查结果
echo -e "${GREEN}检查打包结果...${NC}"
twine check dist/*

# 5. 完成
echo -e "${GREEN}打包完成！${NC}"
ls -lh dist/
```

使用方法:

```bash
chmod +x build.sh
./build.sh
```

## 📞 获取帮助

如果遇到打包问题，可以查看:

- Python 打包文档: https://packaging.python.org/
- Setuptools 文档: https://setuptools.readthedocs.io/
- Twine 文档: https://twine.readthedocs.io/

---

**最后更新**: 2026-03-19
