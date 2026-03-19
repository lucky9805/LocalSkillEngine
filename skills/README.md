# Skills 目录

这是存放所有 skills 的目录。每个 skill 应该是一个独立的文件夹，包含 `SKILL.md` 文件。

## 目录结构（OpenClaw 标准）

```
skills/
├── example/
│   ├── SKILL.md              # 必需：元数据 + 使用说明
│   ├── scripts/              # 可选：可执行代码
│   │   └── main.py
│   ├── references/           # 可选：参考文档、schema、细节说明
│   │   ├── api-reference.md
│   │   └── examples.md
│   └── assets/               # 可选：模板、样例、输出资源
│       ├── template.docx
│       └── sample-data.json
└── your-skill/
    ├── SKILL.md
    ├── scripts/
    │   └── main.py
    ├── references/
    └── assets/
```

## 各目录说明

| 目录/文件 | 必需 | 说明 |
|-----------|------|------|
| `SKILL.md` | ✅ | 核心文件，包含 YAML frontmatter 元数据和 skill 使用说明 |
| `scripts/` | ❌ | 存放可执行代码（Python、Shell 等），供 skill 调用 |
| `references/` | ❌ | 存放参考文档、API 文档、schema 定义等，按需加载 |
| `assets/` | ❌ | 存放模板文件、示例数据、静态资源等 |

## SKILL.md 格式

每个 skill 必须包含 `SKILL.md` 文件，格式如下：

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
    # 可以通过 parameters['_skill_context'] 获取 references 和 assets 路径
    return result
\`\`\`

## 参数

- name: 参数说明
- greeting: 参数说明

## 使用示例

```bash
skill-service run skill-name --param name=value
```

## 工具依赖

列出需要的工具...
```

## 在脚本中使用 References 和 Assets

当 skill 被执行时，系统会自动在 `parameters` 中添加 `_skill_context` 字段，包含以下信息：

```python
def execute(parameters):
    # 获取 skill 上下文
    context = parameters.get('_skill_context', {})
    
    # 获取 references 文件路径
    references = context.get('references', {})
    # references = {'api-reference.md': '/path/to/skill/references/api-reference.md', ...}
    
    # 获取 assets 文件路径
    assets = context.get('assets', {})
    # assets = {'template.docx': '/path/to/skill/assets/template.docx', ...}
    
    # 获取 skill 根目录
    skill_path = context.get('skill_path', '')
    
    # 你的逻辑...
    return result
```

## 示例

参考 `example/` 目录下的示例 skill。
