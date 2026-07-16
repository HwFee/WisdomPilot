"""Exception handlers for API responses."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

FIELD_NAMES = {
    "email": "邮箱",
    "username": "用户名",
    "password": "密码",
}
DEFAULT_MIN_LENGTH = 8
VALIDATION_FAILED_MESSAGE = "验证失败"
UNKNOWN_FIELD_NAME = "未知字段"


def get_field_name(error: dict[str, Any]) -> str:
    """Return the display name for the failed validation field."""
    location = error.get("loc", [])
    field = location[-1] if location else UNKNOWN_FIELD_NAME
    return FIELD_NAMES.get(field, field)


def format_value_error(field_name: str, message: str, context: dict[str, Any]) -> str:
    """Return a friendly message for Pydantic value errors."""
    if "error" in context:
        return f"{field_name}: {context['error']}"

    if "Password must contain at least one letter" in message:
        return f"{field_name}需要包含至少一个字母"

    if "Password must contain at least one digit" in message:
        return f"{field_name}需要包含至少一个数字"

    clean_message = message.replace("Value error, ", "").strip()
    return f"{field_name}: {clean_message}"


def format_validation_error(error: dict[str, Any]) -> str:
    """Return a single friendly validation error message."""
    field_name = get_field_name(error)
    error_type = error.get("type", "")
    message = error.get("msg", VALIDATION_FAILED_MESSAGE)
    context = error.get("ctx", {})

    if error_type == "string_too_short":
        min_length = context.get("min_length", DEFAULT_MIN_LENGTH)
        return f"{field_name}长度至少需要{min_length}个字符"

    if error_type == "value_error":
        return format_value_error(field_name, message, context)

    if error_type == "value_error.email":
        return "请输入有效的邮箱地址"

    if "missing" in error_type:
        return f"缺少必填字段: {field_name}"

    return f"{field_name}: {message}"


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Convert validation details into a frontend-friendly string."""
    messages = [format_validation_error(error) for error in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": "; ".join(messages)})


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Log unexpected errors without exposing internals to clients."""
    logger.error(
        "Unhandled exception on %s %s",
        request.method,
        request.url,
        exc_info=True,
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


def register_exception_handlers(app: FastAPI) -> None:
    """Register application-wide exception handlers."""
    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(Exception, global_exception_handler)
