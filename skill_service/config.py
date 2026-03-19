"""
配置管理模块
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    # Server Configuration
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    debug: bool = False

    # Skill Storage
    skills_directory: str = "./skills"
    cache_directory: str = "./.cache"

    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/skill_service.log"

    # API Configuration
    api_prefix: str = "/api/v1"
    max_execution_time: int = 300

    # Security
    api_key: str = "your-secret-api-key-change-this"
    enable_auth: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # 忽略未定义的环境变量
    )

    @property
    def api_docs_url(self) -> str:
        """API 文档 URL"""
        return "/docs"

    @property
    def api_redoc_url(self) -> str:
        """ReDoc URL"""
        return "/redoc"


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings
