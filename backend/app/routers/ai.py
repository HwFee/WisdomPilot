"""AI 模块路由 - 独立模块，不影响原有代码"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.utils.deps import get_current_active_user
from app.models.user import User
from app.schemas.ai import (
    ChoiceExplanationRequest,
    ChoiceExplanationResponse,
    CodeReviewRequest,
    CodeReviewResponse,
    AIConfigResponse,
    UpdateAIConfigRequest,
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
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """获取当前 AI 配置 - 管理员专用"""
    # TODO: 添加管理员权限检查
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
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """更新 AI 配置 - 管理员专用"""
    # TODO: 添加管理员权限检查
    # TODO: 持久化配置到数据库
    # 当前仅更新内存中的配置
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
    return {"message": "AI 配置已更新"}
