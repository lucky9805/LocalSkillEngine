#!/usr/bin/env python3
"""
Self Improve Skill - Skill 自我改进工具

支持自动创建新 skill、优化现有 skill、分析 skill 质量
"""

import sys
import json
import re
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime


# Skill 模板库
SKILL_TEMPLATES = {
    "api": {
        "description": "调用外部 API 获取数据",
        "imports": ["import requests", "import json", "from typing import Dict, Any"],
        "features": ["HTTP 请求", "错误处理", "数据解析"]
    },
    "data_processing": {
        "description": "数据处理和分析",
        "imports": ["import json", "import re", "from typing import Dict, Any, List"],
        "features": ["数据清洗", "格式转换", "统计分析"]
    },
    "automation": {
        "description": "自动化任务执行",
        "imports": ["import os", "import subprocess", "from pathlib import Path"],
        "features": ["文件操作", "命令执行", "定时任务"]
    },
    "content_generation": {
        "description": "内容生成和创作",
        "imports": ["import json", "import re", "from datetime import datetime"],
        "features": ["模板渲染", "内容格式化", "多风格支持"]
    },
    "utility": {
        "description": "通用工具函数",
        "imports": ["import json", "from typing import Dict, Any"],
        "features": ["工具函数", "辅助方法", "通用接口"]
    }
}


# 代码模板
MAIN_PY_TEMPLATE = '''#!/usr/bin/env python3
"""
{skill_name} Skill

{description}
"""

{imports}


def execute(params: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    主执行函数
    
    Args:
        params: 参数字典
{param_docs}
    
    Returns:
        执行结果字典
    """
    params = params or {{}}
    
    try:
        # 参数验证
{param_validation}
        
        # 主逻辑
{main_logic}
        
        return {{
            "success": True,
            "output": result,
            "data": {{
{result_data}
            }}
        }}
        
    except Exception as e:
        import traceback
        return {{
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "output": None
        }}


{helper_functions}


def main():
    """命令行入口"""
    # 测试参数
    test_params = {{
{test_params}
    }}
    
    result = execute(test_params)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
'''


SKILL_MD_TEMPLATE = '''---
name: {skill_name}
description: {description}
license: MIT
compatibility: {compatibility}
metadata:
  version: "1.0.0"
  author: Skill Service Team
  category: {category}
  keywords:
{keywords}
---

# {skill_title} Skill

{description}

## 功能特性

{features}

## 使用方法

### 通过 chat 命令

```bash
python -m skill_service chat "{usage_example}"
```

### 通过 run 命令

```bash
python -m skill_service run {skill_name} {param_example}
```

## 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
{param_table}

## 示例

### 输入

```json
{input_example}
```

### 输出

```json
{output_example}
```

## 注意事项

- 首次使用建议先查看生成的代码
- 根据实际需求调整参数和逻辑
- 建议添加适当的错误处理

## 依赖

- Python 3.9+
{dependencies}
'''


def execute(params: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Self Improve Skill 主函数
    
    Args:
        params: 参数字典
            - action: 操作类型 (create/optimize/optimize-all/lint/analyze)
            - description: skill 描述（create 时必填）
            - skill_name: skill 名称（可选）
            - target_skill: 目标 skill 名称（optimize/lint 时必填）
            - auto_apply: 是否自动应用优化（默认 false）
            - style: 代码风格 (simple/standard/advanced)
    
    Returns:
        执行结果字典
    """
    params = params or {}
    
    action = params.get("action", "")
    
    if not action:
        return {
            "success": False,
            "error": "缺少必填参数: action（操作类型：create/optimize/optimize-all/lint/analyze）",
            "output": None
        }
    
    try:
        if action == "create":
            return create_skill(params)
        elif action == "optimize":
            return optimize_skill(params)
        elif action == "optimize-all":
            return optimize_all_skills(params)
        elif action == "lint":
            return lint_skill(params)
        elif action == "analyze":
            return analyze_skill(params)
        else:
            return {
                "success": False,
                "error": f"不支持的操作类型: {action}，支持的操作：create, optimize, optimize-all, lint, analyze",
                "output": None
            }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "output": None
        }


def create_skill(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    自动创建新 skill
    
    Args:
        params: 包含 description, skill_name, style 等参数
    
    Returns:
        创建结果
    """
    description = params.get("description", "")
    if not description:
        return {
            "success": False,
            "error": "create 操作需要提供 description 参数",
            "output": None
        }
    
    # 推断或生成 skill_name
    skill_name = params.get("skill_name") or infer_skill_name(description)
    style = params.get("style", "standard")
    
    # 分析意图，确定 skill 类型
    skill_type = analyze_skill_type(description)
    
    # 提取参数
    extracted_params = extract_params_from_description(description)
    
    # 生成代码
    main_py_content = generate_main_py(skill_name, description, skill_type, extracted_params, style)
    
    # 生成 SKILL.md
    skill_md_content = generate_skill_md(skill_name, description, skill_type, extracted_params)
    
    # 确定保存路径
    skills_dir = Path(__file__).parent.parent.parent
    skill_dir = skills_dir / skill_name
    scripts_dir = skill_dir / "scripts"
    
    # 检查是否已存在
    if skill_dir.exists():
        return {
            "success": False,
            "error": f"Skill '{skill_name}' 已存在，请使用其他名称或先删除现有 skill",
            "output": None
        }
    
    # 创建目录和文件
    try:
        skill_dir.mkdir(parents=True, exist_ok=True)
        scripts_dir.mkdir(exist_ok=True)
        
        (skill_dir / "SKILL.md").write_text(skill_md_content, encoding='utf-8')
        (scripts_dir / "main.py").write_text(main_py_content, encoding='utf-8')
        
        # 生成建议
        suggestions = generate_suggestions(skill_type, extracted_params)
        
        result_output = f"""✅ Skill 创建成功！

📁 文件位置:
   - SKILL.md: {skill_dir / 'SKILL.md'}
   - main.py: {scripts_dir / 'main.py'}

📋 Skill 信息:
   - 名称: {skill_name}
   - 类型: {skill_type}
   - 风格: {style}
   
🔧 功能特性:
{chr(10).join('   - ' + f for f in SKILL_TEMPLATES.get(skill_type, {}).get('features', ['自定义功能']))}

💡 使用示例:
   python -m skill_service run {skill_name} --param key=value
   
   或
   
   python -m skill_service chat "{description[:50]}..."

⚠️ 后续建议:
{chr(10).join('   ' + s for s in suggestions)}
"""
        
        return {
            "success": True,
            "output": result_output,
            "data": {
                "action": "create",
                "skill_name": skill_name,
                "path": str(skill_dir),
                "files_created": ["SKILL.md", "scripts/main.py"],
                "skill_type": skill_type,
                "style": style,
                "parameters": extracted_params,
                "suggestions": suggestions
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"创建文件失败: {str(e)}",
            "output": None
        }


def optimize_skill(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    优化现有 skill
    
    Args:
        params: 包含 target_skill, auto_apply 等参数
    
    Returns:
        优化结果和建议
    """
    target_skill = params.get("target_skill", "")
    auto_apply = str(params.get("auto_apply", "false")).lower() == "true"
    
    if not target_skill:
        return {
            "success": False,
            "error": "optimize 操作需要提供 target_skill 参数",
            "output": None
        }
    
    # 查找 skill
    skills_dir = Path(__file__).parent.parent.parent
    skill_dir = skills_dir / target_skill
    
    if not skill_dir.exists():
        return {
            "success": False,
            "error": f"Skill '{target_skill}' 不存在",
            "output": None
        }
    
    # 分析 skill
    analysis_result = analyze_skill_structure(skill_dir)
    
    # 生成优化建议
    suggestions = generate_optimization_suggestions(analysis_result)
    
    # 如果 auto_apply，应用部分优化
    applied_changes = []
    if auto_apply and suggestions:
        applied_changes = apply_optimizations(skill_dir, suggestions)
    
    # 格式化输出
    output_lines = [
        f"🔍 Skill 分析结果: {target_skill}",
        "",
        f"📊 质量评分: {analysis_result.get('score', 0)}/100",
        "",
        f"📁 文件结构:",
    ]
    
    for file_info in analysis_result.get('files', []):
        output_lines.append(f"   - {file_info['name']}: {file_info.get('status', 'unknown')}")
    
    if suggestions:
        output_lines.extend([
            "",
            f"💡 发现 {len(suggestions)} 个优化建议:",
            ""
        ])
        
        for i, suggestion in enumerate(suggestions, 1):
            severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(suggestion.get('severity', 'low'), "⚪")
            output_lines.append(f"{severity_emoji} {i}. [{suggestion.get('type', 'general')}] {suggestion.get('message', '')}")
            if 'file' in suggestion:
                output_lines.append(f"   文件: {suggestion['file']}")
    
    if applied_changes:
        output_lines.extend([
            "",
            f"✅ 已自动应用 {len(applied_changes)} 个优化:",
        ])
        for change in applied_changes:
            output_lines.append(f"   - {change}")
    
    return {
        "success": True,
        "output": "\n".join(output_lines),
        "data": {
            "action": "optimize",
            "target_skill": target_skill,
            "score": analysis_result.get('score', 0),
            "issues_found": len(suggestions),
            "suggestions": suggestions,
            "applied_changes": applied_changes,
            "optimized": len(applied_changes) > 0
        }
    }


def optimize_all_skills(params: Dict[str, Any]) -> Dict[str, Any]:
    """批量优化所有 skill"""
    skills_dir = Path(__file__).parent.parent.parent
    
    results = []
    total_skills = 0
    optimized_count = 0
    
    for skill_dir in skills_dir.iterdir():
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
            total_skills += 1
            
            # 跳过 self-improve 本身，避免递归
            if skill_dir.name == "self-improve-nl":
                continue
            
            try:
                result = optimize_skill({
                    "target_skill": skill_dir.name,
                    "auto_apply": params.get("auto_apply", False)
                })
                
                if result.get("success"):
                    results.append({
                        "skill": skill_dir.name,
                        "score": result.get("data", {}).get("score", 0),
                        "issues": result.get("data", {}).get("issues_found", 0)
                    })
                    
                    if result.get("data", {}).get("optimized", False):
                        optimized_count += 1
            except Exception as e:
                results.append({
                    "skill": skill_dir.name,
                    "error": str(e)
                })
    
    # 生成报告
    output_lines = [
        "📊 Skill 批量优化报告",
        "",
        f"总计检查: {total_skills} 个 skill",
        f"自动优化: {optimized_count} 个 skill",
        "",
        "📋 详细结果:",
    ]
    
    for result in results:
        if "error" in result:
            output_lines.append(f"   ❌ {result['skill']}: {result['error']}")
        else:
            score_emoji = "🟢" if result['score'] >= 80 else "🟡" if result['score'] >= 60 else "🔴"
            output_lines.append(f"   {score_emoji} {result['skill']}: 评分 {result['score']}, 问题 {result['issues']}")
    
    return {
        "success": True,
        "output": "\n".join(output_lines),
        "data": {
            "action": "optimize-all",
            "total_skills": total_skills,
            "optimized_count": optimized_count,
            "results": results
        }
    }


def lint_skill(params: Dict[str, Any]) -> Dict[str, Any]:
    """检查 skill 代码质量"""
    target_skill = params.get("target_skill", "")
    
    if not target_skill:
        return {
            "success": False,
            "error": "lint 操作需要提供 target_skill 参数",
            "output": None
        }
    
    skills_dir = Path(__file__).parent.parent.parent
    skill_dir = skills_dir / target_skill
    
    if not skill_dir.exists():
        return {
            "success": False,
            "error": f"Skill '{target_skill}' 不存在",
            "output": None
        }
    
    # 执行代码检查
    issues = []
    
    main_py_path = skill_dir / "scripts" / "main.py"
    if main_py_path.exists():
        code = main_py_path.read_text(encoding='utf-8')
        
        # 检查是否有 execute 函数
        if "def execute(" not in code:
            issues.append({
                "type": "error",
                "file": "scripts/main.py",
                "message": "缺少必需的 execute 函数",
                "severity": "high"
            })
        
        # 检查是否有 docstring
        if '"""' not in code and "'''" not in code:
            issues.append({
                "type": "warning",
                "file": "scripts/main.py",
                "message": "建议添加模块文档字符串",
                "severity": "low"
            })
        
        # 检查错误处理
        if "try:" not in code:
            issues.append({
                "type": "warning",
                "file": "scripts/main.py",
                "message": "建议添加错误处理（try-except）",
                "severity": "medium"
            })
    
    # 检查 SKILL.md
    skill_md_path = skill_dir / "SKILL.md"
    if skill_md_path.exists():
        content = skill_md_path.read_text(encoding='utf-8')
        
        if "---" not in content:
            issues.append({
                "type": "error",
                "file": "SKILL.md",
                "message": "缺少 YAML Front Matter（---）",
                "severity": "high"
            })
        
        if "name:" not in content:
            issues.append({
                "type": "error",
                "file": "SKILL.md",
                "message": "缺少 name 字段",
                "severity": "high"
            })
    else:
        issues.append({
            "type": "error",
            "file": "SKILL.md",
            "message": "缺少 SKILL.md 文件",
            "severity": "high"
        })
    
    # 生成报告
    output_lines = [
        f"🔍 Skill 代码检查: {target_skill}",
        "",
        f"发现 {len(issues)} 个问题:",
        ""
    ]
    
    for issue in issues:
        severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(issue['severity'], "⚪")
        output_lines.append(f"{severity_emoji} [{issue['type'].upper()}] {issue['file']}")
        output_lines.append(f"   {issue['message']}")
        output_lines.append("")
    
    if not issues:
        output_lines.append("✅ 未发现问题，代码质量良好！")
    
    return {
        "success": True,
        "output": "\n".join(output_lines),
        "data": {
            "action": "lint",
            "target_skill": target_skill,
            "issues_found": len(issues),
            "issues": issues,
            "passed": len(issues) == 0
        }
    }


def analyze_skill(params: Dict[str, Any]) -> Dict[str, Any]:
    """分析 skill 结构和功能"""
    target_skill = params.get("target_skill", "")
    
    if not target_skill:
        return {
            "success": False,
            "error": "analyze 操作需要提供 target_skill 参数",
            "output": None
        }
    
    skills_dir = Path(__file__).parent.parent.parent
    skill_dir = skills_dir / target_skill
    
    if not skill_dir.exists():
        return {
            "success": False,
            "error": f"Skill '{target_skill}' 不存在",
            "output": None
        }
    
    analysis = analyze_skill_structure(skill_dir)
    
    output_lines = [
        f"📊 Skill 分析报告: {target_skill}",
        "",
        f"综合评分: {analysis.get('score', 0)}/100",
        "",
        "📁 文件结构:",
    ]
    
    for file_info in analysis.get('files', []):
        size = file_info.get('size', 0)
        size_str = f"{size} bytes" if size < 1024 else f"{size/1024:.1f} KB"
        output_lines.append(f"   - {file_info['name']}: {size_str}")
    
    output_lines.extend([
        "",
        "🔧 功能分析:",
        f"   - 参数数量: {analysis.get('param_count', 0)}",
        f"   - 函数数量: {analysis.get('function_count', 0)}",
        f"   - 代码行数: {analysis.get('code_lines', 0)}",
        "",
        "📋 质量指标:",
        f"   - 文档完整性: {analysis.get('doc_score', 0)}%",
        f"   - 代码规范: {analysis.get('style_score', 0)}%",
        f"   - 错误处理: {analysis.get('error_score', 0)}%",
    ])
    
    return {
        "success": True,
        "output": "\n".join(output_lines),
        "data": analysis
    }


# ============== 辅助函数 ==============

def infer_skill_name(description: str) -> str:
    """从描述中推断 skill 名称"""
    # 提取关键词
    keywords = []
    
    # 常见模式匹配
    patterns = [
        r"(?:创建|生成|制作)(?:一个|一种)?(\w+)",
        r"(\w+)(?:工具|助手|服务|系统)",
        r"(?:查询|获取|抓取)(\w+)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description)
        if match:
            keywords.append(match.group(1))
    
    # 如果没有匹配到，使用描述的前两个词
    if not keywords:
        words = re.findall(r'[\u4e00-\u9fff\w]+', description)
        keywords = words[:2] if words else ["skill"]
    
    # 转换为 kebab-case
    name = "-".join(keywords).lower()
    name = re.sub(r'[^\w\-]', '', name)
    
    # 确保名称有效
    if not name or name == "-":
        name = "auto-generated-skill"
    
    return name[:50]  # 限制长度


def analyze_skill_type(description: str) -> str:
    """分析 skill 类型"""
    desc_lower = description.lower()
    
    if any(kw in desc_lower for kw in ["api", "接口", "请求", "http", "查询", "获取数据"]):
        return "api"
    elif any(kw in desc_lower for kw in ["处理", "分析", "转换", "清洗", "计算"]):
        return "data_processing"
    elif any(kw in desc_lower for kw in ["自动", "定时", "脚本", "批处理", "任务"]):
        return "automation"
    elif any(kw in desc_lower for kw in ["生成", "写作", "创作", "内容", "文章", "博客"]):
        return "content_generation"
    else:
        return "utility"


def extract_params_from_description(description: str) -> List[Dict[str, str]]:
    """从描述中提取参数"""
    params = []
    
    # 匹配模式：支持XXX、输入YYY
    param_patterns = [
        r"支持([\w\、]+)",
        r"输入([\w\、]+)",
        r"参数[:：]\s*([\w\、,]+)",
        r"可以([\w\、]+)",
    ]
    
    for pattern in param_patterns:
        matches = re.findall(pattern, description)
        for match in matches:
            # 分割多个参数
            param_names = re.split(r'[\、,，]', match)
            for name in param_names:
                name = name.strip()
                if name and len(name) <= 20:
                    params.append({
                        "name": name,
                        "type": "string",
                        "description": f"{name}参数",
                        "required": "false"
                    })
    
    # 去重
    seen = set()
    unique_params = []
    for p in params:
        if p["name"] not in seen:
            seen.add(p["name"])
            unique_params.append(p)
    
    return unique_params[:5]  # 最多5个参数


def generate_main_py(skill_name: str, description: str, skill_type: str, 
                     params: List[Dict], style: str) -> str:
    """生成 main.py 代码"""
    
    # 获取模板
    template = SKILL_TEMPLATES.get(skill_type, SKILL_TEMPLATES["utility"])
    
    # 生成导入语句
    imports = "\n".join(template["imports"])
    
    # 生成参数文档
    param_docs = ""
    for param in params:
        param_docs += f"            - {param['name']}: {param['description']}\n"
    if not param_docs:
        param_docs = "            - 无特定参数\n"
    
    # 生成参数验证
    param_validation = ""
    for param in params:
        param_validation += f"        # {param['name']} = params.get('{param['name']}', '')\n"
    if not param_validation:
        param_validation = "        # 参数处理\n        pass"
    
    # 生成主逻辑
    main_logic = generate_main_logic(skill_type, params)
    
    # 生成返回数据
    result_data = '                "result": "操作成功"'
    
    # 生成辅助函数
    helper_functions = generate_helper_functions(skill_type)
    
    # 生成测试参数
    test_params_list = [f'        "{p["name"]}": "test_value"' for p in params[:2]]
    test_params = ",\n".join(test_params_list) if test_params_list else '        "example": "value"'
    
    return MAIN_PY_TEMPLATE.format(
        skill_name=skill_name,
        description=description,
        imports=imports,
        param_docs=param_docs,
        param_validation=param_validation,
        main_logic=main_logic,
        result_data=result_data,
        helper_functions=helper_functions,
        test_params=test_params
    )


def generate_main_logic(skill_type: str, params: List[Dict]) -> str:
    """生成主逻辑代码"""
    
    if skill_type == "api":
        return '''        # API 调用示例
        # url = "https://api.example.com/data"
        # response = requests.get(url, timeout=30)
        # data = response.json()
        
        result = {
            "message": "API 调用成功",
            "data": {}
        }'''
    
    elif skill_type == "data_processing":
        return '''        # 数据处理示例
        # processed = process_data(input_data)
        
        result = {
            "message": "数据处理完成",
            "processed_count": 0
        }'''
    
    elif skill_type == "automation":
        return '''        # 自动化任务示例
        # execute_task()
        
        result = {
            "message": "任务执行完成",
            "status": "success"
        }'''
    
    elif skill_type == "content_generation":
        return '''        # 内容生成示例
        # content = generate_content(params)
        
        result = {
            "message": "内容生成完成",
            "content": "生成的内容..."
        }'''
    
    else:
        return '''        # 主逻辑实现
        result = {
            "message": "操作成功",
            "input_params": params
        }'''


def generate_helper_functions(skill_type: str) -> str:
    """生成辅助函数"""
    
    if skill_type == "api":
        return '''
def make_request(url: str, method: str = "GET", data: Dict = None) -> Dict:
    """发送 HTTP 请求"""
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=30)
        else:
            response = requests.post(url, json=data, timeout=30)
        
        return {
            "success": True,
            "status_code": response.status_code,
            "data": response.json() if response.content else {}
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }'''
    
    elif skill_type == "data_processing":
        return '''
def process_data(data: Any) -> Any:
    """处理数据"""
    # 实现数据处理逻辑
    return data'''
    
    else:
        return '''
def helper_function():
    """辅助函数示例"""
    pass'''


def generate_skill_md(skill_name: str, description: str, skill_type: str, 
                      params: List[Dict]) -> str:
    """生成 SKILL.md 内容"""
    
    template = SKILL_TEMPLATES.get(skill_type, SKILL_TEMPLATES["utility"])
    
    # 生成特性列表
    features = "\n".join(f"- {f}" for f in template["features"])
    
    # 生成关键词
    keywords_list = [skill_name.split("-")[0], "auto-generated"] + [p["name"] for p in params[:3]]
    keywords = "\n".join(f"    - {kw}" for kw in keywords_list if kw)
    
    # 生成参数表格
    if params:
        param_table = "\n".join(
            f"| {p['name']} | {p['type']} | {'是' if p.get('required') == 'true' else '否'} | {p['description']} |"
            for p in params
        )
    else:
        param_table = "| param1 | string | 否 | 示例参数 |"
    
    return SKILL_MD_TEMPLATE.format(
        skill_name=skill_name,
        skill_title=skill_name.replace("-", " ").title(),
        description=description,
        compatibility="Requires Python 3.9+",
        category=skill_type,
        keywords=keywords,
        features=features,
        usage_example=f"使用 {skill_name} 完成某项任务",
        param_example=" ".join(f"--param {p['name']}=value" for p in params[:2]) if params else "--param key=value",
        param_table=param_table,
        input_example=json.dumps({p["name"]: f"{p['name']}的值" for p in params[:2]}, ensure_ascii=False, indent=2) if params else '{"example": "value"}',
        output_example=json.dumps({"success": True, "output": "结果"}, ensure_ascii=False, indent=2),
        dependencies="- " + "\n- ".join(template["imports"])
    )


def generate_suggestions(skill_type: str, params: List[Dict]) -> List[str]:
    """生成后续建议"""
    suggestions = [
        "根据实际需求修改 main.py 中的逻辑",
        "完善 SKILL.md 中的使用示例",
    ]
    
    if skill_type == "api":
        suggestions.append("配置 API 密钥和请求参数")
    elif skill_type == "data_processing":
        suggestions.append("添加数据验证和清洗逻辑")
    
    if not params:
        suggestions.append("添加必要的参数定义")
    
    suggestions.append("添加单元测试确保代码质量")
    
    return suggestions


def analyze_skill_structure(skill_dir: Path) -> Dict[str, Any]:
    """分析 skill 结构"""
    
    analysis = {
        "skill_name": skill_dir.name,
        "files": [],
        "score": 0,
        "param_count": 0,
        "function_count": 0,
        "code_lines": 0,
        "doc_score": 0,
        "style_score": 0,
        "error_score": 0
    }
    
    # 检查文件
    skill_md_path = skill_dir / "SKILL.md"
    main_py_path = skill_dir / "scripts" / "main.py"
    
    if skill_md_path.exists():
        content = skill_md_path.read_text(encoding='utf-8')
        analysis["files"].append({
            "name": "SKILL.md",
            "size": len(content),
            "status": "ok"
        })
        
        # 检查文档完整性
        doc_checks = [
            "---" in content,  # YAML Front Matter
            "name:" in content,
            "description:" in content,
            "## " in content,  # 有章节
        ]
        analysis["doc_score"] = int(sum(doc_checks) / len(doc_checks) * 100)
    else:
        analysis["files"].append({
            "name": "SKILL.md",
            "size": 0,
            "status": "missing"
        })
    
    if main_py_path.exists():
        code = main_py_path.read_text(encoding='utf-8')
        analysis["files"].append({
            "name": "scripts/main.py",
            "size": len(code),
            "status": "ok"
        })
        
        # 分析代码
        analysis["code_lines"] = len(code.splitlines())
        analysis["function_count"] = len(re.findall(r'def \w+\(', code))
        
        # 检查代码规范
        style_checks = [
            '"""' in code or "'''" in code,  # 有文档字符串
            'def execute(' in code,  # 有 execute 函数
            'try:' in code,  # 有错误处理
            'import' in code,  # 有导入
        ]
        analysis["style_score"] = int(sum(style_checks) / len(style_checks) * 100)
        
        # 检查错误处理
        error_checks = [
            'try:' in code,
            'except' in code,
            'return {' in code and '"success"' in code
        ]
        analysis["error_score"] = int(sum(error_checks) / len(error_checks) * 100)
        
        # 提取参数数量
        param_match = re.search(r'Args:.*?(?:Returns:|"""|$)', code, re.DOTALL)
        if param_match:
            analysis["param_count"] = len(re.findall(r'- \w+:', param_match.group()))
    else:
        analysis["files"].append({
            "name": "scripts/main.py",
            "size": 0,
            "status": "missing"
        })
    
    # 计算综合评分
    analysis["score"] = int(
        (analysis.get("doc_score", 0) + 
         analysis.get("style_score", 0) + 
         analysis.get("error_score", 0)) / 3
    )
    
    return analysis


def generate_optimization_suggestions(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """生成优化建议"""
    suggestions = []
    
    if analysis.get("doc_score", 0) < 80:
        suggestions.append({
            "type": "documentation",
            "message": "文档不够完整，建议补充使用示例和参数说明",
            "severity": "medium"
        })
    
    if analysis.get("style_score", 0) < 80:
        suggestions.append({
            "type": "code_style",
            "message": "代码规范有待改进，建议添加类型注解和文档字符串",
            "severity": "low"
        })
    
    if analysis.get("error_score", 0) < 80:
        suggestions.append({
            "type": "error_handling",
            "message": "错误处理不够完善，建议添加更多的异常处理",
            "severity": "high"
        })
    
    if analysis.get("function_count", 0) < 2:
        suggestions.append({
            "type": "architecture",
            "message": "函数数量较少，建议将逻辑拆分为多个小函数",
            "severity": "low"
        })
    
    return suggestions


def apply_optimizations(skill_dir: Path, suggestions: List[Dict[str, Any]]) -> List[str]:
    """应用优化（简化版本，仅记录）"""
    applied = []
    
    for suggestion in suggestions:
        # 这里可以实现自动修复逻辑
        # 目前仅记录建议
        applied.append(f"[{suggestion['type']}] {suggestion['message']}")
    
    return applied


def main():
    """命令行入口"""
    # 默认测试：创建示例 skill
    test_params = {
        "action": "create",
        "description": "创建一个示例 skill，用于演示功能",
        "skill_name": "example-demo",
        "style": "standard"
    }
    
    result = execute(test_params)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
