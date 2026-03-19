"""
LLM-based Skill Generator - 使用大模型生成 Skill 代码

这个模块替代了原来的基于规则的 nl_generator，使用 LLM 来：
1. 分析用户自然语言描述
2. 生成高质量的 Python 代码
3. 创建完整的 SKILL.md 文档
"""
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from skill_service.llm.provider import LLMProvider, LLMMessage
from skill_service.utils.logger import get_logger
from skill_service.utils.validator import validate_skill_name

logger = get_logger(__name__)


class LLMSkillGenerator:
    """
    LLM-based Skill 生成器
    
    使用大模型从自然语言描述生成完整的 skill
    """
    
    def __init__(self, llm_provider: LLMProvider):
        """
        初始化生成器
        
        Args:
            llm_provider: LLM Provider 实例
        """
        self.llm = llm_provider
        self.logger = logger
        self.skills_dir = Path("./skills")
    
    async def generate(
        self,
        description: str,
        skill_name: Optional[str] = None,
        examples: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        从自然语言描述生成 skill
        
        Args:
            description: 自然语言描述
            skill_name: 指定的 skill 名称（可选）
            examples: 示例输入输出（可选）
            
        Returns:
            生成结果
        """
        self.logger.info(f"开始生成 skill: {description[:50]}...")
        
        # 如果没有指定名称，让 LLM 生成
        if not skill_name:
            skill_name = await self._generate_skill_name(description)
        
        # 验证名称格式
        name_errors = validate_skill_name(skill_name)
        if name_errors:
            skill_name = self._sanitize_name(skill_name)
        
        try:
            # 生成代码
            code = await self._generate_code(description, skill_name, examples)
            
            # 生成 SKILL.md
            skill_md = await self._generate_skill_md(description, skill_name, code)
            
            # 创建 skill 目录和文件
            result = self._create_skill_files(skill_name, skill_md, code)
            
            self.logger.info(f"成功生成 skill: {skill_name}")
            return result
            
        except Exception as e:
            self.logger.error(f"生成 skill 失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _generate_skill_name(self, description: str) -> str:
        """
        使用 LLM 生成 skill 名称
        
        Args:
            description: 描述
            
        Returns:
            skill 名称
        """
        prompt = f"""根据以下描述，生成一个简短的 skill 名称。

要求：
- 使用小写字母和连字符
- 简洁明了，2-3 个单词
- 只输出名称，不要其他内容

描述: {description}

Skill 名称:"""
        
        messages = [
            LLMMessage(role="system", content="你是一个命名专家，专门为软件功能生成简洁的名称。"),
            LLMMessage(role="user", content=prompt)
        ]
        
        try:
            response = await self.llm.chat(messages, temperature=0.3, max_tokens=50)
            name = response.content.strip().lower()
            
            # 清理名称
            name = re.sub(r'[^a-z0-9\-]', '-', name)
            name = re.sub(r'-+', '-', name)
            name = name.strip('-')
            
            return name or "custom-skill"
            
        except Exception as e:
            self.logger.error(f"生成名称失败: {e}")
            return "custom-skill"
    
    async def _generate_code(
        self,
        description: str,
        skill_name: str,
        examples: Optional[List[Dict]] = None
    ) -> str:
        """
        生成 Python 代码
        
        Args:
            description: 描述
            skill_name: skill 名称
            examples: 示例
            
        Returns:
            Python 代码
        """
        examples_text = ""
        if examples:
            examples_text = "\n## 示例\n"
            for i, ex in enumerate(examples, 1):
                examples_text += f"\n示例 {i}:\n"
                examples_text += f"输入: {json.dumps(ex.get('input', {}), ensure_ascii=False)}\n"
                examples_text += f"输出: {json.dumps(ex.get('output', ''), ensure_ascii=False)}\n"
        
        prompt = f"""根据以下描述，生成一个 Python 函数的 skill 代码。

## 描述
{description}{examples_text}

## 要求

1. 函数签名必须是: `def execute(parameters: dict) -> Any:`
2. parameters 是字典，包含所有输入参数
3. 返回可以是任意类型（字符串、字典、列表等）
4. 添加详细的中文文档字符串，说明功能、参数和返回值
5. 包含适当的错误处理
6. 只输出代码，不要输出 markdown 代码块标记
7. 如果需要外部库，在注释中说明

## 输出格式

直接输出 Python 代码，格式如下:

def execute(parameters):
    \"\"\"
    功能描述
    
    Args:
        parameters: 参数字典
            - param1: 参数1说明
            - param2: 参数2说明
    
    Returns:
        返回值说明
    \"\"\"
    # 实现代码
    ...

请生成代码:"""
        
        messages = [
            LLMMessage(role="system", content="你是一个 Python 专家，擅长编写清晰、健壮的函数代码。"),
            LLMMessage(role="user", content=prompt)
        ]
        
        try:
            response = await self.llm.chat(messages, temperature=0.5, max_tokens=2000)
            code = response.content.strip()
            
            # 移除可能的 markdown 代码块标记
            code = self._extract_code_from_markdown(code)
            
            # 验证代码包含 execute 函数
            if "def execute(" not in code:
                raise ValueError("生成的代码缺少 execute 函数")
            
            return code
            
        except Exception as e:
            self.logger.error(f"生成代码失败: {e}")
            raise
    
    async def _generate_skill_md(
        self,
        description: str,
        skill_name: str,
        code: str
    ) -> str:
        """
        生成 SKILL.md 内容
        
        Args:
            description: 描述
            skill_name: skill 名称
            code: 生成的代码
            
        Returns:
            SKILL.md 内容
        """
        # 从代码中提取参数信息
        params = self._extract_params_from_code(code)
        
        prompt = f"""为以下 skill 生成 SKILL.md 的 frontmatter 和描述部分。

## Skill 信息
- 名称: {skill_name}
- 描述: {description}
- 参数: {json.dumps(params, ensure_ascii=False)}

## 代码预览
```python
{code[:500]}...
```

## 要求

生成符合 Agent Skills 规范的 SKILL.md，包含:
1. YAML frontmatter (name, description, license, compatibility, metadata)
2. 使用场景描述 (When to use)
3. 使用方法 (How to use)
4. 参数说明
5. 示例

## 输出格式

```markdown
---
name: {skill_name}
description: 简短描述
license: MIT
compatibility: skill-service >=0.1.0
metadata:
  version: "1.0.0"
  author: AI Generated
  category: utility
---

# Skill 标题

## When to use this skill

...

## How to use

### Parameters
...

### Examples
...
```

请生成 SKILL.md 内容:"""
        
        messages = [
            LLMMessage(role="system", content="你是一个技术文档专家，擅长编写清晰的 skill 文档。"),
            LLMMessage(role="user", content=prompt)
        ]
        
        try:
            response = await self.llm.chat(messages, temperature=0.5, max_tokens=2000)
            skill_md = response.content.strip()
            
            # 移除可能的 markdown 代码块标记
            skill_md = self._extract_code_from_markdown(skill_md)
            
            return skill_md
            
        except Exception as e:
            self.logger.error(f"生成 SKILL.md 失败: {e}")
            # 返回默认模板
            return self._generate_default_skill_md(skill_name, description, params)
    
    def _create_skill_files(
        self,
        skill_name: str,
        skill_md: str,
        code: str
    ) -> Dict[str, Any]:
        """
        创建 skill 文件
        
        Args:
            skill_name: skill 名称
            skill_md: SKILL.md 内容
            code: 代码
            
        Returns:
            创建结果
        """
        try:
            # 创建目录
            skill_dir = self.skills_dir / skill_name
            scripts_dir = skill_dir / "scripts"
            
            skill_dir.mkdir(parents=True, exist_ok=True)
            scripts_dir.mkdir(exist_ok=True)
            
            # 写入文件
            (skill_dir / "SKILL.md").write_text(skill_md, encoding='utf-8')
            (scripts_dir / "main.py").write_text(code, encoding='utf-8')
            
            return {
                "success": True,
                "skill_name": skill_name,
                "path": str(skill_dir),
                "files_created": [
                    str(skill_dir / "SKILL.md"),
                    str(scripts_dir / "main.py")
                ]
            }
            
        except Exception as e:
            self.logger.error(f"创建文件失败: {e}")
            raise
    
    def _extract_params_from_code(self, code: str) -> List[Dict]:
        """
        从代码中提取参数信息
        
        Args:
            code: Python 代码
            
        Returns:
            参数列表
        """
        params = []
        
        # 简单提取 docstring 中的参数说明
        docstring_match = re.search(r'"""(.*?)"""', code, re.DOTALL)
        if docstring_match:
            docstring = docstring_match.group(1)
            
            # 查找 Args 部分
            args_match = re.search(r'Args:(.*?)(?:Returns:|Raises:|"""|$)', docstring, re.DOTALL)
            if args_match:
                args_section = args_match.group(1)
                
                # 提取参数行
                for line in args_section.split('\n'):
                    line = line.strip()
                    if line.startswith('-') or line.startswith('*'):
                        # 提取参数名和描述
                        param_match = re.match(r'[-*]\s*(\w+):\s*(.+)', line)
                        if param_match:
                            params.append({
                                "name": param_match.group(1),
                                "description": param_match.group(2)
                            })
        
        return params
    
    def _extract_code_from_markdown(self, text: str) -> str:
        """
        从 markdown 中提取代码
        
        Args:
            text: 可能包含 markdown 代码块的文本
            
        Returns:
            纯代码
        """
        text = text.strip()
        
        # 移除 ```python 或 ``` 标记
        if text.startswith("```"):
            lines = text.split('\n')
            # 移除第一行 (```python)
            if lines[0].startswith("```"):
                lines = lines[1:]
            # 移除最后一行 (```)
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            return '\n'.join(lines)
        
        return text
    
    def _sanitize_name(self, name: str) -> str:
        """
        清理 skill 名称
        
        Args:
            name: 原始名称
            
        Returns:
            清理后的名称
        """
        # 转换为小写
        name = name.lower()
        
        # 替换非法字符为连字符
        name = re.sub(r'[^a-z0-9\-]', '-', name)
        
        # 移除连续连字符
        name = re.sub(r'-+', '-', name)
        
        # 移除开头和结尾的连字符
        name = name.strip('-')
        
        # 限制长度
        if len(name) > 64:
            name = name[:64]
        
        return name or "custom-skill"
    
    def _generate_default_skill_md(
        self,
        skill_name: str,
        description: str,
        params: List[Dict]
    ) -> str:
        """
        生成默认的 SKILL.md
        
        Args:
            skill_name: skill 名称
            description: 描述
            params: 参数列表
            
        Returns:
            默认 SKILL.md 内容
        """
        params_md = ""
        for p in params:
            params_md += f"- `{p['name']}`: {p.get('description', '参数说明')}\n"
        
        if not params_md:
            params_md = "- `parameters`: 参数字典\n"
        
        return f"""---
name: {skill_name}
description: {description}
license: MIT
compatibility: skill-service >=0.1.0
metadata:
  version: "1.0.0"
  author: AI Generated
  category: utility
  generated_at: "{datetime.now().isoformat()}"
---

# {skill_name.replace('-', ' ').title()}

## When to use this skill

{description}

## How to use

### Parameters

{params_md}

### Example

```bash
skill-service run {skill_name}
```

## Notes

This skill was automatically generated from natural language description.
You may need to adjust the implementation based on your specific requirements.
"""
    
    async def improve_skill(
        self,
        skill_name: str,
        feedback: str,
        current_code: str
    ) -> Dict[str, Any]:
        """
        改进现有 skill
        
        Args:
            skill_name: skill 名称
            feedback: 改进建议
            current_code: 当前代码
            
        Returns:
            改进结果
        """
        prompt = f"""根据以下反馈，改进现有的 skill 代码。

## 当前代码

```python
{current_code}
```

## 改进建议
{feedback}

## 要求

1. 保持函数签名不变: `def execute(parameters: dict) -> Any:`
2. 根据反馈改进功能
3. 添加或更新文档字符串
4. 只输出改进后的代码

请输出改进后的代码:"""
        
        messages = [
            LLMMessage(role="system", content="你是一个代码优化专家，擅长根据反馈改进代码。"),
            LLMMessage(role="user", content=prompt)
        ]
        
        try:
            response = await self.llm.chat(messages, temperature=0.5, max_tokens=2000)
            improved_code = self._extract_code_from_markdown(response.content.strip())
            
            # 更新文件
            skill_dir = self.skills_dir / skill_name
            scripts_dir = skill_dir / "scripts"
            (scripts_dir / "main.py").write_text(improved_code, encoding='utf-8')
            
            return {
                "success": True,
                "skill_name": skill_name,
                "message": "Skill 已改进"
            }
            
        except Exception as e:
            self.logger.error(f"改进 skill 失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
