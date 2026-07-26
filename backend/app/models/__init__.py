"""Models package - 数据模型

训练舱重构后仅保留认证所需的 User；领域模型全部位于 app.deck.models。
"""

from app.models.user import User

__all__ = ["User"]
