"""
全局异常处理器模块。

本模块将 FastAPI/Pydantic 抛出的异常转换为前端友好的 JSON 响应。
统一异常处理的好处：
    1. 前端不需要解析复杂的错误结构，只需读取 ``detail`` 字段
    2. 错误消息使用中文，对终端用户更友好
    3. 未捕获的异常不会暴露内部堆栈信息给客户端（安全考虑）

处理的异常类型：
    - ``RequestValidationError``: 请求参数校验失败（如字段缺失、格式错误）
    - ``Exception``: 所有其他未捕获的异常（兜底处理）

响应格式：
    所有错误响应统一返回 ``{"detail": "错误描述"}`` 格式的 JSON。
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# 字段名中英映射表：将 Pydantic 的英文字段名转换为中文显示名
FIELD_NAMES = {
    "email": "邮箱",
    "username": "用户名",
    "password": "密码",
}
# 默认最小长度要求（用于密码等字段的长度校验提示）
DEFAULT_MIN_LENGTH = 8
# 校验失败的默认消息
VALIDATION_FAILED_MESSAGE = "验证失败"
# 未知字段的显示名称
UNKNOWN_FIELD_NAME = "未知字段"


def get_field_name(error: dict[str, Any]) -> str:
    """从校验错误中提取字段的中文显示名。

    Pydantic 校验错误中 ``loc`` 字段是一个路径元组，如 ``("body", "password")``，
    最后一个元素是实际出错的字段名。本函数将英文字段名映射为中文。

    Args:
        error: Pydantic 的单个错误字典，包含 ``loc``、``msg``、``type`` 等字段

    Returns:
        str: 字段的中文显示名，如 "密码"、"邮箱"；未映射的字段返回原英文名
    """
    """Return the display name for the failed validation field."""
    location = error.get("loc", [])
    # loc 是一个路径元组，如 ("body", "email")，取最后一个元素作为字段名
    field = location[-1] if location else UNKNOWN_FIELD_NAME
    return FIELD_NAMES.get(field, field)


def format_value_error(field_name: str, message: str, context: dict[str, Any]) -> str:
    """格式化 Pydantic 值错误（value_error）为友好的中文消息。

    处理自定义的密码校验规则等产生的 value_error，将英文消息转为中文。

    Args:
        field_name: 字段的中文显示名（如 "密码"）
        message: 原始错误消息
        context: 错误上下文，可能包含自定义的 ``error`` 字段

    Returns:
        str: 格式化后的中文错误消息
    """
    """Return a friendly message for Pydantic value errors."""
    # 如果上下文中包含自定义 error 字段，直接使用它
    if "error" in context:
        return f"{field_name}: {context['error']}"

    # 密码必须包含字母的校验
    if "Password must contain at least one letter" in message:
        return f"{field_name}需要包含至少一个字母"

    # 密码必须包含数字的校验
    if "Password must contain at least one digit" in message:
        return f"{field_name}需要包含至少一个数字"

    # 其他 value_error：去除 Pydantic 前缀后拼接字段名
    clean_message = message.replace("Value error, ", "").strip()
    return f"{field_name}: {clean_message}"


def format_validation_error(error: dict[str, Any]) -> str:
    """将单个 Pydantic 校验错误格式化为友好的中文消息。

    根据错误类型（``error_type``）分别处理：
        - ``string_too_short``: 字符串太短，提示最小长度要求
        - ``value_error``: 自定义值错误（如密码复杂度校验）
        - ``value_error.email``: 邮箱格式错误
        - 含 ``missing``: 必填字段缺失
        - 其他: 直接拼接字段名和原始消息

    Args:
        error: Pydantic 的单个错误字典

    Returns:
        str: 格式化后的中文错误消息
    """
    """Return a single friendly validation error message."""
    field_name = get_field_name(error)
    error_type = error.get("type", "")
    message = error.get("msg", VALIDATION_FAILED_MESSAGE)
    context = error.get("ctx", {})

    # 字符串长度不足错误
    if error_type == "string_too_short":
        min_length = context.get("min_length", DEFAULT_MIN_LENGTH)
        return f"{field_name}长度至少需要{min_length}个字符"

    # 自定义值错误（如密码复杂度校验）
    if error_type == "value_error":
        return format_value_error(field_name, message, context)

    # 邮箱格式错误
    if error_type == "value_error.email":
        return "请输入有效的邮箱地址"

    # 必填字段缺失
    if "missing" in error_type:
        return f"缺少必填字段: {field_name}"

    # 其他类型的错误：直接拼接
    return f"{field_name}: {message}"


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """请求参数校验失败异常处理器。

    当 Pydantic 校验请求体/参数失败时，FastAPI 会抛出
    ``RequestValidationError``。本处理器将其转换为前端友好的
   中文错误消息。

    响应格式：
        ``{"detail": "密码长度至少需要8个字符; 邮箱: 请输入有效的邮箱地址"}``

    Args:
        request: 触发异常的请求对象
        exc: Pydantic 校验异常，包含所有校验错误的详细信息

    Returns:
        JSONResponse: 422 状态码的 JSON 响应，``detail`` 字段包含所有错误消息（分号分隔）
    """
    """Convert validation details into a frontend-friendly string."""
    # 将每个校验错误格式化为中文消息，用分号连接
    messages = [format_validation_error(error) for error in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": "; ".join(messages)})


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """全局兜底异常处理器。

    捕获所有未被特定处理器处理的异常，记录完整堆栈日志，
    但只向客户端返回通用的错误消息（不暴露内部实现细节）。

    为什么不暴露详细信息：
        - 安全考虑：堆栈信息可能包含文件路径、数据库结构等敏感信息
        - 用户体验：前端只需知道"出错了"，具体原因由后端日志排查

    Args:
        request: 触发异常的请求对象
        exc: 未被捕获的异常对象

    Returns:
        JSONResponse: 500 状态码的 JSON 响应，``detail`` 为通用错误消息
    """
    """Log unexpected errors without exposing internals to clients."""
    # 记录完整的异常堆栈到日志（供开发者排查），exc_info=True 会输出完整 traceback
    logger.error(
        "Unhandled exception on %s %s",
        request.method,
        request.url,
        exc_info=True,
    )
    # 返回通用错误消息，不暴露内部细节
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


def register_exception_handlers(app: FastAPI) -> None:
    """注册应用级异常处理器。

    将异常处理器注册到 FastAPI 应用上。注册顺序不重要，
    FastAPI 会根据异常类型自动匹配最合适的处理器。

    注册的处理器：
        1. ``RequestValidationError`` -> ``validation_exception_handler``
           处理请求参数校验失败，返回 422 + 中文错误消息
        2. ``Exception`` -> ``global_exception_handler``
           兜底处理器，处理所有其他异常，返回 500 + 通用消息

    Args:
        app: FastAPI 应用实例
    """
    """Register application-wide exception handlers."""
    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(Exception, global_exception_handler)
