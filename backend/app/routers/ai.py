"""AI 模块路由 - 独立模块，不影响原有代码"""

import json
from typing import Annotated, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
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
)
from app.services.ai import ai_service
from app.config import get_settings

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 解答失败: {str(e)}")


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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"代码审查失败: {str(e)}")


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
    )


@config_router.put("/config")
async def update_ai_config(
    request: UpdateAIConfigRequest,
    current_user: Annotated[User, Depends(get_current_admin_user)],
):
    """更新 AI 配置 - 管理员专用"""
    from app.schemas.ai import AIProviderConfig

    settings = get_settings()
    new_config = AIProviderConfig(
        provider=request.provider or settings.AI_PROVIDER,
        api_key=request.api_key or settings.AI_API_KEY,
        model=request.model or settings.AI_MODEL,
        temperature=request.temperature
        if request.temperature is not None
        else settings.AI_TEMPERATURE,
        base_url=request.base_url or settings.AI_BASE_URL,
    )
    ai_service.configure(new_config)
    return {"message": "AI 配置更新成功"}


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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 问答失败: {str(e)}")


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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 分析失败: {str(e)}")


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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 反馈失败: {str(e)}")
