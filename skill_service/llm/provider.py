"""
LLM Provider 接口 - 支持多种大模型

支持的提供商:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- 本地模型 (通过 OpenAI-compatible API)
- 其他兼容 OpenAI API 格式的服务
"""
import os
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, AsyncGenerator
from enum import Enum

from skill_service.utils.logger import get_logger

logger = get_logger(__name__)


class LLMProviderType(str, Enum):
    """LLM 提供商类型"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    LOCAL = "local"
    CUSTOM = "custom"


@dataclass
class LLMMessage:
    """LLM 消息"""
    role: str  # system, user, assistant, tool
    content: str
    name: Optional[str] = None  # for tool messages
    tool_calls: Optional[List[Dict]] = None  # for assistant messages with tool calls


@dataclass
class LLMResponse:
    """LLM 响应"""
    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: Optional[str] = None
    tool_calls: Optional[List[Dict]] = None
    raw_response: Optional[Any] = None


class LLMProvider(ABC):
    """
    LLM Provider 抽象基类
    
    所有 LLM 提供商都需要实现这个接口
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化 Provider
        
        Args:
            config: 配置字典，包含 api_key, base_url, model 等
        """
        self.config = config
        self.model = config.get("model", "gpt-3.5-turbo")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 2000)
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    async def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        对话接口
        
        Args:
            messages: 消息列表
            tools: 可用工具列表 (function calling)
            **kwargs: 额外参数
            
        Returns:
            LLM 响应
        """
        pass
    
    @abstractmethod
    async def stream_chat(
        self,
        messages: List[LLMMessage],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        流式对话接口
        
        Args:
            messages: 消息列表
            **kwargs: 额外参数
            
        Yields:
            文本片段
        """
        pass
    
    def format_messages(self, messages: List[LLMMessage]) -> List[Dict]:
        """
        格式化消息为标准格式
        
        Args:
            messages: LLMMessage 列表
            
        Returns:
            标准格式的消息字典列表
        """
        formatted = []
        for msg in messages:
            msg_dict = {"role": msg.role, "content": msg.content}
            if msg.name:
                msg_dict["name"] = msg.name
            if msg.tool_calls:
                msg_dict["tool_calls"] = msg.tool_calls
            formatted.append(msg_dict)
        return formatted


class OpenAIProvider(LLMProvider):
    """OpenAI Provider - 也支持 OpenAI-compatible API (如豆包、DeepSeek 等)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # 优先使用 config 中的 api_key，如果没有再从环境变量获取
        self.api_key = config.get("api_key")
        if not self.api_key:
            self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        
        # 对于自定义 OpenAI-compatible API，允许使用任意 API key
        is_custom = config.get("provider_type") == "custom" or (self.base_url and "ark.cn-beijing.volces.com" in self.base_url)
        
        if not self.api_key and not is_custom:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY env var or pass api_key in config.")
        
        # 对于自定义 API，如果没有 api_key，使用一个占位符（某些本地模型不需要）
        if not self.api_key:
            self.api_key = "custom-api-key"
        
        try:
            import openai
            # 临时清除 OPENAI_API_KEY 环境变量，避免干扰
            original_openai_key = os.environ.pop('OPENAI_API_KEY', None)
            try:
                self.client = openai.AsyncOpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
            finally:
                # 恢复环境变量
                if original_openai_key is not None:
                    os.environ['OPENAI_API_KEY'] = original_openai_key
        except ImportError:
            raise ImportError("openai package is required. Install with: pip install openai")
    
    async def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> LLMResponse:
        """OpenAI 对话接口"""
        try:
            params = {
                "model": kwargs.get("model", self.model),
                "messages": self.format_messages(messages),
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            }
            
            if tools:
                params["tools"] = tools
                params["tool_choice"] = kwargs.get("tool_choice", "auto")
            
            response = await self.client.chat.completions.create(**params)
            
            choice = response.choices[0]
            message = choice.message
            
            return LLMResponse(
                content=message.content or "",
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                finish_reason=choice.finish_reason,
                tool_calls=message.tool_calls if hasattr(message, 'tool_calls') else None,
                raw_response=response
            )
            
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            raise
    
    async def stream_chat(
        self,
        messages: List[LLMMessage],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """OpenAI 流式对话"""
        try:
            stream = await self.client.chat.completions.create(
                model=kwargs.get("model", self.model),
                messages=self.format_messages(messages),
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            self.logger.error(f"OpenAI streaming error: {e}")
            raise


class AnthropicProvider(LLMProvider):
    """Anthropic Claude Provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = config.get("base_url", "https://api.anthropic.com")
        
        if not self.api_key:
            raise ValueError("Anthropic API key is required. Set ANTHROPIC_API_KEY env var or pass api_key in config.")
        
        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(
                api_key=self.api_key,
                base_url=self.base_url
            )
        except ImportError:
            raise ImportError("anthropic package is required. Install with: pip install anthropic")
    
    async def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> LLMResponse:
        """Claude 对话接口"""
        try:
            # 分离 system message
            system_message = ""
            chat_messages = []
            
            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    chat_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            params = {
                "model": kwargs.get("model", self.model),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "temperature": kwargs.get("temperature", self.temperature),
                "messages": chat_messages,
            }
            
            if system_message:
                params["system"] = system_message
            
            if tools:
                params["tools"] = tools
            
            response = await self.client.messages.create(**params)
            
            # 提取文本内容
            content = ""
            for block in response.content:
                if block.type == "text":
                    content += block.text
            
            return LLMResponse(
                content=content,
                model=response.model,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                finish_reason=response.stop_reason,
                raw_response=response
            )
            
        except Exception as e:
            self.logger.error(f"Anthropic API error: {e}")
            raise
    
    async def stream_chat(
        self,
        messages: List[LLMMessage],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Claude 流式对话"""
        try:
            system_message = ""
            chat_messages = []
            
            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    chat_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            params = {
                "model": kwargs.get("model", self.model),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "temperature": kwargs.get("temperature", self.temperature),
                "messages": chat_messages,
                "stream": True
            }
            
            if system_message:
                params["system"] = system_message
            
            async with self.client.messages.stream(**params) as stream:
                async for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            self.logger.error(f"Anthropic streaming error: {e}")
            raise


class LocalProvider(LLMProvider):
    """
    本地模型 Provider
    
    支持通过 OpenAI-compatible API 运行的本地模型
    如: llama.cpp, ollama, text-generation-webui 等
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key", "not-needed")
        self.base_url = config.get("base_url", "http://localhost:8000/v1")
        
        try:
            import openai
            self.client = openai.AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        except ImportError:
            raise ImportError("openai package is required. Install with: pip install openai")
    
    async def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> LLMResponse:
        """本地模型对话接口"""
        try:
            params = {
                "model": kwargs.get("model", self.model),
                "messages": self.format_messages(messages),
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            }
            
            response = await self.client.chat.completions.create(**params)
            
            choice = response.choices[0]
            
            return LLMResponse(
                content=choice.message.content or "",
                model=response.model,
                usage=getattr(response, 'usage', {}),
                finish_reason=choice.finish_reason,
                raw_response=response
            )
            
        except Exception as e:
            self.logger.error(f"Local LLM API error: {e}")
            raise
    
    async def stream_chat(
        self,
        messages: List[LLMMessage],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """本地模型流式对话"""
        try:
            stream = await self.client.chat.completions.create(
                model=kwargs.get("model", self.model),
                messages=self.format_messages(messages),
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            self.logger.error(f"Local LLM streaming error: {e}")
            raise


def create_llm_provider(
    provider_type: LLMProviderType,
    config: Dict[str, Any]
) -> LLMProvider:
    """
    创建 LLM Provider 工厂函数
    
    Args:
        provider_type: 提供商类型
        config: 配置字典
        
    Returns:
        LLMProvider 实例
    """
    providers = {
        LLMProviderType.OPENAI: OpenAIProvider,
        LLMProviderType.ANTHROPIC: AnthropicProvider,
        LLMProviderType.LOCAL: LocalProvider,
        LLMProviderType.AZURE: OpenAIProvider,  # Azure 使用 OpenAI SDK
        LLMProviderType.CUSTOM: OpenAIProvider,  # 自定义 OpenAI-compatible API
    }
    
    provider_class = providers.get(provider_type)
    if not provider_class:
        raise ValueError(f"Unknown provider type: {provider_type}")
    
    # 传递 provider_type 到 config，用于特殊处理
    config["provider_type"] = provider_type.value
    
    return provider_class(config)
