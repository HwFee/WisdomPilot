from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.models import ChapterProgress, LearningSession, ActivityLog  # noqa: F401 - registers models
from app.middleware import RateLimitMiddleware
from app.routers import (
    auth_router,
    users_router,
    admin_router,
    stats_router,
    code_router,
)
from app.routers.ai import choice_router, review_router, config_router


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
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(admin_router)
app.include_router(stats_router)
app.include_router(code_router)

# AI Module routers (独立模块)
app.include_router(choice_router)
app.include_router(review_router)
app.include_router(config_router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "AIcodiingTeach API is running"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}
