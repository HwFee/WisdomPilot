from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.auth.models import User
from app.auth.schemas import UserCreate, UserLogin, Token, UserResponse
from app.auth.security import (
    get_password_hash,
    verify_password,
    create_access_token,
)
from app.config import get_settings
from app.auth.errors import (
    EmailAlreadyRegisteredError,
    InactiveAccountError,
    InvalidCredentialsError,
    UsernameAlreadyRegisteredError,
)

# =====================================================================
# 认证服务层模块
# ---------------------------------------------------------------------
# 本文件实现认证域的核心业务逻辑：注册、登录、查询用户、忘记密码。
#
# 分层架构说明：
#   - router 层：接收 HTTP 请求，调用 service，将领域异常转为 HTTP 响应
#   - service 层（本文件）：业务逻辑，操作数据库，抛出领域异常
#   - security 层：密码哈希、JWT 编解码等纯函数
#   - models 层：ORM 模型定义
#
# AuthService 通过构造函数注入 AsyncSession（依赖注入），
# 使其可在不同请求中复用，且便于单元测试时 mock 数据库。
# =====================================================================

# 在模块加载时读取配置（单例模式，settings 全局共享）
settings = get_settings()


class AuthService:
    """认证服务类：处理用户注册与登录。

    认证服务类，封装注册、登录等业务逻辑。

    设计意图：
        - 通过构造函数注入 AsyncSession，实现数据库会话与业务逻辑解耦
        - 所有方法都是 async，配合 SQLAlchemy 2.0 异步引擎
        - 抛出领域异常（AuthError 子类）而非 HTTPException，保持服务层纯净

    关键属性：
        db: 异步数据库会话（AsyncSession），由 router 层通过 Depends(get_db) 注入
    """

    def __init__(self, db: AsyncSession):
        """初始化认证服务。

        Args:
            db: 异步数据库会话，用于执行所有数据库操作。
        """
        self.db = db

    async def register(self, user_data: UserCreate) -> tuple[User, Token]:
        """注册新用户，返回用户对象和 JWT 令牌。

        注册新用户并返回用户对象和 JWT 令牌。

        业务流程：
            1. 检查邮箱和用户名是否已被注册
            2. 对密码进行 bcrypt 哈希
            3. 创建用户记录并写入数据库
            4. 生成 JWT 访问令牌
            5. 返回用户对象和令牌

        Args:
            user_data: 注册请求数据（email, username, password），已通过 Pydantic 验证。

        Returns:
            元组 (User, Token)：User 是 ORM 对象，Token 包含 JWT 字符串和用户信息。

        Raises:
            EmailAlreadyRegisteredError: 邮箱已存在。
            UsernameAlreadyRegisteredError: 用户名已存在。
        """
        # 检查邮箱或用户名是否已存在（一条查询同时检查两个字段，避免两次数据库往返）
        result = await self.db.execute(
            select(User).where(
                or_(User.email == user_data.email, User.username == user_data.username)
            )
        )
        existing_user = result.scalars().first()

        if existing_user:
            # 根据冲突的字段抛出不同的异常，让用户知道具体是哪个重复了
            if existing_user.email == user_data.email:
                raise EmailAlreadyRegisteredError
            raise UsernameAlreadyRegisteredError

        # 对明文密码进行 bcrypt 哈希，永不存储明文
        hashed_password = get_password_hash(user_data.password)
        # 创建 User ORM 对象（id 和时间戳由模型默认值自动生成）
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
        )

        # add 将对象加入会话，flush 写入数据库（生成 ID 但不提交事务）
        # flush 与 commit 的区别：flush 发送 SQL 但不结束事务，commit 才真正持久化
        self.db.add(new_user)
        await self.db.flush()
        # refresh 从数据库重新加载对象，获取默认值生成的字段（如 id, created_at）
        await self.db.refresh(new_user)

        # 生成 JWT 令牌，载荷中包含用户 ID（sub）和邮箱（email）
        access_token = create_access_token(
            data={"sub": new_user.id, "email": new_user.email},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        # 将 ORM 对象转换为响应 Schema（model_validate 利用 from_attributes 配置）
        user_response = UserResponse.model_validate(new_user)
        token = Token(access_token=access_token, user=user_response)

        return new_user, token

    async def login(self, login_data: UserLogin) -> tuple[User, Token]:
        """验证用户身份，返回用户对象和 JWT 令牌。

        用户登录，验证凭据后返回 JWT 令牌。

        业务流程：
            1. 按用户名或邮箱查询用户
            2. 验证密码哈希是否匹配
            3. 检查账户是否激活
            4. 根据 remember_me 选择过期时间，生成 JWT 令牌

        Args:
            login_data: 登录请求数据（username/email, password, remember_me）。

        Returns:
            元组 (User, Token)：User 是 ORM 对象，Token 包含 JWT 字符串和用户信息。

        Raises:
            InvalidCredentialsError: 用户不存在或密码错误（不区分两者，防枚举攻击）。
            InactiveAccountError: 账户已被停用。
        """
        # 同时按邮箱和用户名查询，因为 login_data.username 可能是其中任一个
        result = await self.db.execute(
            select(User).where(
                or_(User.email == login_data.username, User.username == login_data.username)
            )
        )
        # scalar_one_or_none()：期望返回 0 或 1 条记录，多于 1 条会抛异常（数据完整性保护）
        user = result.scalar_one_or_none()

        # 安全要点：用户不存在和密码错误返回相同异常，防止攻击者通过响应差异枚举有效用户名
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise InvalidCredentialsError

        # 密码正确但账户停用，返回不同的异常（403 而非 401）
        if not user.is_active:
            raise InactiveAccountError

        # "记住我"模式：使用更长的令牌过期时间，减少用户重复登录频率
        if login_data.remember_me:
            expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES_REMEMBER)
        else:
            expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        # 生成 JWT 令牌，载荷中包含用户 ID（sub）和邮箱（email）
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email},
            expires_delta=expires_delta,
        )

        # 将 ORM 对象转换为响应 Schema（model_validate 利用 from_attributes 配置）
        user_response = UserResponse.model_validate(user)
        token = Token(access_token=access_token, user=user_response)

        return user, token

    async def get_user_by_id(self, user_id: str) -> User | None:
        """按用户 ID 查询用户。

        按用户 ID 查询用户。

        Args:
            user_id: 用户唯一标识（UUID 字符串）。

        Returns:
            User 对象，不存在则返回 None。
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def forgot_password(self, email: str) -> None:
        """查询重置收件人，但不暴露其是否存在。

        忘记密码处理：查询邮箱是否存在但不暴露查询结果。

        安全设计：
            无论邮箱是否存在都返回成功，防止攻击者通过 API 响应枚举已注册邮箱。
            当前邮件发送功能尚未实现，此方法仅做查询占位。

        Args:
            email: 用户提供的邮箱地址。
        """
        # 执行查询但不使用结果，仅模拟"查找用户"行为
        await self.db.execute(select(User.id).where(User.email == email))
        # Password-reset delivery is not configured in this application yet.
        return None
