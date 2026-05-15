"""AI 模块路由 - 独立模块，不影响原有代码"""

import json
import logging
from typing import Annotated, AsyncGenerator

logger = logging.getLogger(__name__)
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.utils.deps import get_current_active_user, get_current_admin_user
from app.models.user import User
from app.schemas.ai import (
    ChoiceExplanationRequest,
    ChoiceExplanationResponse,
    CodeReviewRequest,
    CodeReviewResponse,
    AIConfigResponse,
    UpdateAIConfigRequest,
    AIChatRequest,
    AIChatResponse,
    ChoiceAnalysisRequest,
    ChoiceAnalysisResponse,
    CodeFeedbackRequest,
    CodeFeedbackResponse,
    ChatStreamRequest,
    AIStatusResponse,
    TestConnectionRequest,
    TestConnectionResponse,
    ExerciseHintRequest,
)
from app.services.ai import ai_service
from app.config import get_settings


def _make_preview(key: str) -> str:
    """生成密钥预览：显示前4位和后4位，中间用****掩码。"""
    if not key or len(key) <= 8:
        return "****"
    return f"{key[:4]}****{key[-4:]}"


# 选择题 AI 解答路由
choice_router = APIRouter(prefix="/api/ai", tags=["ai-choice"])

# 代码审查路由
review_router = APIRouter(prefix="/api/ai", tags=["ai-review"])

# AI 配置管理路由（管理员专用）
config_router = APIRouter(prefix="/api/admin/ai", tags=["ai-config"])


@choice_router.post("/choice-explanation", response_model=ChoiceExplanationResponse)
async def get_choice_explanation(
    request: ChoiceExplanationRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """获取选择题 AI 解答 - 独立接口"""
    try:
        explanation = await ai_service.generate_choice_explanation(
            question=request.question,
            options=request.options,
            user_selected_index=request.user_selected_index,
            correct_index=request.correct_index,
        )
        return ChoiceExplanationResponse(explanation=explanation)
    except Exception:
        logger.exception("AI choice explanation failed")
        raise HTTPException(status_code=500, detail="AI 服务暂不可用，请稍后重试")


@review_router.post("/code-review", response_model=CodeReviewResponse)
async def get_code_review(
    request: CodeReviewRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """获取代码 AI 审查报告 - 独立接口"""
    try:
        review = await ai_service.generate_code_review(
            code=request.code,
            language=request.language,
            chapter_id=request.chapter_id,
            subsection_index=request.subsection_index,
        )
        return CodeReviewResponse(review=review)
    except Exception:
        logger.exception("AI code review failed")
        raise HTTPException(status_code=500, detail="AI 服务暂不可用，请稍后重试")


@config_router.get("/config", response_model=AIConfigResponse)
async def get_ai_config(
    current_user: Annotated[User, Depends(get_current_admin_user)],
):
    """获取当前 AI 配置 - 管理员专用"""
    settings = get_settings()

    return AIConfigResponse(
        provider=settings.AI_PROVIDER,
        model=settings.AI_MODEL,
        temperature=settings.AI_TEMPERATURE,
        is_configured=bool(settings.AI_API_KEY),
        has_api_key=bool(settings.AI_API_KEY),
        api_key_preview=_make_preview(settings.AI_API_KEY) if settings.AI_API_KEY else None,
        api_key_length=len(settings.AI_API_KEY) if settings.AI_API_KEY else None,
        connection_status=None,
        connection_address=settings.AI_BASE_URL,
        is_local_first=settings.AI_LOCAL_FIRST,
    )


@config_router.put("/config")
async def update_ai_config(
    request: UpdateAIConfigRequest,
    current_user: Annotated[User, Depends(get_current_admin_user)],
):
    """更新 AI 配置 - 管理员专用（持久化到 .env）"""
    from app.schemas.ai import AIProviderConfig
    from dotenv import set_key
    import os

    settings = get_settings()
    # 重要: 用空字符串显式删除 API key，不允许 None 值绕过
    api_key_to_save = settings.AI_API_KEY
    if request.api_key is not None:
        api_key_to_save = request.api_key  # 空字符串 = 删除key

    AIProviderConfig(
        provider=request.provider or settings.AI_PROVIDER,
        api_key=api_key_to_save,
        model=request.model or settings.AI_MODEL,
        temperature=request.temperature
        if request.temperature is not None
        else settings.AI_TEMPERATURE,
        base_url=request.base_url or settings.AI_BASE_URL,
        local_base_url=request.local_base_url or settings.AI_LOCAL_BASE_URL,
        is_local_first=request.is_local_first if request.is_local_first is not None else settings.AI_LOCAL_FIRST,
    )

    # 持久化到 .env
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    if request.provider is not None:
        set_key(env_path, "AI_PROVIDER", request.provider)
    # 空字符串也写入 .env（实现 key 删除）
    if request.api_key is not None:
        set_key(env_path, "AI_API_KEY", request.api_key)
    if request.model is not None:
        set_key(env_path, "AI_MODEL", request.model)
    if request.temperature is not None:
        set_key(env_path, "AI_TEMPERATURE", str(request.temperature))
    if request.base_url is not None:
        set_key(env_path, "AI_BASE_URL", request.base_url)
    if request.local_base_url is not None:
        set_key(env_path, "AI_LOCAL_BASE_URL", request.local_base_url)
    if request.is_local_first is not None:
        set_key(env_path, "AI_LOCAL_FIRST", str(request.is_local_first).lower())

    # 清除缓存，确保 get_settings() 返回新值
    get_settings.cache_clear()

    # 用新值重新配置（清除 lru_cache 后 get_settings() 会重新加载 .env）
    fresh_settings = get_settings()
    fresh_config = AIProviderConfig(
        provider=fresh_settings.AI_PROVIDER,
        api_key=fresh_settings.AI_API_KEY,
        model=fresh_settings.AI_MODEL,
        temperature=fresh_settings.AI_TEMPERATURE,
        base_url=fresh_settings.AI_BASE_URL,
        local_base_url=fresh_settings.AI_LOCAL_BASE_URL,
        is_local_first=fresh_settings.AI_LOCAL_FIRST,
    )
    ai_service.configure(fresh_config)
    return {"message": "AI 配置已保存并生效"}


@config_router.get("/status", response_model=AIStatusResponse)
async def get_ai_status(
    current_user: Annotated[User, Depends(get_current_admin_user)],
):
    """获取所有 AI Provider 的连接状态"""
    return await ai_service.get_provider_status()


@config_router.post("/test-connection", response_model=TestConnectionResponse)
async def test_ai_connection(
    request: TestConnectionRequest,
    current_user: Annotated[User, Depends(get_current_admin_user)],
):
    """测试指定 Provider 的连接是否正常"""
    import time
    import httpx
    from app.services.ai import OllamaProvider, LMStudioProvider

    start = time.time()

    if request.provider == "ollama":
        address = request.local_base_url or OllamaProvider.DEFAULT_BASE_URL
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{address}/v1/models")
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m.get("id", "") for m in data.get("data", [])]
                    model = models[0] if models else request.model or ""
                    latency = int((time.time() - start) * 1000)
                    return TestConnectionResponse(
                        success=True,
                        message="连接成功",
                        model=model,
                        address=address,
                        latency_ms=latency,
                    )
                else:
                    latency = int((time.time() - start) * 1000)
                    return TestConnectionResponse(
                        success=False,
                        message=f"HTTP {resp.status_code}",
                        address=address,
                        latency_ms=latency,
                    )
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            return TestConnectionResponse(
                success=False,
                message=f"连接失败: {e}",
                address=address,
                latency_ms=latency,
            )

    elif request.provider == "lmstudio":
        address = request.local_base_url or LMStudioProvider.DEFAULT_BASE_URL
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{address}/v1/models")
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m.get("id", "") for m in data.get("data", [])]
                    model = models[0] if models else request.model or ""
                    latency = int((time.time() - start) * 1000)
                    return TestConnectionResponse(
                        success=True,
                        message="连接成功",
                        model=model,
                        address=address,
                        latency_ms=latency,
                    )
                else:
                    latency = int((time.time() - start) * 1000)
                    return TestConnectionResponse(
                        success=False,
                        message=f"HTTP {resp.status_code}",
                        address=address,
                        latency_ms=latency,
                    )
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            return TestConnectionResponse(
                success=False,
                message=f"连接失败: {e}",
                address=address,
                latency_ms=latency,
            )

    elif request.provider == "minimax":
        address = request.base_url or "https://api.minimaxi.com/anthropic"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{address}/v1/messages",
                    headers={
                        "x-api-key": request.api_key or get_settings().AI_API_KEY,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": request.model or "MiniMax-M2.7",
                        "max_tokens": 1,
                        "messages": [{"role": "user", "content": "hi"}],
                    },
                )
                latency = int((time.time() - start) * 1000)
                if resp.status_code == 200:
                    return TestConnectionResponse(
                        success=True,
                        message="连接成功",
                        model=request.model or "MiniMax-M2.7",
                        address=address,
                        latency_ms=latency,
                    )
                else:
                    return TestConnectionResponse(
                        success=False,
                        message=f"HTTP {resp.status_code}: {resp.text[:100]}",
                        address=address,
                        latency_ms=latency,
                    )
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            return TestConnectionResponse(
                success=False,
                message=f"连接失败: {e}",
                address=address,
                latency_ms=latency,
            )

    elif request.provider in ("deepseek", "siliconflow"):
        address = request.base_url or ("https://api.deepseek.com" if request.provider == "deepseek" else "https://api.siliconflow.cn/v1")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{address}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {request.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": request.model or ("deepseek-v4-flash" if request.provider == "deepseek" else "deepseek-ai/DeepSeek-V3"),
                        "max_tokens": 1,
                        "messages": [{"role": "user", "content": "hi"}],
                    },
                )
                latency = int((time.time() - start) * 1000)
                if resp.status_code == 200:
                    return TestConnectionResponse(
                        success=True,
                        message="连接成功",
                        model=request.model or ("deepseek-v4-flash" if request.provider == "deepseek" else "deepseek-ai/DeepSeek-V3"),
                        address=address,
                        latency_ms=latency,
                    )
                else:
                    return TestConnectionResponse(
                        success=False,
                        message=f"HTTP {resp.status_code}: {resp.text[:100]}",
                        address=address,
                        latency_ms=latency,
                    )
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            return TestConnectionResponse(
                success=False,
                message=f"连接失败: {e}",
                address=address,
                latency_ms=latency,
            )

    return TestConnectionResponse(
        success=False,
        message=f"未知 Provider: {request.provider}",
    )


# AI 聊天路由
chat_router = APIRouter(prefix="/api/ai", tags=["ai-chat"])


@chat_router.post("/chat", response_model=AIChatResponse)
async def ai_chat(
    request: AIChatRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """AI 智能问答 - 用户可随时提问"""
    try:
        reply = await ai_service.generate_chat(message=request.message)
        return AIChatResponse(reply=reply)
    except Exception:
        logger.exception("AI chat failed")
        raise HTTPException(status_code=500, detail="AI 服务暂不可用，请稍后重试")


async def sse_chat_generator(
    message: str, context: dict | None
) -> AsyncGenerator[bytes, None]:
    """SSE 格式的聊天流生成器"""
    try:
        async for chunk in ai_service.stream_chat(message, context):
            payload = json.dumps({"content": chunk}) + "\n"
            yield f"data: {payload}\n\n".encode()
        yield b"data: [DONE]\n\n"
    except Exception as e:
        error_payload = json.dumps({"error": str(e)}) + "\n"
        yield f"data: {error_payload}\n\n".encode()


@chat_router.post("/chat/stream")
async def ai_chat_stream(
    request: ChatStreamRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """AI 智能问答（流式）- 支持题目上下文"""
    return StreamingResponse(
        sse_chat_generator(request.message, request.context),
        media_type="text/event-stream",
    )


# AI 嵌入式分析路由
analysis_router = APIRouter(prefix="/api/ai", tags=["ai-analysis"])


@analysis_router.post("/choice-analysis", response_model=ChoiceAnalysisResponse)
async def analyze_choice(
    request: ChoiceAnalysisRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """选择题 AI 分析 —— 学生答错后触发"""
    try:
        result = await ai_service.generate_choice_analysis(
            question_text=request.question_text,
            options=request.options,
            user_selected=request.user_selected,
            correct_answer=request.correct_answer,
        )
        return ChoiceAnalysisResponse(**result)
    except Exception:
        logger.exception("AI analysis failed")
        raise HTTPException(status_code=500, detail="AI 服务暂不可用，请稍后重试")


@analysis_router.post("/code-feedback", response_model=CodeFeedbackResponse)
async def get_code_feedback(
    request: CodeFeedbackRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """编程题 AI 反馈 —— 纠错 + 优化 + 建议 三合一"""
    try:
        result = await ai_service.generate_code_feedback(
            code=request.code,
            language=request.language,
            exercise_description=request.exercise_description,
            expected_output=request.expected_output,
            actual_output=request.actual_output,
            status=request.status,
            error_message=request.error_message,
        )
        return CodeFeedbackResponse(**result)
    except Exception:
        logger.exception("AI feedback failed")
        raise HTTPException(status_code=500, detail="AI 服务暂不可用，请稍后重试")


# ========================================
# AI 编程题提示路由（挑战之路）
# ========================================

hint_router = APIRouter(prefix="/api/ai", tags=["ai-hint"])

# 提示级别对应的智核消耗
HINT_COSTS = {
    "light": 1,
    "medium": 3,
    "deep": 5,
}


@hint_router.get("/exercise-hint/cache/{exercise_id}/{hint_level}")
async def get_cached_hint(
    exercise_id: str,
    hint_level: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """获取缓存的 AI 提示 - 如果用户已购买过，免费返回"""
    from app.models.ai_hint_cache import AIHintCache

    result = await db.execute(
        select(AIHintCache).where(
            AIHintCache.user_id == current_user.id,
            AIHintCache.exercise_id == exercise_id,
            AIHintCache.hint_level == hint_level,
        )
    )
    cached = result.scalar_one_or_none()

    if cached:
        return {
            "cached": True,
            "hint": cached.hint_content,
            "cost": 0,  # 免费
        }

    return {"cached": False, "cost": HINT_COSTS.get(hint_level, 1)}


async def sse_exercise_hint_generator(
    request: ExerciseHintRequest,
    user: User,
    db: AsyncSession,
    cost: int,
    exercise_id: str,
) -> AsyncGenerator[bytes, None]:
    """SSE 格式的编程题提示流生成器，包含智核扣除和缓存"""
    from app.services.core_service import CoreService
    from app.models.ai_hint_cache import AIHintCache

    try:
        # 使用 CoreService 扣除智核（会创建交易记录）
        core_service = CoreService(db)
        category = f"ai_hint_{request.hint_level}"  # ai_hint_light, ai_hint_medium, ai_hint_deep

        try:
            await core_service.spend_cores(
                user_id=user.id,
                amount=cost,
                category=category,
                reference_type="exercise_hint",
                reference_id=exercise_id,
                description=f"AI提示 - {request.exercise_title[:50]}",
            )
        except ValueError as e:
            if "Insufficient" in str(e):
                error_payload = json.dumps({"error": "智核余额不足", "code": "INSUFFICIENT_CORES"}) + "\n"
                yield f"data: {error_payload}\n\n".encode()
                return
            raise

        # 收集完整内容用于缓存
        full_content = ""

        # 生成提示
        async for chunk in ai_service.stream_exercise_hint(
            exercise_title=request.exercise_title,
            exercise_description=request.exercise_description,
            difficulty=request.difficulty,
            knowledge_points=request.knowledge_points,
            hint_level=request.hint_level,
            code_template=request.code_template,
            sample_input=request.sample_input,
            sample_output=request.sample_output,
        ):
            full_content += chunk
            payload = json.dumps({"content": chunk}) + "\n"
            yield f"data: {payload}\n\n".encode()

        # 保存缓存
        if full_content:
            cache = AIHintCache(
                user_id=user.id,
                exercise_id=exercise_id,
                hint_level=request.hint_level,
                hint_content=full_content,
                cost=cost,
            )
            db.add(cache)
            await db.commit()

        yield b"data: [DONE]\n\n"
    except Exception as e:
        error_payload = json.dumps({"error": str(e)}) + "\n"
        yield f"data: {error_payload}\n\n".encode()


@hint_router.post("/exercise-hint/stream")
async def stream_exercise_hint(
    request: ExerciseHintRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """编程题 AI 提示（流式）- 挑战之路使用

    智核会在流式输出开始时扣除，如果余额不足会立即返回错误。
    生成后会缓存，下次访问免费。
    """
    from app.models.ai_hint_cache import AIHintCache

    # 使用前端传递的 exercise_id，如果没有则基于标题生成
    if request.exercise_id:
        exercise_id = request.exercise_id
    else:
        import hashlib
        exercise_id = hashlib.md5(
            f"{request.exercise_title}:{request.exercise_description[:100]}".encode()
        ).hexdigest()[:16]

    logger.info(f"[AI Hint] user={current_user.id[:8]}... exercise_id={exercise_id} level={request.hint_level}")

    # 检查是否已缓存
    result = await db.execute(
        select(AIHintCache).where(
            AIHintCache.user_id == current_user.id,
            AIHintCache.exercise_id == exercise_id,
            AIHintCache.hint_level == request.hint_level,
        )
    )
    cached = result.scalar_one_or_none()

    if cached:
        logger.info("[AI Hint] CACHE HIT! Returning cached content")
        # 直接返回缓存内容（不扣费）
        async def cached_generator(content: str) -> AsyncGenerator[bytes, None]:
            # 模拟流式输出效果
            chunk_size = 20
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                payload = json.dumps({"content": chunk, "cached": True}) + "\n"
                yield f"data: {payload}\n\n".encode()
            yield b"data: [DONE]\n\n"

        return StreamingResponse(
            cached_generator(cached.hint_content),
            media_type="text/event-stream",
        )

    logger.info("[AI Hint] CACHE MISS, generating new hint...")

    # 获取消耗
    cost = HINT_COSTS.get(request.hint_level, 1)

    return StreamingResponse(
        sse_exercise_hint_generator(request, current_user, db, cost, exercise_id),
        media_type="text/event-stream",
    )
