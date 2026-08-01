from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
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

    用户登录请求 Schema，支持用户名或邮箱登录。

    设计说明：
        username 字段同时接受用户名和邮箱，通过 model_validator 自动将邮箱
        填入 username，使 service 层只需查询一个字段。
    """
    username: str
    # email 为可选字段，前端可只传 email 不传 username
    email: EmailStr | None = None
    password: str
    # remember_me=True 时使用更长的令牌过期时间
    remember_me: bool = False

    @model_validator(mode="before")
    @classmethod
    def set_login_identifier(cls, values):
        """模型级前置验证器：如果只传了 email 没传 username，自动将 email 赋给 username。

        mode="before" 表示在字段类型验证之前执行，处理的是原始输入字典。
        这样 service 层只需按 username 查询，无需同时处理 email 和 username 两个字段。

        Args:
            values: 原始输入数据（通常是 dict）。

        Returns:
            处理后的输入数据（确保 username 字段有值）。
        """
        if not isinstance(values, dict):
            # 非 dict 输入（如已实例化的对象）直接返回，交给后续验证
            return values
        # 如果已有 username 或没有 email，无需处理
        if values.get("username") or not values.get("email"):
            return values
        # 将 email 复制到 username 字段，统一登录标识符
        normalized_values = values.copy()
        normalized_values["username"] = normalized_values["email"]
        return normalized_values


class UserResponse(UserBase):
    """用户信息响应 Schema（公开信息）。

    用户信息响应 Schema，用于 API 返回用户公开信息。
    继承 UserBase 的 email/username，额外增加只读字段。
    """
    id: str
    is_active: bool
    is_admin: bool = False
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
