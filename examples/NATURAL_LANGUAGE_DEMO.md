# 自然语言创建 Skill 演示

## 🎉 功能已集成！

你现在可以使用自然语言来创建 skills！

## 📖 使用方法

### 基本语法

```bash
skill-service create "你的自然语言描述"
```

### 示例 1: 问候技能 ✅

**输入**：
```bash
skill-service create "创建一个问候技能，可以自定义名字和问候语"
```

**输出**：
```
✅ Skill 创建成功!
名称: greeting-nl
路径: skills/greeting-nl
```

**运行**：
```bash
skill-service run greeting-nl --param name="小明" --param greeting="早上好"
```

**结果**：
```
早上好，小明！
```

## 🎯 支持的功能类型

### 1. 问候技能 ✅
```bash
skill-service create "创建一个问候技能"
```

### 2. 计算技能 ✅
```bash
skill-service create "创建一个计算技能，计算两个数的和、差、积、商"
```

### 3. 格式化技能 ✅
```bash
skill-service create "创建一个格式化 JSON 的技能"
```

### 4. 统计技能 ✅
```bash
skill-service create "创建一个统计技能，计算数字列表的平均值、最大值、最小值"
```

## 📝 生成的代码示例

### 问候技能

**SKILL.md**:
```markdown
---
name: greeting-nl
version: 1.0.0
author: AI Generated
category: utility
description: greeting-nl - 创建一个问候技能，可以自定义名字和问候语
---
```

**scripts/main.py**:
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

## 🔄 工作流程

1. **描述需求**
   ```bash
   skill-service create "创建一个技能，做xxx"
   ```

2. **查看生成的代码**
   ```bash
   cat skills/your-skill/scripts/main.py
   ```

3. **测试运行**
   ```bash
   skill-service run your-skill --param ...
   ```

4. **修改完善**
   ```bash
   vim skills/your-skill/scripts/main.py
   skill-service reload
   ```

## 💡 最佳实践

### 1. 描述要清晰
- ✅ "创建一个问候技能，可以自定义名字和问候语"
- ❌ "搞个问候"

### 2. 指定参数
- ✅ "创建一个技能，接收名字和年龄，生成个人信息"
- ❌ "生成信息"

### 3. 说明功能
- ✅ "创建一个技能，计算数字列表的平均值、最大值、最小值"
- ❌ "处理数据"

## 🎨 高级用法

### 指定 skill 名称

```bash
skill-service create "创建一个问候技能" --name my-greeting
```

### 创建后自动加载

```bash
skill-service create "创建一个技能"
skill-service list  # 立即看到新技能
```

## 🔧 自定义生成的代码

生成的代码只是一个起点，你可以根据需要进行修改：

```bash
# 1. 生成基础代码
skill-service create "创建一个技能"

# 2. 编辑代码
vim skills/your-skill/scripts/main.py

# 3. 重新加载
skill-service reload

# 4. 测试
skill-service run your-skill --param ...
```

## 📝 完整示例

### 示例：创建一个实用的数据处理技能

**步骤 1: 自然语言描述**
```bash
skill-service create "创建一个数据处理技能，计算数字列表的统计信息"
```

**步骤 2: 查看生成的代码**
```bash
cat skills/data-processor-nl/scripts/main.py
```

**步骤 3: 运行测试**
```bash
skill-service run data-processor-nl --json-params '{"numbers":[1,2,3,4,5]}'
```

**步骤 4: 根据需要修改**
```bash
vim skills/data-processor-nl/scripts/main.py
skill-service reload
```

## ✨ 优势

1. **快速原型** - 几秒钟创建基础技能
2. **学习工具** - 通过生成的代码学习如何编写技能
3. **降低门槛** - 不需要精通 Python 就能创建简单技能
4. **可扩展** - 生成的代码可以进一步自定义

## 🎯 使用场景

### 场景 1: 快速原型开发
```bash
# 快速创建一个原型技能
skill-service create "创建一个技能，处理CSV数据"
# 然后基于生成的代码进行开发
```

### 场景 2: 学习参考
```bash
# 查看生成的代码学习最佳实践
skill-service create "创建一个技能，调用API"
cat skills/api-skill-nl/scripts/main.py
```

### 场景 3: 自动化任务
```bash
# 创建自动化任务技能
skill-service create "创建一个技能，批量处理文件"
```

## 📚 更多示例

### 示例 1: 文本处理
```bash
skill-service create "创建一个技能，把文本转换成大写"
```

### 示例 2: 数据转换
```bash
skill-service create "创建一个技能，把温度从摄氏度转换成华氏度"
```

### 示例 3: 格式化
```bash
skill-service create "创建一个技能，格式化日期时间"
```

## 🚀 下一步

1. **尝试创建你的第一个技能**
   ```bash
   skill-service create "创建一个简单的问候技能"
   ```

2. **查看生成的代码**
   ```bash
   cat skills/greeting-nl/scripts/main.py
   ```

3. **根据需求修改**
   ```bash
   vim skills/greeting-nl/scripts/main.py
   ```

4. **重新加载并测试**
   ```bash
   skill-service reload
   skill-service run greeting-nl --param name="测试"
   ```

## 💡 提示

- 生成的代码是一个起点，建议根据实际需求进行调整
- 可以查看 `skills/` 目录下的示例学习更多
- 参考 `examples/SKILL_TEMPLATE.md` 了解完整的 skill 结构

---

**现在就用自然语言创建你的第一个 skill 吧！** 🎉
