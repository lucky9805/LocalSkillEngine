"""
API 数据模型定义 (Pydantic Schemas)
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class SkillStatus(str, Enum):
    """Skill 状态枚举"""
    ENABLED = "enabled"
    DISABLED = "disabled"
    LOADING = "loading"
    ERROR = "error"


class SkillInfo(BaseModel):
    """Skill 信息摘要"""
    name: str = Field(..., description="Skill 名称")
    version: str = Field(..., description="版本号")
    category: str = Field(..., description="分类")
    description: str = Field(..., description="描述")
    author: str = Field(..., description="作者")
    enabled: bool = Field(..., description="是否启用")
    status: SkillStatus = Field(..., description="状态")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "greeting",
                "version": "1.0.0",
                "category": "utility",
                "description": "打招呼技能",
                "author": "Your Name",
                "enabled": True,
                "status": "enabled"
            }
        }


class SkillDetail(BaseModel):
    """Skill 详细信息"""
    name: str
    version: str
    author: str
    category: str
    description: str
    instructions: str
    tools: List[str] = []
    scripts: Dict[str, str] = {}
    enabled: bool
    path: str
    created_at: datetime
    updated_at: datetime
    status: SkillStatus


class SkillExecutionRequest(BaseModel):
    """Skill 执行请求"""
    parameters: Dict[str, Any] = Field(default_factory=dict, description="执行参数")
    timeout: Optional[int] = Field(None, description="超时时间（秒）")

    class Config:
        json_schema_extra = {
            "example": {
                "parameters": {"name": "World"},
                "timeout": 30
            }
        }


class SkillExecutionResult(BaseModel):
    """Skill 执行结果"""
    success: bool = Field(..., description="是否成功")
    skill_name: str = Field(..., description="Skill 名称")
    result: Any = Field(None, description="执行结果")
    execution_time: float = Field(..., description="执行时间（秒）")
    logs: List[str] = Field(default_factory=list, description="执行日志")
    error: Optional[str] = Field(None, description="错误信息")
    timestamp: datetime = Field(default_factory=datetime.now, description="执行时间")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "skill_name": "greeting",
                "result": "Hello, World!",
                "execution_time": 0.123,
                "logs": ["Executing skill greeting..."],
                "error": None,
                "timestamp": "2024-01-01T00:00:00"
            }
        }


class SkillListResponse(BaseModel):
    """Skill 列表响应"""
    skills: List[SkillInfo] = Field(..., description="Skill 列表")
    total: int = Field(..., description="总数")


class SkillInstallRequest(BaseModel):
    """Skill 安装请求"""
    path: str = Field(..., description="Skill 路径")
    enabled: bool = Field(True, description="是否启用")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="版本号")
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="详细描述")


class ImportFromDirectoryRequest(BaseModel):
    """从目录导入 skill 请求"""
    source_dir: str = Field(..., description="源目录路径")
    skill_name: Optional[str] = Field(None, description="目标 skill 名称")
    overwrite: bool = Field(False, description="是否覆盖已存在的 skill")


class ImportFromGitRequest(BaseModel):
    """从 Git 导入 skill 请求"""
    git_url: str = Field(..., description="Git 仓库地址")
    skill_name: Optional[str] = Field(None, description="目标 skill 名称")
    subdir: Optional[str] = Field(None, description="仓库中的子目录")
    overwrite: bool = Field(False, description="是否覆盖已存在的 skill")


class ImportResponse(BaseModel):
    """导入响应"""
    success: bool = Field(..., description="是否成功")
    skill_name: Optional[str] = Field(None, description="skill 名称")
    target_path: Optional[str] = Field(None, description="目标路径")
    message: str = Field(..., description="结果消息")
    warnings: List[str] = Field(default_factory=list, description="警告信息")
    errors: List[str] = Field(default_factory=list, description="错误信息")


class ChatRequest(BaseModel):
    """智能对话请求"""
    user_input: str = Field(..., description="用户输入的自然语言描述")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_input": "计算 123 加 456"
            }
        }


class SkillSelection(BaseModel):
    """Skill 选择结果"""
    skill_name: Optional[str] = Field(None, description="选择的 skill 名称")
    confidence: float = Field(..., description="置信度 (0-1)")
    reasoning: str = Field(..., description="选择理由")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="提取的参数")
    direct_response: Optional[str] = Field(None, description="直接回复（当没有匹配 skill 时）")


class ChatExecutionResult(BaseModel):
    """对话执行结果"""
    success: bool = Field(..., description="是否成功")
    result: Any = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")
    execution_time: float = Field(..., description="执行时间（秒）")
    logs: List[str] = Field(default_factory=list, description="执行日志")


class ChatResponse(BaseModel):
    """智能对话响应"""
    success: bool = Field(..., description="是否成功")
    user_input: str = Field(..., description="用户输入")
    selection: SkillSelection = Field(..., description="Skill 选择信息")
    execution: Optional[ChatExecutionResult] = Field(None, description="执行结果（如果选择了 skill）")
    error: Optional[str] = Field(None, description="错误信息")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")
