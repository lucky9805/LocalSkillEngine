"""
智能 Skill Selector - 使用 LLM 判断何时调用哪个 skill

这个模块实现了基于大模型的 skill 选择逻辑：
1. 接收用户输入
2. 使用 LLM 分析意图
3. 从可用 skills 中选择最合适的
4. 提取调用参数
"""
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from skill_service.llm.provider import LLMProvider, LLMMessage, LLMResponse
from skill_service.models import Skill, SkillInfo
from skill_service.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SkillSelection:
    """Skill 选择结果"""
    skill_name: Optional[str]  # 选中的 skill 名称，None 表示不需要 skill
    parameters: Dict[str, Any]  # 提取的参数
    confidence: float  # 置信度 0-1
    reasoning: str  # 选择理由
    direct_response: Optional[str] = None  # 如果不调用 skill，直接回复的内容


class SkillSelector:
    """
    智能 Skill 选择器
    
    使用 LLM 来判断：
    - 用户输入是否需要调用 skill
    - 应该调用哪个 skill
    - 需要传递什么参数
    """
    
    def __init__(self, llm_provider: LLMProvider):
        """
        初始化选择器
        
        Args:
            llm_provider: LLM Provider 实例
        """
        self.llm = llm_provider
        self.logger = logger
    
    async def select_skill(
        self,
        user_input: str,
        available_skills: List[SkillInfo],
        conversation_context: Optional[List[Dict]] = None
    ) -> SkillSelection:
        """
        选择最合适的 skill
        
        Args:
            user_input: 用户输入
            available_skills: 可用的 skills 列表 (Tier 1: Catalog)
            conversation_context: 对话上下文（可选）
            
        Returns:
            SkillSelection 选择结果
        """
        if not available_skills:
            return SkillSelection(
                skill_name=None,
                parameters={},
                confidence=1.0,
                reasoning="没有可用的 skills",
                direct_response=user_input
            )
        
        # 构建 system prompt
        system_prompt = self._build_system_prompt(available_skills)
        
        # 构建用户消息
        user_message = self._build_user_message(user_input, conversation_context)
        
        # 调用 LLM
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_message)
        ]
        
        try:
            response = await self.llm.chat(
                messages=messages,
                temperature=0.1,  # 低温度，更确定性的输出
                max_tokens=1000
            )
            
            # 解析响应
            selection = self._parse_selection_response(response.content)
            return selection
            
        except Exception as e:
            self.logger.error(f"Skill selection failed: {e}")
            # 失败时返回空选择
            return SkillSelection(
                skill_name=None,
                parameters={},
                confidence=0.0,
                reasoning=f"选择过程出错: {e}",
                direct_response=user_input
            )
    
    def _build_system_prompt(self, skills: List[SkillInfo]) -> str:
        """
        构建系统提示词
        
        Args:
            skills: 可用 skills
            
        Returns:
            System prompt
        """
        skills_catalog = []
        for skill in skills:
            skills_catalog.append({
                "name": skill.name,
                "description": skill.description
            })
        
        prompt = f"""你是一个智能 Skill 选择器。你的任务是分析用户的输入，决定是否需要调用 skill，以及调用哪个 skill。

## 可用 Skills

```json
{json.dumps(skills_catalog, ensure_ascii=False, indent=2)}
```

## 任务

1. 分析用户输入的意图
2. 判断是否需要调用 skill：
   - 如果用户请求与某个 skill 的功能匹配，选择该 skill
   - 如果用户只是闲聊或询问信息，不需要调用 skill
   - 如果用户请求无法匹配任何 skill，不需要调用 skill

3. 如果需要调用 skill，提取必要的参数

## 输出格式

你必须以 JSON 格式输出，不要包含其他内容：

```json
{{
  "skill_name": "skill-name-or-null",
  "parameters": {{}},
  "confidence": 0.95,
  "reasoning": "选择理由",
  "direct_response": "如果不调用 skill，直接回复用户的内容"
}}
```

字段说明：
- `skill_name`: 选中的 skill 名称，如果不需要调用 skill 则为 null
- `parameters`: 调用 skill 需要的参数对象
- `confidence`: 置信度 0-1
- `reasoning`: 选择理由的简短说明
- `direct_response`: 如果不调用 skill，直接回复用户的内容（可选）

## 示例

用户输入: "计算 15 加 27"
输出:
```json
{{
  "skill_name": "calculator",
  "parameters": {{"operation": "add", "a": 15, "b": 27}},
  "confidence": 0.95,
  "reasoning": "用户需要进行加法计算，匹配 calculator skill"
}}
```

用户输入: "你好"
输出:
```json
{{
  "skill_name": null,
  "parameters": {{}},
  "confidence": 1.0,
  "reasoning": "用户只是打招呼，不需要调用 skill",
  "direct_response": "你好！有什么我可以帮助你的吗？"
}}
```

现在请分析用户的输入并输出 JSON 结果。"""
        
        return prompt
    
    def _build_user_message(
        self,
        user_input: str,
        context: Optional[List[Dict]] = None
    ) -> str:
        """
        构建用户消息
        
        Args:
            user_input: 用户输入
            context: 对话上下文
            
        Returns:
            用户消息
        """
        message = f"用户输入: {user_input}\n\n"
        
        if context:
            message += "对话上下文:\n"
            for msg in context[-5:]:  # 只取最近 5 条
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                message += f"{role}: {content}\n"
            message += "\n"
        
        message += "请分析并输出 JSON 结果："
        
        return message
    
    def _parse_selection_response(self, content: str) -> SkillSelection:
        """
        解析 LLM 的选择响应
        
        Args:
            content: LLM 响应内容
            
        Returns:
            SkillSelection
        """
        try:
            # 提取 JSON
            json_str = self._extract_json(content)
            data = json.loads(json_str)
            
            return SkillSelection(
                skill_name=data.get("skill_name"),
                parameters=data.get("parameters", {}),
                confidence=data.get("confidence", 0.0),
                reasoning=data.get("reasoning", ""),
                direct_response=data.get("direct_response")
            )
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse selection response: {e}")
            # 尝试从文本中提取 skill 名称
            return self._fallback_parse(content)
        except Exception as e:
            self.logger.error(f"Unexpected error parsing selection: {e}")
            return SkillSelection(
                skill_name=None,
                parameters={},
                confidence=0.0,
                reasoning="解析响应失败",
                direct_response=None
            )
    
    def _extract_json(self, content: str) -> str:
        """
        从文本中提取 JSON
        
        Args:
            content: 可能包含 JSON 的文本
            
        Returns:
            JSON 字符串
        """
        # 尝试直接解析
        content = content.strip()
        
        # 如果包裹在代码块中
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            return content[start:end].strip()
        
        if "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            return content[start:end].strip()
        
        # 尝试找到 JSON 对象
        if content.startswith("{") and content.endswith("}"):
            return content
        
        # 查找第一个 { 和最后一个 }
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1:
            return content[start:end+1]
        
        return content
    
    def _fallback_parse(self, content: str) -> SkillSelection:
        """
        备用解析方法
        
        当 JSON 解析失败时，尝试从文本中提取信息
        """
        content_lower = content.lower()
        
        # 检查是否包含 "不需要" "不调用" 等关键词
        if any(kw in content_lower for kw in ["不需要", "不调用", "none", "null", "不需要调用"]):
            return SkillSelection(
                skill_name=None,
                parameters={},
                confidence=0.5,
                reasoning="从文本分析，不需要调用 skill",
                direct_response=None
            )
        
        # 无法确定
        return SkillSelection(
            skill_name=None,
            parameters={},
            confidence=0.0,
            reasoning="无法解析 LLM 响应",
            direct_response=None
        )
    
    async def batch_select(
        self,
        user_inputs: List[str],
        available_skills: List[SkillInfo]
    ) -> List[SkillSelection]:
        """
        批量选择 skill
        
        Args:
            user_inputs: 用户输入列表
            available_skills: 可用 skills
            
        Returns:
            SkillSelection 列表
        """
        results = []
        for user_input in user_inputs:
            selection = await self.select_skill(user_input, available_skills)
            results.append(selection)
        return results
