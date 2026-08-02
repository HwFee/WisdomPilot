# =====================================================================
# 用户数据模型模块（SQLAlchemy ORM）
# ---------------------------------------------------------------------
# 本文件定义认证域唯一的数据库模型 —— User 表。
# 在训练舱重构后，User 表只保留认证相关字段和智核（cores）余额，
# 不再冗余任何领域数据（掌握度、训练记录等都在 app.training.models 中）。
#
# 技术栈：SQLAlchemy 2.0 风格声明式映射（Mapped + mapped_column）
# =====================================================================

import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base  # Base 是所有 ORM 模型的声明式基类
from app.utils.time import utc_now  # 统一的 UTC 时间获取函数，避免各处自行取时间


class User(Base):
    """认证与用户模型。

    训练舱重构后仅保留认证所需字段与智核余额；领域数据（掌握度、训练记录、
    智核流水等）全部落在 app.training.models 的事件/账本表中，不在 User 上冗余。

    关键属性：
        id: 用户唯一标识，UUID v4 字符串（36 字符），由 Python 端生成而非数据库自增。
        email: 用户邮箱，唯一索引，用于登录和通知。
        username: 用户名，唯一索引，支持中文/字母/数字/下划线。
        hashed_password: 经 bcrypt 哈希后的密码密文，永不存储明文。
        is_active: 账户是否激活，False 时登录被拒绝（但返回403而非401）。
        is_admin: 是否管理员，当前训练舱版本未使用管理员功能，保留字段供未来扩展。
        cores: 智核余额（平台虚拟货币），初始 100，实际流水记录在 DeckCoreTransaction 表。
        created_at / updated_at: 审计时间戳，均使用 UTC。

    设计意图：
        - User 表保持精简，遵循"单一职责"——只管认证和基础账户信息
        - cores 字段是缓存读模型，真正的账本是 DeckCoreTransaction（事件源模式）
    """

    # __tablename__ 指定数据库中的表名
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        # 主键使用 UUID 字符串而非自增整数：
        # 1) UUID 全局唯一，便于未来分布式/分库分表
        # 2) 不暴露用户数量（自增 ID 可被猜测）
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(
        # 邮箱字段：唯一约束 + 索引（登录时按邮箱查询，需要快速定位）
        String(255), unique=True, index=True, nullable=False
    )
    username: Mapped[str] = mapped_column(
        # 用户名字段：可重复（2026-08 起登录统一走邮箱，用户名仅作展示昵称）
        String(100), index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(
        # 密码密文：只存哈希值，不存明文。bcrypt 输出固定 60 字符，255 足够
        String(255), nullable=False
    )
    is_active: Mapped[str] = mapped_column(
        # 账户激活状态：默认 True。管理员可设为 False 停用账户
        Boolean, default=True, nullable=False
    )
    is_admin: Mapped[str] = mapped_column(
        # 管理员标志：默认 False。当前版本未启用管理后台，字段预留
        Boolean, default=False, nullable=False
    )
    cores: Mapped[int] = mapped_column(
        # 智核余额：平台虚拟货币，新用户默认 100 智核。
        # 注意：此字段是缓存读模型，真正的变动流水记录在 DeckCoreTransaction 表，
        # 修改智核时应通过事件追加方式，而非直接 UPDATE 此字段。
        Integer,
        default=100,
        nullable=False,
        comment="Core (智核) balance - platform currency; ledger in DeckCoreTransaction",
    )
    created_at: Mapped[datetime] = mapped_column(
        # 创建时间：使用 utc_now() 保证全局统一 UTC 时间，避免服务器时区差异
        DateTime, default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        # 更新时间：创建时同 created_at，每次 UPDATE 时自动刷新（onupdate=utc_now）
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )

    def __repr__(self) -> str:
        """调试用的字符串表示，方便在日志/REPL 中识别用户对象。"""
        return f"<User {self.email}>"
