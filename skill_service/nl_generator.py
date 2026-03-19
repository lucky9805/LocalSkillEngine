"""
自然语言 Skill 生成器
"""
import re
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from skill_service.utils.logger import get_logger


class NaturalLanguageSkillGenerator:
    """自然语言 skill 生成器"""

    def __init__(self):
        """初始化生成器"""
        self.logger = get_logger(__name__)
        self.skills_dir = Path("./skills")

    def generate_from_description(
        self,
        description: str,
        skill_name: str = None
    ) -> Dict[str, Any]:
        """
        从自然语言描述生成 skill

        Args:
            description: 自然语言描述
            skill_name: skill 名称（可选）

        Returns:
            生成结果
        """
        # 分析描述
        intent = self._analyze_intent(description)

        # 生成 skill 名称
        if not skill_name:
            skill_name = self._generate_skill_name(description)

        # 生成代码
        code = self._generate_code(description, intent)

        # 创建 skill
        result = self._create_skill(skill_name, description, code, intent)

        return result

    def _analyze_intent(self, description: str) -> Dict[str, Any]:
        """
        分析用户意图

        Args:
            description: 自然语言描述

        Returns:
            意图分析结果
        """
        intent = {
            "type": "utility",
            "operation": "general",
            "parameters": [],
            "operations": []
        }

        desc_lower = description.lower()

        # 识别操作类型
        if "问候" in desc_lower or "打招呼" in desc_lower or "hello" in desc_lower:
            intent["type"] = "utility"
            intent["operation"] = "greeting"
            intent["parameters"] = ["name", "greeting"]

        elif "计算" in desc_lower or "运算" in desc_lower:
            intent["type"] = "utility"
            intent["operation"] = "calculation"
            intent["operations"] = self._extract_operations(description)

            if "和" in description or "加" in description:
                intent["operations"].append("add")
            if "差" in description or "减" in description:
                intent["operations"].append("subtract")
            if "积" in description or "乘" in description:
                intent["operations"].append("multiply")
            if "商" in description or "除" in description:
                intent["operations"].append("divide")

        elif "格式化" in desc_lower or "json" in desc_lower:
            intent["type"] = "utility"
            intent["operation"] = "format"
            intent["parameters"] = ["data", "mode"]

        elif "统计" in desc_lower or "平均" in desc_lower or "最大" in desc_lower or "最小" in desc_lower:
            intent["type"] = "utility"
            intent["operation"] = "statistics"
            intent["parameters"] = ["numbers"]

        elif "转换" in desc_lower or "换算" in desc_lower:
            intent["type"] = "utility"
            intent["operation"] = "conversion"
            intent["parameters"] = ["value", "unit_from", "unit_to"]

        elif "api" in desc_lower or "请求" in desc_lower or "调用" in desc_lower:
            intent["type"] = "utility"
            intent["operation"] = "api"
            intent["parameters"] = ["url", "method"]

        else:
            # 默认为通用文本处理
            intent["type"] = "utility"
            intent["operation"] = "text_processing"

        return intent

    def _extract_operations(self, description: str) -> List[str]:
        """
        提取运算操作

        Args:
            description: 描述文本

        Returns:
            操作列表
        """
        operations = []

        if "和" in description or "加" in description:
            operations.append("add")
        if "差" in description or "减" in description:
            operations.append("subtract")
        if "积" in description or "乘" in description:
            operations.append("multiply")
        if "商" in description or "除" in description:
            operations.append("divide")

        if not operations:
            operations = ["add", "subtract", "multiply", "divide"]

        return operations

    def _generate_skill_name(self, description: str) -> str:
        """
        生成 skill 名称

        Args:
            description: 描述文本

        Returns:
            skill 名称（仅包含小写字母、数字、下划线和连字符）
        """
        desc_lower = description.lower()

        if "问候" in desc_lower or "打招呼" in desc_lower:
            return "greeting-nl"
        elif "计算" in desc_lower or "运算" in desc_lower:
            return "calculator-nl"
        elif "格式化" in desc_lower or "json" in desc_lower:
            return "formatter-nl"
        elif "统计" in desc_lower:
            return "statistics-nl"
        elif "抓取" in desc_lower or "爬取" in desc_lower or "新闻" in desc_lower:
            return "news-fetcher-nl"
        elif "转换" in desc_lower or "换算" in desc_lower:
            return "converter-nl"
        elif "api" in desc_lower or "请求" in desc_lower:
            return "api-client-nl"
        else:
            # 生成通用名称 - 只使用英文单词
            # 提取英文字母和数字
            words = re.findall(r'[a-zA-Z0-9]+', description)
            if words:
                # 转换为小写并限制长度
                name_parts = [w.lower()[:10] for w in words[:3]]
                return f"{'-'.join(name_parts)}-nl"
            return "custom-skill-nl"

    def _generate_code(self, description: str, intent: Dict[str, Any]) -> str:
        """
        生成代码

        Args:
            description: 描述文本
            intent: 意图分析结果

        Returns:
            生成的代码
        """
        operation = intent.get("operation", "general")

        if operation == "greeting":
            return self._generate_greeting_code(description)
        elif operation == "calculation":
            return self._generate_calculation_code(description, intent)
        elif operation == "format":
            return self._generate_format_code(description)
        elif operation == "statistics":
            return self._generate_statistics_code(description)
        elif operation == "conversion":
            return self._generate_conversion_code(description)
        elif operation == "api":
            return self._generate_api_code(description)
        else:
            return self._generate_generic_code(description)

    def _generate_greeting_code(self, description: str) -> str:
        """生成问候代码"""
        code = '''def execute(parameters):
    """
    问候技能 - 向用户打招呼

    参数：
    - name: 名字（可选，默认为"朋友"）
    - greeting: 问候语（可选，默认为"你好"）
    """
    name = parameters.get("name", "朋友")
    greeting = parameters.get("greeting", "你好")

    return f"{greeting}，{name}！"
'''
        return code

    def _generate_calculation_code(self, description: str, intent: Dict[str, Any]) -> str:
        """生成计算代码"""
        operations = intent.get("operations", ["add", "subtract", "multiply", "divide"])

        operations_code = ""
        for op in operations:
            if op == "add":
                operations_code += '    "和": a + b,\n'
            elif op == "subtract":
                operations_code += '    "差": a - b,\n'
            elif op == "multiply":
                operations_code += '    "积": a * b,\n'
            elif op == "divide":
                operations_code += '    "商": a / b if b != 0 else "无法除以零",\n'

        code = f'''def execute(parameters):
    """
    计算技能 - 执行数学运算

    参数：
    - a: 第一个数字
    - b: 第二个数字
    """
    a = parameters.get("a", 0)
    b = parameters.get("b", 0)

    operations = {{
{operations_code}
    }}

    return operations
'''
        return code

    def _generate_format_code(self, description: str) -> str:
        """生成格式化代码"""
        code = '''import json

def execute(parameters):
    """
    数据格式化技能

    参数：
    - data: 要格式化的数据
    - mode: 格式化模式（pretty/compact）
    """
    data = parameters.get("data", {})
    mode = parameters.get("mode", "pretty")

    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            return {"error": "无效的 JSON 字符串"}

    if mode == "compact":
        return json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    else:
        return json.dumps(data, indent=2, ensure_ascii=False)
'''
        return code

    def _generate_statistics_code(self, description: str) -> str:
        """生成统计代码"""
        code = '''def execute(parameters):
    """
    数据统计技能 - 计算统计信息

    参数：
    - numbers: 数字列表
    """
    numbers = parameters.get("numbers", [])

    if not numbers:
        return {"error": "请提供数字列表"}

    result = {
        "总数": len(numbers),
        "总和": sum(numbers),
        "平均值": sum(numbers) / len(numbers),
        "最大值": max(numbers),
        "最小值": min(numbers)
    }

    return result
'''
        return code

    def _generate_conversion_code(self, description: str) -> str:
        """生成转换代码"""
        code = '''def execute(parameters):
    """
    单位转换技能

    参数：
    - value: 要转换的数值
    - unit_from: 原单位
    - unit_to: 目标单位
    """
    value = parameters.get("value", 0)
    unit_from = parameters.get("unit_from", "")
    unit_to = parameters.get("unit_to", "")

    # 简单的温度转换示例
    if unit_from == "celsius" and unit_to == "fahrenheit":
        result = value * 9/5 + 32
    elif unit_from == "fahrenheit" and unit_to == "celsius":
        result = (value - 32) * 5/9
    else:
        return {"error": "不支持的转换类型"}

    return f"{value} {unit_from} = {result} {unit_to}"
'''
        return code

    def _generate_api_code(self, description: str) -> str:
        """生成 API 调用代码"""
        code = '''import requests

def execute(parameters):
    """
    API 调用技能

    参数：
    - url: API 地址
    - method: 请求方法（GET/POST）
    - data: 请求数据（可选）
    """
    url = parameters.get("url", "")
    method = parameters.get("method", "GET").upper()
    data = parameters.get("data", {})

    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        else:
            return {"error": f"不支持的请求方法: {method}"}

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API 请求失败: {response.status_code}"}

    except Exception as e:
        return {"error": f"请求异常: {str(e)}"}
'''
        return code

    def _generate_generic_code(self, description: str) -> str:
        """生成通用代码"""
        code = '''def execute(parameters):
    """
    自定义技能

    根据你的自然语言描述自动生成
    """
    # 根据你的需求实现功能
    result = "这是自动生成的技能，请根据实际需求修改代码"

    return result
'''
        return code

    def _create_skill(
        self,
        skill_name: str,
        description: str,
        code: str,
        intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建 skill 文件

        Args:
            skill_name: skill 名称
            description: 自然语言描述
            code: 生成的代码
            intent: 意图分析结果

        Returns:
            创建结果
        """
        try:
            # 创建 skill 目录
            skill_dir = self.skills_dir / skill_name
            scripts_dir = skill_dir / "scripts"

            skill_dir.mkdir(parents=True, exist_ok=True)
            scripts_dir.mkdir(exist_ok=True)

            # 生成 SKILL.md
            skill_md = self._generate_skill_md(skill_name, description, intent)
            (skill_dir / "SKILL.md").write_text(skill_md, encoding='utf-8')

            # 生成执行脚本
            (scripts_dir / "main.py").write_text(code, encoding='utf-8')

            self.logger.info(f"成功创建 skill: {skill_name}")

            return {
                "success": True,
                "skill_name": skill_name,
                "path": str(skill_dir),
                "description": description,
                "intent": intent
            }

        except Exception as e:
            self.logger.error(f"创建 skill 失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_skill_md(
        self,
        skill_name: str,
        description: str,
        intent: Dict[str, Any]
    ) -> str:
        """
        生成 SKILL.md 内容 - 符合 Agent Skills 规范

        Args:
            skill_name: skill 名称
            description: 描述文本
            intent: 意图分析结果

        Returns:
            SKILL.md 内容
        """
        operation = intent.get("operation", "general")
        parameters = intent.get("parameters", [])

        # 推断需要的工具
        allowed_tools = self._infer_allowed_tools(operation, intent)

        # 推断兼容性信息
        compatibility = self._infer_compatibility(operation, intent)

        # 构建参数文档
        params_md = ""
        for param in parameters:
            params_md += f"- `{param}`: 参数说明\n"

        # 构建使用场景描述
        usage_scenarios = self._generate_usage_scenarios(operation, description)

        skill_md = f'''---
name: {skill_name}
description: {description}. Use when {usage_scenarios}.
license: MIT
compatibility: {compatibility}
metadata:
  version: "1.0.0"
  author: AI Generated
  category: utility
  generated_at: "{datetime.now().isoformat()}"
  operation: {operation}
---

# {skill_name.replace("-", " ").title()}

## When to use this skill

{description}.

Use this skill when:
{self._generate_when_to_use(operation)}

## How to use

### Parameters

{params_md if params_md else "- `parameters`: 参数字典 (optional)"}

### Example

```bash
skill-service run {skill_name}
```

Or with parameters:

```bash
skill-service run {skill_name} --param key=value
```

## Implementation

This skill was automatically generated from natural language description.
You may need to adjust the implementation based on your specific requirements.

## Notes

- This is auto-generated code
- Review and test before production use
- Customize as needed for your use case
'''
        return skill_md

    def _infer_allowed_tools(self, operation: str, intent: Dict[str, Any]) -> str:
        """
        根据操作类型推断需要的工具

        Args:
            operation: 操作类型
            intent: 意图分析结果

        Returns:
            allowed-tools 字符串
        """
        tools = ["Read", "Write"]

        if operation in ["api", "fetch"]:
            tools.extend(["Fetch", "Bash(curl:*)"])
        elif operation == "calculation":
            tools.append("Bash(python:*)")
        elif operation in ["greeting", "text_processing"]:
            pass  # 基础工具足够
        elif operation == "format":
            tools.append("Bash(python:*)")
        else:
            # 默认添加 Python 执行能力
            tools.append("Bash(python:*)")

        return " ".join(tools)

    def _infer_compatibility(self, operation: str, intent: Dict[str, Any]) -> str:
        """
        推断兼容性信息

        Args:
            operation: 操作类型
            intent: 意图分析结果

        Returns:
            兼容性描述字符串
        """
        requirements = ["Requires Python 3.9+"]

        if operation == "api":
            requirements.append("requires requests library")
        elif operation == "calculation":
            requirements.append("standard library only")
        elif operation == "format":
            requirements.append("requires json module")

        return "; ".join(requirements)

    def _generate_usage_scenarios(self, operation: str, description: str) -> str:
        """
        生成使用场景描述

        Args:
            operation: 操作类型
            description: 原始描述

        Returns:
            使用场景字符串
        """
        scenarios = {
            "greeting": "user needs a greeting or welcome message",
            "calculation": "user needs to perform mathematical calculations",
            "format": "user needs to format or structure data",
            "statistics": "user needs statistical analysis of data",
            "conversion": "user needs to convert between units or formats",
            "api": "user needs to make API calls or fetch data from web services",
            "text_processing": "user needs to process or transform text",
        }

        return scenarios.get(operation, "user needs to perform related tasks")

    def _generate_when_to_use(self, operation: str) -> str:
        """
        生成 "When to use" 列表

        Args:
            operation: 操作类型

        Returns:
            Markdown 列表字符串
        """
        scenarios = {
            "greeting": [
                "User asks for a greeting or welcome message",
                "User wants to personalize a message with a name",
            ],
            "calculation": [
                "User needs to perform mathematical operations",
                "User asks about sums, differences, products, or quotients",
            ],
            "format": [
                "User needs to format JSON or other data",
                "User wants to pretty-print or compact data",
            ],
            "statistics": [
                "User needs statistical analysis of a dataset",
                "User asks for averages, maximums, or minimums",
            ],
            "conversion": [
                "User needs to convert between units",
                "User asks for temperature, length, or other conversions",
            ],
            "api": [
                "User needs to fetch data from a web API",
                "User wants to make HTTP requests",
            ],
            "text_processing": [
                "User needs to process or transform text",
                "User has custom text processing requirements",
            ],
        }

        default = [
            "User has a task related to this skill's functionality",
            "User explicitly requests this type of operation",
        ]

        items = scenarios.get(operation, default)
        return "\n".join(f"- {item}" for item in items)


def create_skill_from_text(description: str, skill_name: str = None) -> Dict[str, Any]:
    """
    从自然语言文本创建 skill（便捷函数）

    Args:
        description: 自然语言描述
        skill_name: skill 名称（可选）

    Returns:
        创建结果
    """
    generator = NaturalLanguageSkillGenerator()
    return generator.generate_from_description(description, skill_name)


if __name__ == "__main__":
    # 测试生成器
    test_descriptions = [
        "创建一个问候技能，可以自定义名字和问候语",
        "创建一个计算技能，计算两个数的和、差、积、商",
        "创建一个技能，格式化JSON数据",
        "创建一个技能，计算数字列表的平均值、最大值、最小值"
    ]

    generator = NaturalLanguageSkillGenerator()

    for desc in test_descriptions:
        print(f"\n描述: {desc}")
        result = generator.generate_from_description(desc)
        print(f"结果: {result}")
