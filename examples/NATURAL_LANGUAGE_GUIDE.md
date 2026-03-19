# 使用自然语言创建 Skill

## 🌟 概述

Skill Service 支持使用自然语言描述来创建技能！你只需要用中文描述你想做什么，系统会自动生成可执行的 skill。

## 📝 创建方式

### 方式 1: 通过 CLI 创建

```bash
# 使用自然语言描述创建 skill
skill-service create "帮我写一个问候别人的技能，可以自定义问候语和名字"

# 创建数据处理技能
skill-service create "创建一个技能，能从CSV文件读取数据并计算平均值"

# 创建API调用技能
skill-service create "写一个技能，调用天气API获取北京今天的天气"
```

### 方式 2: 通过 API 创建

```python
import requests

response = requests.post(
    'http://localhost:8000/api/v1/skills/create-from-text',
    json={
        "description": "帮我写一个问候别人的技能，可以自定义问候语和名字",
        "skill_name": "my-greeting"
    }
)

result = response.json()
print(result)
```

## 🎯 支持的功能类型

### 1. 文本处理
- 字符串拼接
- 格式化文本
- 文本替换
- 模板生成

**示例**：
```
创建一个技能，把名字和日期格式化成"你好，[名字]，今天是[日期]"
```

### 2. 数学计算
- 基本运算
- 统计计算
- 数据转换

**示例**：
```
创建一个技能，计算一组数字的平均值、最大值和最小值
```

### 3. 数据转换
- JSON 格式化
- 数据转换
- 单位换算

**示例**：
```
创建一个技能，把温度从摄氏度转换成华氏度
```

### 4. 文件操作
- 读取文件
- 写入文件
- 文件处理

**示例**：
```
创建一个技能，读取文本文件并统计行数和字数
```

### 5. API 调用
- HTTP 请求
- 数据获取
- 服务集成

**示例**：
```
创建一个技能，调用某个API获取股票价格
```

## 📋 自然语言示例

### 示例 1: 问候技能

**输入**：
```
创建一个问候技能，向用户打招呼，可以自定义名字和问候语
```

**自动生成的代码**：
```python
def execute(parameters):
    """
    问候技能 - 向用户打招呼

    参数：
    - name: 名字（可选，默认为"朋友"）
    - greeting: 问候语（可选，默认为"你好"）
    """
    name = parameters.get("name", "朋友")
    greeting = parameters.get("greeting", "你好")

    return f"{greeting}，{name}！"
```

### 示例 2: 计算技能

**输入**：
```
创建一个技能，计算两个数的和、差、积、商
```

**自动生成的代码**：
```python
def execute(parameters):
    """
    计算技能 - 执行基本数学运算

    参数：
    - a: 第一个数字
    - b: 第二个数字
    """
    a = parameters.get("a", 0)
    b = parameters.get("b", 0)

    operations = {
        "和": a + b,
        "差": a - b,
        "积": a * b,
        "商": a / b if b != 0 else "无法除以零"
    }

    return operations
```

### 示例 3: 数据处理技能

**输入**：
```
创建一个技能，接收一个数字列表，计算平均值、最大值、最小值
```

**自动生成的代码**：
```python
def execute(parameters):
    """
    数据处理技能 - 计算统计信息

    参数：
    - numbers: 数字列表
    """
    numbers = parameters.get("numbers", [])

    if not numbers:
        return {"error": "请提供数字列表"}

    result = {
        "平均值": sum(numbers) / len(numbers),
        "最大值": max(numbers),
        "最小值": min(numbers),
        "总数": len(numbers)
    }

    return result
```

### 示例 4: JSON 格式化技能

**输入**：
```
创建一个技能，格式化JSON数据，可以压缩或美化输出
```

**自动生成的代码**：
```python
import json

def execute(parameters):
    """
    JSON 格式化技能

    参数：
    - data: JSON 数据或字符串
    - mode: 格式化模式（pretty/compact）
    """
    import json

    data = parameters.get("data", {})
    mode = parameters.get("mode", "pretty")

    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            return {"error": "无效的 JSON 字符串"}

    if mode == "compact":
        return json.dumps(data, separators=(',', ':'))
    else:
        return json.dumps(data, indent=2, ensure_ascii=False)
```

## 🎨 高级功能

### 添加错误处理

在描述中添加错误处理要求：
```
创建一个技能，读取文件，如果文件不存在就返回友好的错误信息
```

### 添加参数验证

指定参数的验证规则：
```
创建一个技能，计算折扣价格，价格必须是正数，折扣在0到1之间
```

### 添加日志

要求添加执行日志：
```
创建一个技能，处理数据时记录详细的执行步骤
```

## 💡 最佳实践

### 1. 描述要清晰
- ✅ "创建一个技能，计算两个数的和"
- ❌ "算两个数"

### 2. 指定参数
- ✅ "创建一个技能，接收名字和年龄，生成个人信息"
- ❌ "生成信息"

### 3. 说明输出格式
- ✅ "创建一个技能，返回JSON格式的结果"
- ❌ "返回结果"

### 4. 提及特殊需求
- ✅ "创建一个技能，处理中文文本，确保编码正确"
- ❌ "处理文本"

## 🔧 技术实现

系统会根据你的自然语言描述：

1. **分析意图**
   - 识别功能类型（计算、处理、调用等）
   - 提取关键信息（参数、操作、逻辑）

2. **生成代码**
   - 根据意图选择合适的模板
   - 自动生成 Python 代码
   - 添加参数处理和错误处理

3. **创建文件**
   - 生成 SKILL.md 文件
   - 创建执行脚本
   - 保存到 skills 目录

4. **自动加载**
   - 重新加载 skills
   - 验证功能
   - 提供测试建议

## 🚀 快速开始

### 1. 创建第一个自然语言 skill

```bash
skill-service create "创建一个简单的问候技能"
```

### 2. 查看生成的 skill

```bash
skill-service info greeting-nl
```

### 3. 测试运行

```bash
skill-service run greeting-nl --param name="小明"
```

### 4. 根据需要修改

```bash
# 编辑生成的文件
vim skills/greeting-nl/scripts/main.py

# 重新加载
skill-service reload
```

## 📝 完整示例

### 任务：创建一个实用的数据处理技能

**自然语言描述**：
```
创建一个数据处理技能，能够：
1. 接收一个数字列表
2. 计算总和、平均值、最大值、最小值
3. 过滤掉负数
4. 返回格式化的JSON结果
```

**生成的 skill**：

**SKILL.md**:
```markdown
---
name: data-processor
version: 1.0.0
author: AI Generated
category: utility
description: 数据处理技能 - 计算统计信息并过滤数据
---

## 简介
这个技能能够处理数字列表，计算统计信息并过滤掉负数。

## 参数
- numbers: 数字列表
- filter_negative: 是否过滤负数（默认为true）

## 功能
- 计算总和、平均值、最大值、最小值
- 过滤负数（可选）
- 返回JSON格式结果
```

**scripts/main.py**:
```python
def execute(parameters):
    """
    数据处理技能
    """
    numbers = parameters.get("numbers", [])
    filter_negative = parameters.get("filter_negative", True)

    # 过滤负数
    if filter_negative:
        numbers = [n for n in numbers if n >= 0]

    if not numbers:
        return {"error": "没有有效数据"}

    # 计算统计信息
    result = {
        "总数": len(numbers),
        "总和": sum(numbers),
        "平均值": sum(numbers) / len(numbers),
        "最大值": max(numbers),
        "最小值": min(numbers),
        "数据": numbers
    }

    return result
```

## ❓ 常见问题

### Q: 可以描述复杂的逻辑吗？
A: 可以！支持条件判断、循环、错误处理等复杂逻辑。

### Q: 生成的代码可靠吗？
A: 生成的代码会经过验证，你可以查看并修改。

### Q: 支持哪些编程语言？
A: 目前主要生成 Python 代码。

### Q: 可以调用外部服务吗？
A: 可以，通过自然语言描述 API 调用需求即可。

## 🎯 下一步

1. **尝试创建简单的 skill**
   ```
   skill-service create "创建一个问候技能"
   ```

2. **逐步增加复杂度**
   ```
   skill-service create "创建一个数据处理技能，计算平均值和总和"
   ```

3. **集成到工作流**
   ```
   skill-service create "创建一个技能，从API获取数据并处理"
   ```

---

**现在就用自然语言创建你的第一个 skill 吧！** 🚀
