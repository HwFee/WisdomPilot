"""
Core (智核) Router - API endpoints for core currency management
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.utils.deps import get_current_user
from app.models.user import User
from app.services.core_service import CoreService, get_core_service
from app.schemas.core import (
    CoreBalanceResponse,
    CoreSpendRequest,
    CoreSpendResponse,
    CoreEarnRequest,
    CoreEarnResponse,
    CoreTransactionListResponse,
    DailyCoreSummaryResponse,
)

router = APIRouter(prefix="/api/cores", tags=["cores"])


@router.get("/balance")
async def get_core_balance(
    current_user: User = Depends(get_current_user),
    core_service: CoreService = Depends(get_core_service),
) -> CoreBalanceResponse:
    """Get user's current core (智核) balance"""
    try:
        balance_data = await core_service.get_balance(current_user.id)
        return CoreBalanceResponse(**balance_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/spend")
async def spend_cores(
    request: CoreSpendRequest,
    current_user: User = Depends(get_current_user),
    core_service: CoreService = Depends(get_core_service),
) -> CoreSpendResponse:
    """Spend cores for AI hints and other features

    Categories:
    - ai_hint_light: Light hint (1 core)
    - ai_hint_medium: Medium hint (3 cores)
    - ai_hint_deep: Deep explanation (5 cores)
    """
    try:
        result = await core_service.spend_cores(
            user_id=current_user.id,
            amount=request.amount,
            category=request.category.value,  # Convert enum to string
            reference_type=request.reference_type,
            reference_id=request.reference_id,
            description=request.description,
        )
        return CoreSpendResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/earn")
async def earn_cores(
    request: CoreEarnRequest,
    current_user: User = Depends(get_current_user),
    core_service: CoreService = Depends(get_core_service),
) -> CoreEarnResponse:
    """Earn cores from various activities (for testing/manual award)

    Categories:
    - mastery: Mastery path correct answer (+2 cores)
    - arena: Arena path correct answer (+3 cores)
    - checkin: Daily check-in (+5-55 cores based on streak)
    - study_time: Study time reward
    - daily_exercises: Daily exercise completion
    - daily_accuracy: Daily accuracy bonus
    - bonus: System bonus
    """
    try:
        result = await core_service.earn_cores(
            user_id=current_user.id,
            amount=request.amount,
            category=request.category.value,
            reference_type=request.reference_type,
            reference_id=request.reference_id,
            description=request.description,
        )
        return CoreEarnResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/transactions")
async def get_core_transactions(
    current_user: User = Depends(get_current_user),
    core_service: CoreService = Depends(get_core_service),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> CoreTransactionListResponse:
    """Get user's core transaction history"""
    result = await core_service.get_transactions(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )
    return CoreTransactionListResponse(**result)


@router.get("/daily-summary")
async def get_daily_core_summary(
    current_user: User = Depends(get_current_user),
    core_service: CoreService = Depends(get_core_service),
) -> DailyCoreSummaryResponse:
    """Get user's daily core statistics including pending rewards"""
    result = await core_service.get_daily_summary(current_user.id)
    return DailyCoreSummaryResponse(**result)


# ============================================
# 测试专用端点 - 不影响真实统计数据
# ============================================

@router.post("/test/earn")
async def test_earn_cores(
    request: CoreEarnRequest,
    current_user: User = Depends(get_current_user),
    core_service: CoreService = Depends(get_core_service),
) -> CoreEarnResponse:
    """[测试专用] 模拟获取智核，不影响做题统计、正确率、段位等

    仅用于测试智核系统，不会：
    - 增加今日做题数
    - 影响正确率
    - 改变段位/星星
    - 解锁章节进度
    """
    try:
        result = await core_service.earn_cores(
            user_id=current_user.id,
            amount=request.amount,
            category=request.category.value,
            reference_type=request.reference_type or "test",
            reference_id=request.reference_id or "test",
            description=f"[测试] {request.description or '模拟获取'}",
        )
        return CoreEarnResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/test/spend")
async def test_spend_cores(
    request: CoreSpendRequest,
    current_user: User = Depends(get_current_user),
    core_service: CoreService = Depends(get_core_service),
) -> CoreSpendResponse:
    """[测试专用] 模拟消耗智核，不影响其他统计

    仅用于测试智核消耗，等同于真实的AI提示消耗
    """
    try:
        result = await core_service.spend_cores(
            user_id=current_user.id,
            amount=request.amount,
            category=request.category.value,
            reference_type=request.reference_type or "test",
            reference_id=request.reference_id or "test",
            description=f"[测试] {request.description or '模拟消耗'}",
        )
        return CoreSpendResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

