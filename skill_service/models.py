"""
数据模型定义 - 符合 Agent Skills 规范
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class SkillStatus(str, Enum):
    """Skill 状态枚举"""
    ENABLED = "enabled"
    DISABLED = "disabled"
    LOADING = "loading"
    ERROR = "error"


@dataclass
class Skill:
    """
    Skill 数据模型 - 符合 Agent Skills 规范
    
    标准字段 (Agent Skills Spec):
    - name: skill 名称 (必需)
    - description: 描述和使用场景 (必需)
    - license: 许可证 (可选)
    - compatibility: 环境要求 (可选)
    - allowed_tools: 允许使用的工具 (可选)
    - metadata: 额外元数据 (可选)
    
    内部字段:
    - instructions: SKILL.md body 内容
    - scripts/references/assets: 资源文件路径
    """
    # Agent Skills 标准字段
    name: str
    description: str
    license: Optional[str] = None
    compatibility: Optional[str] = None
    allowed_tools: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)
    
    # 内部管理字段
    instructions: str = ""  # SKILL.md body (frontmatter 之后的内容)
    scripts: Dict[str, str] = field(default_factory=dict)
    references: Dict[str, str] = field(default_factory=dict)
    assets: Dict[str, str] = field(default_factory=dict)
    
    # 运行时字段
    enabled: bool = True
    path: str = ""  # SKILL.md 文件的绝对路径
    _skill_dir: str = ""  # skill 目录的绝对路径 (内部使用)
    
    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def status(self) -> SkillStatus:
        """获取 skill 状态"""
        if not self.enabled:
            return SkillStatus.DISABLED
        return SkillStatus.ENABLED
    
    @property
    def skill_dir(self) -> str:
        """获取 skill 目录路径"""
        if self._skill_dir:
            return self._skill_dir
        if self.path:
            from pathlib import Path
            return str(Path(self.path).parent)
        return ""
    
    @skill_dir.setter
    def skill_dir(self, value: str):
        """设置 skill 目录路径"""
        self._skill_dir = value
    
    # 向后兼容属性
    @property
    def version(self) -> str:
        """从 metadata 获取版本 (向后兼容)"""
        return self.metadata.get("version", "1.0.0")
    
    @property
    def author(self) -> str:
        """从 metadata 获取作者 (向后兼容)"""
        return self.metadata.get("author", "Unknown")
    
    @property
    def category(self) -> str:
        """从 metadata 获取分类 (向后兼容)"""
        return self.metadata.get("category", "uncategorized")
    
    @property
    def tools(self) -> List[str]:
        """从 allowed_tools 解析工具列表 (向后兼容)"""
        if self.allowed_tools:
            return [t.strip() for t in self.allowed_tools.split()]
        return []


@dataclass
class SkillExecutionRequest:
    """Skill 执行请求"""
    skill_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout: Optional[int] = None
    model: Optional[str] = None  # 指定使用的模型，None 表示使用系统默认模型


@dataclass
class SkillExecutionResult:
    """Skill 执行结果"""
    success: bool
    skill_name: str
    result: Any
    execution_time: float
    logs: List[str] = field(default_factory=list)
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SkillInfo:
    """
    Skill 信息摘要 - Tier 1: Catalog
    
    只包含 name 和 description，用于模型判断何时使用 skill。
    这是渐进式披露的第一级，token 成本最低 (~50-100 tokens per skill)。
    """
    name: str
    description: str
    # 可选：包含 location 用于文件读取激活
    location: Optional[str] = None
    # 向后兼容字段
    enabled: bool = True
    status: SkillStatus = SkillStatus.ENABLED
    
    # 这些字段从 metadata 获取，用于向后兼容
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def category(self) -> str:
        return "uncategorized"
    
    @property
    def author(self) -> str:
        return "Unknown"


@dataclass
class SkillInstallRequest:
    """Skill 安装请求"""
    path: str
    enabled: bool = True
