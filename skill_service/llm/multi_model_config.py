"""
多模型配置管理

支持在一个配置文件中管理多个模型，并快速切换
支持从以下位置读取配置（按优先级）：
1. 项目目录下的 .env 文件
2. ~/.skill-service/models-config.yaml
"""
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from skill_service.utils.logger import get_logger
from skill_service.llm.config import LLMConfig, create_llm_from_config

logger = get_logger(__name__)


@dataclass
class ModelProfile:
    """模型配置文件"""
    name: str
    provider: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 60
    description: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "ModelProfile":
        """从字典创建模型配置"""
        return cls(
            name=name,
            provider=data.get("provider", "openai"),
            model=data.get("model", "gpt-3.5-turbo"),
            api_key=data.get("api_key"),
            base_url=data.get("base_url"),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 2000),
            timeout=data.get("timeout", 60),
            description=data.get("description"),
            extra=data.get("extra", {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = {
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "extra": self.extra
        }
        if self.api_key:
            data["api_key"] = self.api_key
        if self.base_url:
            data["base_url"] = self.base_url
        if self.description:
            data["description"] = self.description
        return data
    
    def to_llm_config(self) -> LLMConfig:
        """转换为 LLMConfig"""
        return LLMConfig(
            provider=self.provider,
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout,
            extra=self.extra
        )


class MultiModelConfigManager:
    """
    多模型配置管理器
    
    支持：
    1. 在一个配置文件中管理多个模型
    2. 快速切换当前使用的模型
    3. 从环境变量读取 API keys
    4. 从项目目录的 .env 文件读取配置
    """
    
    # 环境变量前缀
    ENV_PREFIX = "SKILL_SERVICE_LLM_"
    
    def __init__(self):
        """初始化多模型配置管理器"""
        self.config_file = Path.home() / ".skill-service" / "models-config.yaml"
        self._profiles: Dict[str, ModelProfile] = {}
        self._current_profile: Optional[str] = None
        
        # 首先尝试从 .env 文件加载
        if not self._load_from_dotenv():
            # 如果 .env 没有配置，从 yaml 文件加载
            self._load_from_file()
    
    def _find_dotenv_file(self) -> Optional[Path]:
        """
        查找项目目录下的 .env 文件
        
        搜索顺序：
        1. 当前工作目录
        2. 项目根目录（向上查找包含 .git 或 pyproject.toml 的目录）
        
        Returns:
            .env 文件路径，未找到返回 None
        """
        # 首先检查当前目录
        cwd = Path.cwd()
        dotenv_file = cwd / ".env"
        if dotenv_file.exists():
            return dotenv_file
        
        # 向上查找项目根目录
        current = cwd
        while current != current.parent:
            # 检查项目标记文件
            if (current / ".git").exists() or (current / "pyproject.toml").exists() or (current / "setup.py").exists():
                dotenv_file = current / ".env"
                if dotenv_file.exists():
                    return dotenv_file
                break
            current = current.parent
        
        return None
    
    def _parse_dotenv(self, dotenv_path: Path) -> Dict[str, str]:
        """
        解析 .env 文件
        
        Args:
            dotenv_path: .env 文件路径
            
        Returns:
            环境变量字典
        """
        env_vars = {}
        try:
            with open(dotenv_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # 跳过空行和注释
                    if not line or line.startswith('#'):
                        continue
                    # 解析 KEY=VALUE
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # 移除引号
                        if (value.startswith('"') and value.endswith('"')) or \
                           (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]
                        env_vars[key] = value
        except Exception as e:
            logger.warning(f"解析 .env 文件失败: {e}")
        
        return env_vars
    
    def _load_from_dotenv(self) -> bool:
        """
        从 .env 文件加载模型配置
        
        支持的格式：
        SKILL_SERVICE_LLM_CURRENT=doubao-seed
        SKILL_SERVICE_LLM_DOUBAO_SEED_PROVIDER=custom
        SKILL_SERVICE_LLM_DOUBAO_SEED_MODEL=ep-xxx
        SKILL_SERVICE_LLM_DOUBAO_SEED_API_KEY=xxx
        SKILL_SERVICE_LLM_DOUBAO_SEED_BASE_URL=https://...
        
        Returns:
            是否成功加载配置
        """
        dotenv_path = self._find_dotenv_file()
        if not dotenv_path:
            return False
        
        try:
            env_vars = self._parse_dotenv(dotenv_path)
            
            # 查找以 SKILL_SERVICE_LLM_ 开头的变量
            prefix = self.ENV_PREFIX
            model_configs: Dict[str, Dict[str, Any]] = {}
            
            # 定义已知的属性名（用于从后往前解析）
            known_properties = [
                "PROVIDER", "MODEL", "API_KEY", "BASE_URL",
                "TEMPERATURE", "MAX_TOKENS", "TIMEOUT", "DESCRIPTION"
            ]
            
            for key, value in env_vars.items():
                if not key.startswith(prefix):
                    continue
                
                # 移除前缀
                rest = key[len(prefix):]
                
                # 检查是否是 CURRENT 设置
                if rest == "CURRENT":
                    self._current_profile = value.lower()
                    continue
                
                # 从后往前解析：找到最后一个已知属性
                property_name = None
                model_name = None
                
                for prop in known_properties:
                    if rest.endswith(f"_{prop}"):
                        property_name = prop.lower()
                        model_name = rest[:-len(prop)-1].lower()
                        break
                
                if not property_name or not model_name:
                    continue
                
                if model_name not in model_configs:
                    model_configs[model_name] = {}
                
                # 转换属性值
                if property_name == "temperature":
                    model_configs[model_name][property_name] = float(value)
                elif property_name == "max_tokens" or property_name == "timeout":
                    model_configs[model_name][property_name] = int(value)
                else:
                    model_configs[model_name][property_name] = value
            
            # 创建 ModelProfile 对象
            for name, config in model_configs.items():
                # 设置默认值
                if "provider" not in config:
                    config["provider"] = "openai"
                if "model" not in config:
                    config["model"] = "gpt-3.5-turbo"
                
                self._profiles[name] = ModelProfile.from_dict(name, config)
            
            if self._profiles:
                logger.info(f"Loaded {len(self._profiles)} model profiles from {dotenv_path}")
                
                # 如果没有设置当前模型，使用第一个
                if not self._current_profile and self._profiles:
                    self._current_profile = next(iter(self._profiles.keys()))
                
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"从 .env 加载配置失败: {e}")
            return False
    
    def _load_from_file(self):
        """从 YAML 文件加载配置"""
        if not self.config_file.exists():
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                return
            
            # 加载当前配置
            self._current_profile = data.get("current")
            
            # 加载所有模型配置
            profiles_data = data.get("profiles", {})
            for name, profile_data in profiles_data.items():
                # 从环境变量获取 API key（如果配置中是占位符或未设置）
                profile_data = self._resolve_api_key_from_env(name, profile_data)
                self._profiles[name] = ModelProfile.from_dict(name, profile_data)
            
            logger.info(f"Loaded {len(self._profiles)} model profiles from {self.config_file}")
            
        except Exception as e:
            logger.error(f"Error loading models config: {e}")
    
    def _resolve_api_key_from_env(self, name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """从环境变量解析 API key"""
        api_key = data.get("api_key")
        
        # 如果 api_key 是 ${ENV_VAR} 格式，从环境变量获取
        if api_key and isinstance(api_key, str) and api_key.startswith("${") and api_key.endswith("}"):
            env_var = api_key[2:-1]  # 去掉 ${ 和 }
            data["api_key"] = os.getenv(env_var)
        
        # 如果 api_key 未设置或为空，尝试根据 provider 推断环境变量名
        if not api_key or api_key == "***masked***":
            provider = data.get("provider", "openai")
            env_var_map = {
                "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
                "azure": "AZURE_OPENAI_API_KEY",
                "doubao": "DOUBAO_API_KEY",
                "custom": ["DOUBAO_API_KEY", f"{name.upper().replace('-', '_')}_API_KEY"]  # 尝试多个环境变量名
            }
            
            env_vars = env_var_map.get(provider)
            if env_vars:
                # 统一处理为列表
                if isinstance(env_vars, str):
                    env_vars = [env_vars]
                
                # 依次尝试每个环境变量
                for env_var in env_vars:
                    api_key = os.getenv(env_var)
                    if api_key:
                        data["api_key"] = api_key
                        break
        
        return data
    
    def save_to_file(self):
        """保存配置到文件"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 准备保存的数据
            profiles_data = {}
            for name, profile in self._profiles.items():
                data = profile.to_dict()
                # 如果 API key 是环境变量格式，保持原样；否则隐藏
                api_key = data.get("api_key")
                if api_key and not (isinstance(api_key, str) and api_key.startswith("${") and api_key.endswith("}")):
                    data["api_key"] = "***masked***"
                profiles_data[name] = data
            
            data = {
                "current": self._current_profile,
                "profiles": profiles_data
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"Models config saved to {self.config_file}")
            
        except Exception as e:
            logger.error(f"Failed to save models config: {e}")
            raise
    
    def add_profile(self, name: str, profile: ModelProfile, set_current: bool = False):
        """
        添加模型配置
        
        Args:
            name: 配置名称
            profile: 模型配置
            set_current: 是否设为当前配置
        """
        profile.name = name
        self._profiles[name] = profile
        
        if set_current or self._current_profile is None:
            self._current_profile = name
        
        logger.info(f"Added model profile: {name}")
    
    def remove_profile(self, name: str) -> bool:
        """
        移除模型配置
        
        Args:
            name: 配置名称
            
        Returns:
            是否成功移除
        """
        if name not in self._profiles:
            return False
        
        del self._profiles[name]
        
        # 如果移除的是当前配置，重置当前配置
        if self._current_profile == name:
            self._current_profile = next(iter(self._profiles.keys()), None)
        
        logger.info(f"Removed model profile: {name}")
        return True
    
    def set_current(self, name: str) -> bool:
        """
        设置当前使用的模型
        
        Args:
            name: 配置名称
            
        Returns:
            是否设置成功
        """
        if name not in self._profiles:
            logger.error(f"Model profile not found: {name}")
            return False
        
        self._current_profile = name
        logger.info(f"Current model set to: {name}")
        return True
    
    def get_current_profile(self) -> Optional[ModelProfile]:
        """获取当前模型配置"""
        # 重新加载以确保环境变量被正确读取
        self._reload_env_vars()
        
        if self._current_profile and self._current_profile in self._profiles:
            return self._profiles[self._current_profile]
        
        # 如果没有当前配置，返回第一个
        if self._profiles:
            return next(iter(self._profiles.values()))
        
        return None
    
    def _reload_env_vars(self):
        """重新从环境变量加载 API keys"""
        for name, profile in self._profiles.items():
            # 构建包含当前 api_key 的数据字典
            data = {
                "provider": profile.provider,
                "api_key": profile.api_key,
                "base_url": profile.base_url
            }
            # 重新解析 API key
            data = self._resolve_api_key_from_env(name, data)
            # 只有当解析到了新的 api_key 时才更新
            if data.get("api_key"):
                profile.api_key = data.get("api_key")
    
    def get_profile(self, name: str) -> Optional[ModelProfile]:
        """获取指定模型配置"""
        self._reload_env_vars()
        return self._profiles.get(name)
    
    def list_profiles(self) -> List[ModelProfile]:
        """列出所有模型配置"""
        self._reload_env_vars()
        return list(self._profiles.values())
    
    def get_current_name(self) -> Optional[str]:
        """获取当前配置名称"""
        return self._current_profile
    
    def create_llm_provider(self, profile_name: Optional[str] = None):
        """
        创建 LLM Provider
        
        Args:
            profile_name: 配置名称，None 表示使用当前配置
            
        Returns:
            LLMProvider 实例
        """
        from skill_service.llm.provider import create_llm_provider, LLMProviderType
        
        if profile_name:
            profile = self.get_profile(profile_name)
        else:
            profile = self.get_current_profile()
        
        if not profile:
            raise ValueError("No model profile available")
        
        llm_config = profile.to_llm_config()
        provider_type = LLMProviderType(llm_config.provider)
        
        provider_config = {
            "api_key": llm_config.api_key,
            "base_url": llm_config.base_url,
            "model": llm_config.model,
            "temperature": llm_config.temperature,
            "max_tokens": llm_config.max_tokens,
            "timeout": llm_config.timeout,
            "provider_type": llm_config.provider,
            **llm_config.extra
        }
        
        return create_llm_provider(provider_type, provider_config)


# 全局多模型配置管理器实例
_multi_model_manager: Optional[MultiModelConfigManager] = None


def get_multi_model_manager() -> MultiModelConfigManager:
    """获取全局多模型配置管理器"""
    global _multi_model_manager
    if _multi_model_manager is None:
        _multi_model_manager = MultiModelConfigManager()
    else:
        # 重新加载环境变量以确保 API key 是最新的
        _multi_model_manager._reload_env_vars()
    return _multi_model_manager


def switch_model(name: str) -> bool:
    """
    切换到指定模型
    
    Args:
        name: 模型配置名称
        
    Returns:
        是否切换成功
    """
    manager = get_multi_model_manager()
    if manager.set_current(name):
        manager.save_to_file()
        return True
    return False


def get_current_model_info() -> Optional[Dict[str, Any]]:
    """获取当前模型信息"""
    manager = get_multi_model_manager()
    profile = manager.get_current_profile()
    
    if not profile:
        return None
    
    return {
        "name": profile.name,
        "provider": profile.provider,
        "model": profile.model,
        "description": profile.description,
        "temperature": profile.temperature,
        "max_tokens": profile.max_tokens
    }
