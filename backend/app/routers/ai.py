"""AI 模块路由 - 独立模块，不影响原有代码"""

import json
import logging
from typing import Annotated, AsyncGenerator

logger = logging.getLogger(__name__)
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, AsyncSessionLocal
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
    ChatStreamRequest,
    AIStatusResponse,
    TestConnectionRequest,
    TestConnectionResponse,
    ExerciseHintRequest,
)
from app.services.ai import ai_service
from app.services.ai_policy import AIFeature, AIPolicy, get_ai_policy
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
    """测试指定 Provider 的连接是否正常（仅支持 DeepSeek / SiliconFlow）"""
    import time
    import httpx

    start = time.time()

    if request.provider in ("deepseek", "siliconflow"):
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


# ========================================
# AI 编程题提示路由（挑战之路）
# ========================================

hint_router = APIRouter(prefix="/api/ai", tags=["ai-hint"])


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
        policy = get_ai_policy(AIFeature.CHALLENGE_HINT, hint_level=hint_level, cached=True)
        return {
            "cached": True,
            "hint": cached.hint_content,
            "cost": policy.cost,
        }

    policy = get_ai_policy(AIFeature.CHALLENGE_HINT, hint_level=hint_level)
    return {"cached": False, "cost": policy.cost}


async def sse_exercise_hint_generator(
    request: ExerciseHintRequest,
    user_id: str,
    policy: AIPolicy,
    exercise_id: str,
) -> AsyncGenerator[bytes, None]:
    """SSE hint generator using independent short-lived DB sessions.

    DB write locks (core deduction, cache save) are held for milliseconds
    in separate transactions, NOT during AI streaming. This prevents
    SQLite 'database is locked' errors when concurrent requests write
    to the users table.
    """
    import time
    t_total_start = time.time()
    logger.info(f"[PERF-HINT] ====== sse_exercise_hint_generator START ====== user={user_id[:8]}... exercise={exercise_id} level={request.hint_level}")

    from app.services.core_service import CoreService
    from app.models.ai_hint_cache import AIHintCache
    from app.database import AsyncSessionLocal

    cost = policy.cost
    category = policy.category

    # --- Step 1: Deduct cores in a short, independent transaction ---
    t_step1 = time.time()
    try:
        async with AsyncSessionLocal() as deduct_db:
            core_service = CoreService(deduct_db)
            try:
                await core_service.spend_cores(
                    user_id=user_id,
                    amount=cost,
                    category=category,
                    reference_type="exercise_hint",
                    reference_id=exercise_id,
                    description=f"AI提示 - {request.exercise_title[:50]}",
                )
                await deduct_db.commit()
                logger.info(f"[PERF-HINT] Step 1 (deduct cores) done in {(time.time()-t_step1)*1000:.1f}ms")
            except ValueError as e:
                if "Insufficient" in str(e):
                    logger.warning(f"[PERF-HINT] Step 1 (deduct cores) INSUFFICIENT in {(time.time()-t_step1)*1000:.1f}ms")
                    error_payload = json.dumps({
                        "error": "智核余额不足",
                        "code": "INSUFFICIENT_CORES",
                    }) + "\n"
                    yield f"data: {error_payload}\n\n".encode()
                    return
                raise
    except Exception as e:
        logger.error(f"[PERF-HINT] Step 1 (deduct cores) FAILED after {(time.time()-t_step1)*1000:.1f}ms: {e}")
        error_payload = json.dumps({
            "error": "服务暂时不可用，请稍后重试",
            "code": "SERVICE_ERROR",
        }) + "\n"
        yield f"data: {error_payload}\n\n".encode()
        return

    # --- Step 2: Stream AI content (NO DB lock held) ---
    t_step2 = time.time()
    full_content = ""
    stream_failed = False
    chunks_yielded = 0

    for attempt in range(3):
        t_attempt = time.time()
        logger.info(f"[PERF-HINT] Step 2 (AI stream) attempt {attempt+1} starting...")
        try:
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
                chunks_yielded += 1
                payload = json.dumps({"content": chunk}) + "\n"
                yield f"data: {payload}\n\n".encode()
            logger.info(f"[PERF-HINT] Step 2 (AI stream) attempt {attempt+1} SUCCESS in {(time.time()-t_attempt)*1000:.1f}ms, chunks={chunks_yielded}, chars={len(full_content)}")
            break
        except Exception as e:
            logger.error(f"[PERF-HINT] Step 2 (AI stream) attempt {attempt+1} FAILED after {(time.time()-t_attempt)*1000:.1f}ms: {e}")
            if full_content:
                logger.error(f"[AI Hint] Stream failed after partial content: {e}")
                stream_failed = True
                break
            if attempt < 2:
                logger.warning(f"[AI Hint] Attempt {attempt + 1} failed, retrying: {e}")
                continue
            logger.error(f"[AI Hint] All 3 attempts failed: {e}")
            stream_failed = True
    logger.info(f"[PERF-HINT] Step 2 total time: {(time.time()-t_step2)*1000:.1f}ms")

    # --- Step 3: Save cache in a short, independent transaction ---
    t_step3 = time.time()
    if full_content:
        try:
            async with AsyncSessionLocal() as cache_db:
                # 先检查是否已存在，避免 UniqueConstraint 冲突或脏数据重复
                existing = await cache_db.execute(
                    select(AIHintCache).where(
                        AIHintCache.user_id == user_id,
                        AIHintCache.exercise_id == exercise_id,
                        AIHintCache.hint_level == request.hint_level,
                    )
                )
                if existing.scalars().first() is None:
                    cache = AIHintCache(
                        user_id=user_id,
                        exercise_id=exercise_id,
                        hint_level=request.hint_level,
                        hint_content=full_content,
                        cost=cost,
                    )
                    cache_db.add(cache)
                    await cache_db.commit()
                    logger.info(f"[PERF-HINT] Step 3 (save cache) done in {(time.time()-t_step3)*1000:.1f}ms, NEW cache saved")
                else:
                    logger.info(f"[PERF-HINT] Step 3 (save cache) skipped in {(time.time()-t_step3)*1000:.1f}ms, already exists")
        except Exception as e:
            logger.warning(f"[PERF-HINT] Step 3 (save cache) FAILED after {(time.time()-t_step3)*1000:.1f}ms: {e}")

    # --- Step 4: Refund if stream completely failed (no content sent) ---
    if stream_failed and not full_content:
        try:
            async with AsyncSessionLocal() as refund_db:
                core_service = CoreService(refund_db)
                await core_service.earn_cores(
                    user_id=user_id,
                    amount=cost,
                    category="arena",
                    reference_type="exercise_hint_refund",
                    reference_id=exercise_id,
                    description="AI提示生成失败退款",
                )
                await refund_db.commit()
            logger.info(f"[AI Hint] Refunded {cost} cores to {user_id[:8]}...")
        except Exception as e:
            logger.error(f"[AI Hint] Refund failed: {e}")

    # --- Step 5: Termination signal ---
    t_total = (time.time() - t_total_start) * 1000
    if stream_failed and not full_content:
        logger.error(f"[PERF-HINT] ====== END (FAILED) ====== total={t_total:.1f}ms")
        error_payload = json.dumps({
            "error": "AI 服务暂不可用，请稍后重试",
            "code": "AI_SERVICE_ERROR",
        }) + "\n"
        yield f"data: {error_payload}\n\n".encode()
    else:
        logger.info(f"[PERF-HINT] ====== END (SUCCESS) ====== total={t_total:.1f}ms, chunks={chunks_yielded}, chars={len(full_content)}")
        yield b"data: [DONE]\n\n"


@hint_router.post("/exercise-hint/stream")
async def stream_exercise_hint(
    request: ExerciseHintRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """编程题 AI 提示（流式）- 挑战之路使用

    智核会在流式输出开始前扣除（独立短事务），如果余额不足会立即返回错误。
    生成后会缓存，下次访问免费。
    DB 写锁仅在扣费和缓存保存的毫秒级事务中持有，不会在 AI 流式生成期间持有。
    """
    import time
    t_route_start = time.time()
    from app.models.ai_hint_cache import AIHintCache

    # 使用前端传递的 exercise_id，如果没有则基于标题生成
    if request.exercise_id:
        exercise_id = request.exercise_id
    else:
        import hashlib
        exercise_id = hashlib.md5(
            f"{request.exercise_title}:{request.exercise_description[:100]}".encode()
        ).hexdigest()[:16]

    logger.info(f"[PERF-ROUTE] ====== stream_exercise_hint START ====== user={current_user.id[:8]}... exercise_id={exercise_id} level={request.hint_level}")

    # 检查是否已缓存（只读操作，不阻塞）
    t_cache_check = time.time()
    # 使用 .first() 而非 scalar_one_or_none() 防止历史脏数据导致多行报错
    result = await db.execute(
        select(AIHintCache).where(
            AIHintCache.user_id == current_user.id,
            AIHintCache.exercise_id == exercise_id,
            AIHintCache.hint_level == request.hint_level,
        )
    )
    cached = result.scalars().first()
    logger.info(f"[PERF-ROUTE] Cache check done in {(time.time()-t_cache_check)*1000:.1f}ms, hit={cached is not None}")

    if cached:
        logger.info("[AI Hint] CACHE HIT! Returning cached content")
        async def cached_generator(content: str) -> AsyncGenerator[bytes, None]:
            t_gen_start = time.time()
            chunk_size = 20
            total_chars = 0
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                total_chars += len(chunk)
                payload = json.dumps({"content": chunk, "cached": True}) + "\n"
                yield f"data: {payload}\n\n".encode()
            logger.info(f"[PERF-ROUTE] Cached content streamed in {(time.time()-t_gen_start)*1000:.1f}ms, chars={total_chars}")
            yield b"data: [DONE]\n\n"

        return StreamingResponse(
            cached_generator(cached.hint_content),
            media_type="text/event-stream",
        )

    logger.info("[AI Hint] CACHE MISS, generating new hint...")

    policy = get_ai_policy(AIFeature.CHALLENGE_HINT, hint_level=request.hint_level)
    logger.info(f"[PERF-ROUTE] Entering SSE generator, elapsed_so_far={(time.time()-t_route_start)*1000:.1f}ms")

    return StreamingResponse(
        sse_exercise_hint_generator(request, current_user.id, policy, exercise_id),
        media_type="text/event-stream",
    )
