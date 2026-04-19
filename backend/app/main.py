from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.database import init_db
from app.models import ChapterProgress, LearningSession, ActivityLog  # noqa: F401 - registers models
from app.models import Course, Chapter, Exercise  # noqa: F401 - registers course models
from app.models import Challenge, UserChallenge  # noqa: F401 - registers challenge models
from app.models import Achievement, UserAchievement  # noqa: F401 - registers achievement models
from app.models import UserWeakPoint, SpacedRepetition  # noqa: F401 - registers new models
from app.models import Favorite, Note, NoteTag  # noqa: F401 - registers favorites and notes models
from app.models import ChapterMastery, ChallengeSession, UserArenaProfile  # noqa: F401 - registers mastery and arena models
from app.models import WrongQuestion  # noqa: F401 - registers wrong question model
from app.middleware import RateLimitMiddleware
from app.routers import (
    auth_router,
    users_router,
    admin_router,
    stats_router,
    code_router,
)
from app.routers.courses import router as courses_router
from app.routers.ai import choice_router, review_router, config_router, chat_router, analysis_router
from app.routers.challenges import router as challenges_router
from app.routers.achievements import router as achievements_router
from app.routers.exercises import router as exercises_router
from app.routers.review import router as spaced_review_router
from app.routers.chapters import router as chapters_router
from app.routers.favorites import router as favorites_router
from app.routers.notes import router as notes_router
from app.routers.note_tags import router as note_tags_router
from app.routers.learning_path import router as learning_path_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup: initialize database and AI service
    await init_db()
    # Initialize AI service with config from settings
    from app.services.ai import ai_service
    from app.schemas.ai import AIProviderConfig
    from app.config import get_settings

    settings = get_settings()
    ai_config = AIProviderConfig(
        provider=settings.AI_PROVIDER,
        api_key=settings.AI_API_KEY,
        model=settings.AI_MODEL,
        temperature=settings.AI_TEMPERATURE,
        base_url=settings.AI_BASE_URL,
        local_base_url=settings.AI_LOCAL_BASE_URL,
        is_local_first=settings.AI_LOCAL_FIRST,
    )
    ai_service.configure(ai_config)
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="AIcodiingTeach API",
    description="AI-powered Programming Teaching Platform API",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiting middleware (C5, C8) -- must be added before CORS
app.add_middleware(RateLimitMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(admin_router)
app.include_router(stats_router)
app.include_router(code_router)
app.include_router(courses_router)

# AI Module routers (独立模块)
app.include_router(choice_router)
app.include_router(review_router)
app.include_router(config_router)
app.include_router(chat_router)
app.include_router(analysis_router)
app.include_router(challenges_router)
app.include_router(achievements_router)
app.include_router(exercises_router)
app.include_router(chapters_router)
app.include_router(spaced_review_router)
app.include_router(favorites_router)
app.include_router(notes_router)
app.include_router(note_tags_router)
app.include_router(learning_path_router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "AIcodiingTeach API is running"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    将 Pydantic 验证错误转换为友好的中文消息。

    FastAPI 默认返回复杂的验证错误对象，前端难以解析。
    此处理器将其转换为简单字符串，方便前端显示。
    """
    errors = exc.errors()
    messages = []

    # 字段名称映射（英 -> 中）
    field_names = {
        "email": "邮箱",
        "username": "用户名",
        "password": "密码",
    }

    for error in errors:
        # 获取字段名
        loc = error.get("loc", [])
        field = loc[-1] if loc else "未知字段"
        field_cn = field_names.get(field, field)

        # 获取错误类型和消息
        error_type = error.get("type", "")
        msg = error.get("msg", "验证失败")
        ctx = error.get("ctx", {})

        # 处理不同类型的错误
        if error_type == "string_too_short":
            min_length = ctx.get("min_length", 8)
            messages.append(f"{field_cn}长度至少需要{min_length}个字符")
        elif error_type == "value_error":
            # 自定义验证错误（如密码复杂度）
            # 尝试从 ctx 中获取原始 ValueError 消息
            if "error" in ctx:
                original_msg = str(ctx["error"])
                messages.append(f"{field_cn}: {original_msg}")
            elif "Password must contain at least one letter" in msg:
                messages.append(f"{field_cn}需要包含至少一个字母")
            elif "Password must contain at least one digit" in msg:
                messages.append(f"{field_cn}需要包含至少一个数字")
            else:
                # 移除 "Value error, " 前缀
                clean_msg = msg.replace("Value error, ", "").strip()
                messages.append(f"{field_cn}: {clean_msg}")
        elif error_type == "value_error.email":
            messages.append("请输入有效的邮箱地址")
        elif "missing" in error_type:
            messages.append(f"缺少必填字段: {field_cn}")
        else:
            # 默认处理
            messages.append(f"{field_cn}: {msg}")

    return JSONResponse(
        status_code=422,
        content={"detail": "; ".join(messages)}
    )
