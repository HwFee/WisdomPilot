from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator
import re


# =====================================================================
# Pydantic Schema 定义模块
# ---------------------------------------------------------------------
# 本文件定义认证域所有输入/输出数据结构（schema），是 API 契约的核心。
# Schema 不含业务逻辑，只做数据验证和格式转换。
#
# 继承层次：
#   UserBase（公共字段 + 验证）
#     ├─ UserCreate（注册用，增加 password 字段及强度校验）
#     └─ UserResponse（响应用，增加 id/is_active/created_at 等只读字段）
#   UserLogin（登录用，独立类）
#   Token / TokenData（JWT 令牌相关）
#   ForgotPasswordRequest（忘记密码用）
#
# Pydantic v2 关键特性：
#   - field_validator：字段级验证器，在赋值时自动触发
#   - model_validator(mode="before")：模型级验证器，在字段验证前处理原始输入
#   - model_config = {"from_attributes": True}：允许从 ORM 对象属性自动构建
# =====================================================================


class UserBase(BaseModel):
    """带公共字段的用户基础 Schema。

    用户基础 Schema，定义 email 和 username 两个公共字段及验证规则。
    被 UserCreate 和 UserResponse 继承，避免重复定义。
    """
    # EmailStr 类型会自动验证邮箱格式（RFC 标准），无效格式直接报 422 错误
    email: EmailStr
    username: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """规范化邮箱：本地部分统一转小写，防止大小写变体创建重复账户。

        安全审计修复：EmailStr 只小写域名部分，本地部分保留原样。
        攻击者可用 Boss@x.com / boss@x.com 注册两个看似相同的账户，
        造成身份混淆。这里将本地部分统一小写后返回（EmailStr 会再次校验格式）。

        Args:
            v: 待规范化的邮箱字符串。

        Returns:
            本地部分小写化后的邮箱字符串。
        """
        local, _, domain = str(v).partition("@")
        return f"{local.lower()}@{domain}"

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名格式：非空、长度 2-100、仅允许中文/字母/数字/下划线。

        Args:
            v: 待验证的用户名字符串。

        Returns:
            验证通过的用户名字符串。

        Raises:
            ValueError: 用户名不符合任一规则时抛出，Pydantic 会自动转为 422 响应。
        """
        if not v or v.strip() == "":
            raise ValueError("用户名不能为空")
        if len(v) < 2:
            raise ValueError("用户名至少需要2个字符")
        if len(v) > 100:
            raise ValueError("用户名不能超过100个字符")
        # 正则匹配：中文（一-龥覆盖 CJK 基本汉字）、字母、数字、下划线
        if not re.match(r"^[一-龥a-zA-Z0-9_]+$", v):
            raise ValueError("用户名只能包含字母、数字、下划线和中文")
        return v


class UserCreate(UserBase):
    """用户注册请求 Schema。

    用户注册请求 Schema，继承 UserBase 的 email/username，额外增加 password 字段。
    """
    # 明文密码：仅用于注册时校验强度并哈希存储，数据库中永不保存明文
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        验证密码强度。

        要求：
        - 至少 8 个字符
        - 至少包含一个字母（a-z 或 A-Z）
        - 至少包含一个数字（0-9）

        验证密码强度，收集所有不满足的条件后一次性报错（而非遇到第一个就返回），
        让用户能看到全部问题，减少来回尝试。

        Args:
            v: 待验证的密码字符串。

        Returns:
            验证通过的密码字符串。

        Raises:
            ValueError: 密码不符合任一强度要求时抛出。
        """
        # 收集所有错误而非遇到第一个就返回，提升用户体验
        errors = []
        if len(v) < 8:
            errors.append("密码长度至少需要8个字符")
        # 安全审计修复：bcrypt 只取前 72 字节，超长部分被静默丢弃会让用户误以为
        # 长密码生效，且截断多字节字符会破坏字符边界。这里明确拒绝超长密码。
        if len(v.encode("utf-8")) > 72:
            errors.append("密码过长（最多 72 字节，中文约 24 字）")
        # 检查是否包含至少一个字母（大小写均可）
        if not re.search(r"[A-Za-z]", v):
            errors.append("密码需要包含至少一个字母")
        # 检查是否包含至少一个数字
        if not re.search(r"\d", v):
            errors.append("密码需要包含至少一个数字")

        if errors:
            # 将所有错误用分号拼接，一次性返回
            raise ValueError("; ".join(errors))
        return v


class UserLogin(BaseModel):
    """用户登录请求 Schema。

    用户登录请求 Schema，邮箱是唯一登录标识。

    设计说明：
        用户名可重复（不参与登录），登录统一以 email 为凭据，
        因此 schema 只接收 email + password，无需 username。
    """
    email: EmailStr
    password: str
    # remember_me=True 时使用更长的令牌过期时间
    remember_me: bool = False

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """登录邮箱本地部分统一转小写，与注册侧规范化保持一致。"""
        local, _, domain = str(v).partition("@")
        return f"{local.lower()}@{domain}"


class UserResponse(UserBase):
    """用户信息响应 Schema（公开信息）。

    用户信息响应 Schema，用于 API 返回用户公开信息。
    继承 UserBase 的 email/username，额外增加只读字段。
    """
    id: str
    is_active: bool
    is_admin: bool = False
    # 性能审计修复：智核余额随响应返回，DeckHeader 走轻量 /api/auth/me
    # 即可刷新余额，无需每个页面都拉取重量级 /api/dashboard 聚合。
    cores: int = 0
    created_at: datetime
    updated_at: datetime

    # from_attributes=True 允许从 ORM 对象（如 User 模型实例）自动提取属性构建 Schema，
    # 即 UserResponse.model_validate(user_orm_instance) 可直接转换。
    model_config = {"from_attributes": True}


class Token(BaseModel):
    """JWT 令牌响应 Schema。

    JWT 令牌响应 Schema，登录/注册成功后返回。
    包含访问令牌字符串和用户信息，前端保存 token 用于后续请求的 Authorization 头。
    """
    access_token: str
    # token_type 固定为 "bearer"，对应 HTTP Authorization: Bearer <token> 格式
    token_type: str = "bearer"
    # 同时返回用户信息，前端无需额外请求 /me 接口
    user: UserResponse


class TokenData(BaseModel):
    """JWT 解码后的数据 Schema。

    JWT 解码后的数据 Schema，用于在依赖注入中提取用户标识。
    """
    user_id: str | None = None
    email: str | None = None


class ForgotPasswordRequest(BaseModel):
    """忘记密码请求 Schema。

    忘记密码请求 Schema，只需提供邮箱地址。
    """
    email: EmailStr
