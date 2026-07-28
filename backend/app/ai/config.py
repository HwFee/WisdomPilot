"""AI provider configuration."""

from pydantic import BaseModel
from typing import Optional


class AIProviderConfig(BaseModel):
    """AI 提供商配置"""

    provider: str = "deepseek"
    api_key: str = ""
    model: str = "deepseek-v4-flash"
    temperature: float = 0.7
    base_url: Optional[str] = None
    local_base_url: Optional[str] = None  # 本地服务地址（自动检测）
    is_local_first: bool = False  # 本地优先模式
