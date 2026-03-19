"""
LLM 集成模块 - 为大模型能力提供支持

主要组件:
- Provider: LLM 提供商接口
- SkillSelector: 智能 Skill 选择器
- SkillGenerator: LLM-based Skill 生成器
- MultiModelConfig: 多模型配置管理
"""

from .provider import LLMProvider, LLMMessage, LLMResponse
from .selector import SkillSelector
from .generator import LLMSkillGenerator
from .multi_model_config import (
    MultiModelConfigManager,
    ModelProfile,
    get_multi_model_manager,
    switch_model,
    get_current_model_info
)

__all__ = [
    "LLMProvider",
    "LLMMessage",
    "LLMResponse",
    "SkillSelector",
    "LLMSkillGenerator",
    "MultiModelConfigManager",
    "ModelProfile",
    "get_multi_model_manager",
    "switch_model",
    "get_current_model_info",
]
