# =====================================================================
# 认证安全工具模块（密码哈希 + JWT 令牌）
# ---------------------------------------------------------------------
# 本文件封装认证域底层安全原语，不依赖数据库和业务逻辑，可独立测试：
#   1. 密码哈希与验证（bcrypt via passlib）
#   2. JWT 访问令牌的创建与解码（python-jose）
#
# 设计意图：
#   - 将安全细节集中在一处，便于审计和升级（如更换哈希算法或 JWT 库）
#   - service 层和 dependencies 层通过此模块间接使用密码学功能
# =====================================================================

from datetime import timedelta
from typing import Any
from uuid import uuid4
from jose import jwt, JWTError  # python-jose：JWT 编解码库
from passlib.context import CryptContext  # passlib：密码哈希统一接口
from app.config import get_settings  # 全局配置（密钥、算法、过期时间等）
from app.utils.time import utc_now  # 统一 UTC 时间

# 创建 bcrypt 哈希上下文。
# - schemes=["bcrypt"]：指定使用 bcrypt 算法（业界标准，抗暴力破解）
# - deprecated="auto"：旧算法哈希自动标记为已弃用，验证时提示升级
# - bcrypt__rounds=12：哈希迭代轮数，数值越大越安全但越慢；12 是当前推荐值
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

# 安全审计修复（登录时序侧信道）：用户不存在时仍执行一次同成本的 bcrypt 验证，
# 使"邮箱已注册"与"邮箱未注册"两条路径耗时一致，防止通过响应时间枚举注册邮箱。
# 该哈希在模块加载时用随机密码生成一次，与真实用户哈希成本完全相同。
_DUMMY_PASSWORD = uuid4().hex
DUMMY_PASSWORD_HASH = pwd_context.hash(_DUMMY_PASSWORD)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码是否与哈希匹配。

    验证明文密码是否与哈希值匹配。

    注意：bcrypt 对密码长度有 72 字节限制，超长部分会被截断。
    这里主动截断到 72 字节，保证哈希与验证行为一致。

    Args:
        plain_password: 用户输入的明文密码。
        hashed_password: 数据库中存储的 bcrypt 哈希值。

    Returns:
        True 表示密码匹配，False 表示不匹配。
    """
    # bcrypt 算法对输入有 72 字节限制，超长部分会被截断。
    # 这里主动截断到 72 字节，确保哈希和验证行为一致。 按照UTF-8编码转成字节
    password_bytes = plain_password.encode('utf-8')[:72]
    # passlib 的 verify() 内部会从 hashed_password 中提取 salt 并重新哈希比对 errors=ignore，就是忽略了那些不完整的切片
    return pwd_context.verify(password_bytes.decode('utf-8', errors='ignore'), hashed_password)


def verify_password_dummy(plain_password: str) -> None:
    """执行一次与真实验证同成本的 bcrypt 验证（结果丢弃），用于抹平登录时序差异。"""
    verify_password(plain_password, DUMMY_PASSWORD_HASH)


def get_password_hash(password: str) -> str:
    """对明文密码进行哈希。

    将明文密码哈希为 bcrypt 密文，用于存储到数据库。

    注意：bcrypt 对密码长度有 72 字节限制，超长部分会被截断。
    这里截断到 72 字节，避免超长密码导致报错。

    Args:
        password: 用户输入的明文密码。

    Returns:
        bcrypt 哈希字符串（含算法标识、salt、哈希值，约 60 字符）。
    """
    # 与 verify_password 保持同样的截断逻辑，确保两端一致
    password_bytes = password.encode('utf-8')[:72]
    # passlib 的 hash() 会自动生成随机 salt 并嵌入结果中，无需单独存储 salt
    return pwd_context.hash(password_bytes.decode('utf-8', errors='ignore'))


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """创建 JWT（JSON Web Token）访问令牌。

    创建 JWT 访问令牌。

    JWT（JSON Web Token）是一种无状态令牌：服务端不存储会话，
    只在令牌中编码用户标识和过期时间，用密钥签名防止篡改。

    Args:
        data: 要编码进 JWT 的载荷数据，通常包含 {"sub": user_id, "email": email}。
        expires_delta: 自定义过期时间增量。若为 None，则使用配置中的默认过期时间。

    Returns:
        编码后的 JWT 字符串（三段式：header.payload.signature）。
    """
    settings = get_settings()
    # 复制载荷字典，避免修改原始引用（函数式最佳实践）
    to_encode = data.copy()
    if expires_delta:
        # 使用调用方指定的过期时间（如"记住我"模式使用更长的过期时间）
        expire = utc_now() + expires_delta
    else:
        # 使用配置默认的过期时间（分钟级）
        expire = utc_now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # 将过期时间戳 "exp" 写入载荷，jose 库在解码时会自动校验是否过期
    to_encode.update({"exp": expire})
    # 使用密钥和指定算法（如 HS256）对载荷签名，生成最终 JWT 字符串 algorithm:JWT签名算法
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any] | None:
    """解码并验证 JWT（JSON Web Token）令牌。

    解码并验证 JWT 令牌。

    验证包括：签名是否正确、是否已过期。任一检查失败则返回 None。

    Args:
        token: 客户端传来的 JWT 字符串。

    Returns:
        解码后的载荷字典（含 sub、email、exp 等字段），验证失败返回 None。
    """
    settings = get_settings()
    try:
        # jose 库自动完成签名验证 + 过期检查，algorithms 参数必须为列表形式
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        # 令牌无效（签名错误、格式错误、已过期等），返回 None 由调用方处理
        return None
