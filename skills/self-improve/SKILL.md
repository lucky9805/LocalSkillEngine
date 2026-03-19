---
name: self-improve
description: Skill 自我改进工具。自动创建新 skill、优化现有 skill、分析 skill 质量、生成改进建议。当用户说"创建一个xxx skill"、"优化skill"、"修复skill问题"、"改进skill"时使用此 skill。
license: MIT
compatibility: Requires Python 3.9+, skill_service framework
metadata:
  version: "1.0.0"
  author: Skill Service Team
  category: development
  keywords:
    - skill
    - create
    - optimize
    - improve
    - generate
    - auto-create
    - self-improve
    - 创建
    - 优化
    - 改进
---

# Self Improve Skill

Skill 自我改进工具，支持自动创建和优化 skill。

## 功能特性

- **自动创建 Skill**: 根据自然语言描述自动生成完整的 skill 结构
- **智能优化**: 分析现有 skill 并提供改进建议
- **代码生成**: 生成符合规范的 main.py 和 SKILL.md
- **质量检查**: 验证 skill 结构和代码质量
- **批量处理**: 支持批量优化多个 skill

## 使用方法

### 1. 自动创建新 Skill

```bash
# 通过 chat 命令
python -m skill_service chat "创建一个天气查询 skill，可以查询实时天气和未来7天预报"

# 通过 run 命令
python -m skill_service run self-improve \
  --param action=create \
  --param description="创建一个天气查询 skill" \
  --param skill_name=weather-query
```

### 2. 优化现有 Skill

```bash
# 分析并优化指定 skill
python -m skill_service run self-improve \
  --param action=optimize \
  --param target_skill=github-daily-rank

# 批量优化所有 skill
python -m skill_service run self-improve \
  --param action=optimize-all
```

### 3. 质量检查

```bash
python -m skill_service run self-improve \
  --param action=lint \
  --param target_skill=blog-writer
```

## 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| action | string | 是 | 操作类型：create/optimize/optimize-all/lint/analyze |
| description | string | 条件 | skill 描述（create 时必填） |
| skill_name | string | 否 | skill 名称（create 时可选，自动推断） |
| target_skill | string | 条件 | 目标 skill 名称（optimize/lint 时必填） |
| auto_apply | boolean | 否 | 是否自动应用优化建议（默认 false） |
| style | string | 否 | 代码风格：simple/standard/advanced（默认 standard） |

## 示例

### 创建 Skill 示例

```json
{
  "action": "create",
  "description": "创建一个股票行情查询 skill，支持查询A股实时价格、涨跌幅、成交量",
  "skill_name": "stock-query",
  "style": "standard"
}
```

### 优化 Skill 示例

```json
{
  "action": "optimize",
  "target_skill": "blog-writer-nl",
  "auto_apply": false
}
```

## 输出说明

### 创建操作输出

```json
{
  "success": true,
  "action": "create",
  "skill_name": "weather-query",
  "path": "skills/weather-query",
  "files_created": ["SKILL.md", "scripts/main.py"],
  "suggestions": ["建议添加错误处理", "建议添加单元测试"]
}
```

### 优化操作输出

```json
{
  "success": true,
  "action": "optimize",
  "target_skill": "blog-writer-nl",
  "issues_found": 3,
  "suggestions": [
    {
      "type": "improvement",
      "file": "scripts/main.py",
      "line": 45,
      "message": "建议添加类型注解",
      "severity": "low"
    }
  ],
  "optimized": false
}
```

## 工作原理

1. **意图分析**: 解析用户描述，提取关键信息（功能、参数、场景等）
2. **模板选择**: 根据功能类型选择合适的代码模板
3. **代码生成**: 生成符合 Agent Skills 规范的代码
4. **质量检查**: 验证生成的代码是否符合最佳实践
5. **优化建议**: 分析现有代码，提供改进建议

## 注意事项

- 自动创建的 skill 需要根据实际需求进行调整
- 建议 review 生成的代码后再使用
- 优化操作默认不会自动修改文件，需要确认后应用
- 复杂的业务逻辑仍需人工编写

## 依赖

- Python 3.9+
- skill_service 框架
- 无需外部 API
