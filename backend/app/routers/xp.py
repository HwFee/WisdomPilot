"""
Mastery XP (精进之路经验) Router - API endpoints for mastery XP management
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.utils.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.services.mastery_xp_transaction_service import (
    MasteryXpTransactionService,
)
from pydantic import BaseModel, Field
from typing import Optional
import logging

router = APIRouter(prefix="/api/xp", tags=["xp"])


class XpBalanceResponse(BaseModel):
    """经验余额响应"""
    balance: int
    level: str


class XpEarnRequest(BaseModel):
    """获取经验请求"""
    amount: int = Field(..., ge=1, le=100, description="经验数量")
    category: str = Field(..., description="来源类型")
    reference_type: Optional[str] = Field(None, description="关联类型")
    reference_id: Optional[str] = Field(None, description="关联ID")
    description: Optional[str] = Field(None, description="描述")


class XpEarnResponse(BaseModel):
    """获取经验响应"""
    id: str
    type: str
    category: str
    amount: int
    balance_after: int
    level_before: str
    level_after: str
    level_up: bool
    description: Optional[str]
    created_at: str


class XpTransactionListResponse(BaseModel):
    """经验交易记录列表响应"""
    transactions: list[dict]
    total: int


@router.get("/balance")
async def get_xp_balance(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
) -> XpBalanceResponse:
    """Get user's current mastery XP balance and level"""
    service = MasteryXpTransactionService(db)
    try:
        balance_data = await service.get_balance(current_user.id)
        return XpBalanceResponse(**balance_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/earn")
async def earn_xp(
    request: XpEarnRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
) -> XpEarnResponse:
    """Earn mastery XP from various activities (for testing/manual award)

    Categories:
    - base_test: Base test questions correct answer
    - mastery_quiz: Mastery quiz completion
    - achievement: Achievement reward
    - bonus: System bonus
    """
    service = MasteryXpTransactionService(db)
    try:
        result = await service.earn_xp(
            user_id=current_user.id,
            amount=request.amount,
            category=request.category,
            reference_type=request.reference_type,
            reference_id=request.reference_id,
            description=request.description,
        )
        return XpEarnResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/transactions")
async def get_xp_transactions(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> XpTransactionListResponse:
    """Get user's mastery XP transaction history"""
    service = MasteryXpTransactionService(db)
    result = await service.get_transactions(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )
    return XpTransactionListResponse(**result)


logger = logging.getLogger(__name__)