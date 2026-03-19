"""
LLM 配置管理

管理 LLM 的 API keys、模型选择和其他配置
"""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from skill_service.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str = "openai"  # openai, anthropic, local, azure
    model: str = "gpt-3.5-turbo"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 60
    
    # 额外配置
    extra: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMConfig":
        """从字典创建配置"""
        return cls(
            provider=data.get("provider", "openai"),
            model=data.get("model", "gpt-3.5-turbo"),
            api_key=data.get("api_key"),
            base_url=data.get("base_url"),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 2000),
            timeout=data.get("timeout", 60),
            extra=data.get("extra", {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "provider": self.provider,
            "model": self.model,
            "api_key": self.api_key,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "extra": self.extra
        }


class LLMConfigManager:
    """
    LLM 配置管理器
    
    支持从多种来源加载配置：
    1. 环境变量
    2. 配置文件
    3. 代码中直接设置
    """
    
    def __init__(self):
        """初始化配置管理器"""
        self.config_file = Path.home() / ".skill-service" / "llm-config.yaml"
        self._config: Optional[LLMConfig] = None
        self._default_config = LLMConfig()
    
    def get_config(self) -> LLMConfig:
        """
        获取 LLM 配置
        
        按优先级加载：
        1. 已设置的配置
        2. 配置文件
        3. 环境变量
        4. 默认配置
        """
        if self._config:
            return self._config
        
        # 尝试从配置文件加载
        if self.config_file.exists():
            try:
                config = self._load_from_file()
                if config:
                    self._config = config
                    return config
            except Exception as e:
                logger.warning(f"Failed to load config from file: {e}")
        
        # 从环境变量加载
        config = self._load_from_env()
        if config:
            self._config = config
            return config
        
        # 返回默认配置
        return self._default_config
    
    def reload_config(self) -> LLMConfig:
        """
        强制重新加载配置（从文件或环境变量）
        
        用于在内存配置被清除后重新加载
        """
        self._config = None
        return self.get_config()
    
    def set_config(self, config: LLMConfig):
        """
        设置配置
        
        Args:
            config: LLM 配置
        """
        self._config = config
        logger.info(f"LLM config set: provider={config.provider}, model={config.model}")
    
    def set_provider(self, provider: str):
        """设置提供商"""
        config = self.get_config()
        config.provider = provider
        self._config = config
    
    def set_model(self, model: str):
        """设置模型"""
        config = self.get_config()
        config.model = model
        self._config = config
    
    def set_api_key(self, api_key: str):
        """设置 API key"""
        config = self.get_config()
        config.api_key = api_key
        self._config = config
    
    def save_config(self):
        """保存配置到文件"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            config = self.get_config()
            
            # 保存时隐藏 API key
            data = config.to_dict()
            if data.get("api_key"):
                data["api_key"] = "***masked***"
            
            with open(self.config_file, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"Config saved to {self.config_file}")
            
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise
    
    def _load_from_file(self) -> Optional[LLMConfig]:
        """
        从文件加载配置
        
        Returns:
            LLMConfig 或 None
        """
        try:
            with open(self.config_file, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data:
                return None
            
            # 如果 API key 被隐藏，从环境变量获取
            if data.get("api_key") == "***masked***":
                provider = data.get("provider", "openai")
                api_key = self._get_api_key_from_env(provider)
                
                # 对于 custom provider，尝试从环境变量获取 DOUBAO_API_KEY
                if provider == "custom" and not api_key:
                    api_key = os.getenv("DOUBAO_API_KEY")
                
                data["api_key"] = api_key
            
            return LLMConfig.from_dict(data)
            
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            return None
    
    def _load_from_env(self) -> Optional[LLMConfig]:
        """
        从环境变量加载配置
        
        Returns:
            LLMConfig 或 None
        """
        # 检测提供商
        provider = "openai"  # 默认
        
        if os.getenv("ANTHROPIC_API_KEY"):
            provider = "anthropic"
        elif os.getenv("OPENAI_API_KEY"):
            provider = "openai"
        elif os.getenv("LOCAL_LLM_URL"):
            provider = "local"
        else:
            return None
        
        config = LLMConfig(provider=provider)
        
        # 加载通用配置
        if os.getenv("LLM_MODEL"):
            config.model = os.getenv("LLM_MODEL")
        
        if os.getenv("LLM_TEMPERATURE"):
            try:
                config.temperature = float(os.getenv("LLM_TEMPERATURE"))
            except ValueError:
                pass
        
        if os.getenv("LLM_MAX_TOKENS"):
            try:
                config.max_tokens = int(os.getenv("LLM_MAX_TOKENS"))
            except ValueError:
                pass
        
        # 加载提供商特定配置
        if provider == "openai":
            config.api_key = os.getenv("OPENAI_API_KEY")
            config.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
            if os.getenv("OPENAI_BASE_URL"):
                config.base_url = os.getenv("OPENAI_BASE_URL")
        
        elif provider == "anthropic":
            config.api_key = os.getenv("ANTHROPIC_API_KEY")
            config.model = os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
            if os.getenv("ANTHROPIC_BASE_URL"):
                config.base_url = os.getenv("ANTHROPIC_BASE_URL")
        
        elif provider == "local":
            config.base_url = os.getenv("LOCAL_LLM_URL", "http://localhost:8000/v1")
            config.model = os.getenv("LOCAL_LLM_MODEL", "local-model")
            config.api_key = os.getenv("LOCAL_LLM_KEY", "not-needed")
        
        elif provider == "azure":
            config.api_key = os.getenv("AZURE_OPENAI_API_KEY")
            config.base_url = os.getenv("AZURE_OPENAI_ENDPOINT")
            config.model = os.getenv("AZURE_OPENAI_MODEL", "gpt-35-turbo")
            config.extra["deployment_name"] = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        
        return config
    
    def _get_api_key_from_env(self, provider: str) -> Optional[str]:
        """
        从环境变量获取 API key
        
        Args:
            provider: 提供商名称
            
        Returns:
            API key 或 None
        """
        env_vars = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "azure": "AZURE_OPENAI_API_KEY",
            "local": "LOCAL_LLM_KEY",
        }
        
        env_var = env_vars.get(provider)
        if env_var:
            return os.getenv(env_var)
        
        return None
    
    def get_provider_config(self) -> Dict[str, Any]:
        """
        获取用于创建 provider 的配置字典
        
        Returns:
            配置字典
        """
        config = self.get_config()
        
        return {
            "api_key": config.api_key,
            "base_url": config.base_url,
            "model": config.model,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "timeout": config.timeout,
            **config.extra
        }


# 全局配置管理器实例
_config_manager: Optional[LLMConfigManager] = None


def get_llm_config_manager() -> LLMConfigManager:
    """获取全局 LLM 配置管理器"""
    global _config_manager
    if _config_manager is None:
        _config_manager = LLMConfigManager()
    return _config_manager


def configure_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
):
    """
    配置 LLM
    
    便捷函数，用于快速配置 LLM
    
    Args:
        provider: 提供商 (openai, anthropic, local, azure)
        model: 模型名称
        api_key: API key
        base_url: 基础 URL
        temperature: 温度
        max_tokens: 最大 token 数
    """
    manager = get_llm_config_manager()
    config = manager.get_config()
    
    if provider:
        config.provider = provider
    if model:
        config.model = model
    if api_key:
        config.api_key = api_key
    if base_url:
        config.base_url = base_url
    if temperature is not None:
        config.temperature = temperature
    if max_tokens is not None:
        config.max_tokens = max_tokens
    
    manager.set_config(config)
    logger.info(f"LLM configured: provider={config.provider}, model={config.model}")


def create_llm_from_config():
    """
    从配置创建 LLM Provider
    
    Returns:
        LLMProvider 实例
    """
    from skill_service.llm.provider import create_llm_provider, LLMProviderType
    
    manager = get_llm_config_manager()
    config = manager.get_config()
    
    provider_type = LLMProviderType(config.provider)
    provider_config = manager.get_provider_config()
    
    return create_llm_provider(provider_type, provider_config)
