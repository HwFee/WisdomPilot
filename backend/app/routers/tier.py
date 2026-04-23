"""
段位系统API路由

王者荣耀风格段位系统API端点
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.user import User
from app.models.user_arena import UserArenaProfile
from app.models.course import Course
from app.core.tier_config import (
    TierRank,
    get_tier_config,
    get_full_tier_name,
    get_all_tiers,
    get_tier_order,
    get_sub_tier_name,
    tier_from_string,
)
from app.services.tier_service import tier_service, TierUpdateResult
from app.services.tier_transaction_service import TierTransactionService
from app.utils.deps import get_current_active_user
import logging

router = APIRouter(prefix="/api/tier", tags=["tier"])

db_dependency = Annotated[AsyncSession, Depends(get_db)]
auth_dependency = Annotated[User, Depends(get_current_active_user)]


class TierInfoResponse(BaseModel):
    """段位信息响应"""
    tier: str
    tier_name: str
    sub_tier: int
    sub_tier_name: str
    full_name: str
    stars: int
    stars_needed: int
    protection_remaining: int
    color: str
    icon: str
    highest_tier: Optional[str] = None
    highest_sub_tier: Optional[int] = None
    highest_full_name: Optional[str] = None


class AllTiersResponse(BaseModel):
    """所有段位配置响应"""
    tiers: list[dict]


class UpdateStarsRequest(BaseModel):
    """更新星星请求"""
    stars_change: int = Field(..., ge=-10, le=10, description="星星变化量，正数增加，负数减少")
    accuracy: Optional[float] = Field(None, ge=0, le=1, description="正确率，0-1之间")
    difficulty: Optional[int] = Field(None, ge=1, le=5, description="难度等级，1-5")


class UpdateStarsResponse(BaseModel):
    """更新星星响应"""
    tier: str
    sub_tier: int
    stars: int
    stars_change: int
    promoted: bool
    demoted: bool
    used_protection: bool
    protection_remaining: int
    full_name: str
    message: str


@router.get("/config", response_model=AllTiersResponse)
async def get_tier_configurations():
    """获取所有段位配置信息"""
    tiers = []
    for config in get_all_tiers():
        tiers.append({
            "rank": config.rank.value,
            "name": config.name,
            "sub_tiers": config.sub_tiers,
            "stars_per_tier": config.stars_per_tier,
            "color": config.color,
            "icon": config.icon,
            "protection_count": config.protection_count,
        })
    return AllTiersResponse(tiers=tiers)


@router.get("/profile", response_model=TierInfoResponse)
async def get_global_tier_info(
    db: db_dependency,
    current_user: auth_dependency,
):
    """
    获取用户全局段位信息（挑战之路用，不关联课程）

    如果用户没有段位Profile，会自动创建一个初始段位
    """
    # 获取或创建用户段位Profile (全局)
    result = await db.execute(
        select(UserArenaProfile).where(
            UserArenaProfile.user_id == current_user.id,
        )
    )
    profile = result.scalar_one_or_none()

    if not profile:
        # 创建初始段位Profile
        initial_config = get_tier_config(TierRank.BRONZE)
        profile = UserArenaProfile(
            user_id=current_user.id,
            tier=TierRank.BRONZE.value,
            sub_tier=initial_config.sub_tiers,
            stars=0,
            protection_remaining=initial_config.protection_count,
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

    # 获取段位配置
    tier = tier_from_string(profile.tier)
    config = get_tier_config(tier)

    # 构建响应
    response = TierInfoResponse(
        tier=profile.tier,
        tier_name=config.name,
        sub_tier=profile.sub_tier,
        sub_tier_name=get_sub_tier_name(profile.sub_tier),
        full_name=get_full_tier_name(tier, profile.sub_tier),
        stars=profile.stars,
        stars_needed=config.stars_per_tier if tier != TierRank.KING else 0,
        protection_remaining=profile.protection_remaining,
        color=config.color,
        icon=config.icon,
        highest_tier=profile.highest_tier,
        highest_sub_tier=profile.highest_sub_tier,
        highest_full_name=get_full_tier_name(
            tier_from_string(profile.highest_tier),
            profile.highest_sub_tier or 1
        ) if profile.highest_tier else None,
    )

    return response


@router.get("/profile/{course_id}", response_model=TierInfoResponse)
async def get_tier_info(
    course_id: int,
    db: db_dependency,
    current_user: auth_dependency,
):
    """
    获取用户在指定课程的段位信息

    如果用户没有段位Profile，会自动创建一个初始段位
    """
    # 检查课程是否存在
    course_result = await db.execute(
        select(Course).where(Course.id == course_id)
    )
    course = course_result.scalar_one_or_none()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course {course_id} not found"
        )

    # 获取或创建用户段位Profile (全局，不关联课程)
    result = await db.execute(
        select(UserArenaProfile).where(
            UserArenaProfile.user_id == current_user.id,
        )
    )
    profile = result.scalar_one_or_none()

    if not profile:
        # 创建初始段位Profile
        initial_config = get_tier_config(TierRank.BRONZE)
        profile = UserArenaProfile(
            user_id=current_user.id,
            tier=TierRank.BRONZE.value,
            sub_tier=initial_config.sub_tiers,  # IV (最低)
            stars=0,
            protection_remaining=initial_config.protection_count,
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

    # 获取段位配置
    tier = tier_from_string(profile.tier)
    config = get_tier_config(tier)

    # 构建响应
    response = TierInfoResponse(
        tier=profile.tier,
        tier_name=config.name,
        sub_tier=profile.sub_tier,
        sub_tier_name=get_sub_tier_name(profile.sub_tier),
        full_name=get_full_tier_name(tier, profile.sub_tier),
        stars=profile.stars,
        stars_needed=config.stars_per_tier if tier != TierRank.KING else 0,
        protection_remaining=profile.protection_remaining,
        color=config.color,
        icon=config.icon,
        highest_tier=profile.highest_tier,
        highest_sub_tier=profile.highest_sub_tier,
        highest_full_name=get_full_tier_name(
            tier_from_string(profile.highest_tier),
            profile.highest_sub_tier or 1
        ) if profile.highest_tier else None,
    )

    return response


@router.post("/profile/{course_id}/stars", response_model=UpdateStarsResponse)
async def update_stars(
    course_id: int,
    request: UpdateStarsRequest,
    db: db_dependency,
    current_user: auth_dependency,
):
    """
    更新用户星星数

    可以直接指定星星变化量，或者通过正确率和难度自动计算
    """
    # 获取用户段位Profile (全局，不关联课程)
    result = await db.execute(
        select(UserArenaProfile).where(
            UserArenaProfile.user_id == current_user.id,
        )
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User tier profile not found"
        )

    tier = tier_from_string(profile.tier)

    # 记录变化前的状态
    tier_before = profile.tier
    sub_tier_before = profile.sub_tier
    stars_before = profile.stars

    # 计算星星变化
    if request.accuracy is not None and request.difficulty is not None:
        # 使用正确率和难度计算
        stars_change = tier_service.calculate_stars_earned(
            accuracy=request.accuracy,
            difficulty=request.difficulty,
        )
    else:
        # 使用指定的变化量
        stars_change = request.stars_change

    # 更新星星
    if stars_change >= 0:
        result = tier_service.add_stars(
            tier=tier,
            sub_tier=profile.sub_tier,
            current_stars=profile.stars,
            stars_earned=stars_change,
        )
    else:
        result = tier_service.remove_stars(
            tier=tier,
            sub_tier=profile.sub_tier,
            current_stars=profile.stars,
            stars_lost=abs(stars_change),
            protection_remaining=profile.protection_remaining,
        )

    # 更新Profile
    new_tier = result.tier
    new_sub_tier = result.sub_tier
    new_stars = result.stars

    profile.tier = new_tier.value
    profile.sub_tier = new_sub_tier
    profile.stars = new_stars

    # 更新保护次数
    if result.used_protection:
        profile.protection_remaining = result.protection_remaining
    elif result.promoted or result.demoted:
        # 晋级或降级时重置保护次数
        new_config = get_tier_config(new_tier)
        profile.protection_remaining = new_config.protection_count

    # 更新历史最高段位
    if result.promoted:
        new_tier_order = get_tier_order(new_tier)
        old_highest_tier = tier_from_string(profile.highest_tier) if profile.highest_tier else None
        old_highest_order = get_tier_order(old_highest_tier) if old_highest_tier else -1

        if new_tier_order > old_highest_order:
            profile.highest_tier = new_tier.value
            profile.highest_sub_tier = new_sub_tier
        elif new_tier_order == old_highest_order and new_sub_tier < (profile.highest_sub_tier or 5):
            profile.highest_sub_tier = new_sub_tier

    # 记录段位变化交易
    tier_tx_service = TierTransactionService(db)
    await tier_tx_service.record_transaction(
        user_id=current_user.id,
        course_id=course_id,
        tier_before=tier_before,
        sub_tier_before=sub_tier_before,
        stars_before=stars_before,
        tier_after=new_tier.value,
        sub_tier_after=new_sub_tier,
        stars_after=new_stars,
        stars_change=stars_change,
        promoted=result.promoted,
        demoted=result.demoted,
        used_protection=result.used_protection,
        protection_remaining=profile.protection_remaining,
        source="arena_challenge",
        description=_generate_tier_message(result, stars_change),
    )

    await db.commit()
    await db.refresh(profile)

    # 生成消息
    message = _generate_tier_message(result, stars_change)

    return UpdateStarsResponse(
        tier=profile.tier,
        sub_tier=profile.sub_tier,
        stars=profile.stars,
        stars_change=stars_change,
        promoted=result.promoted,
        demoted=result.demoted,
        used_protection=result.used_protection,
        protection_remaining=profile.protection_remaining,
        full_name=get_full_tier_name(new_tier, new_sub_tier),
        message=message,
    )


# ============================================
# 段位交易记录 API
# ============================================

class TierTransactionListResponse(BaseModel):
    """段位交易记录列表响应"""
    transactions: list[dict]
    total: int


@router.get("/transactions", response_model=TierTransactionListResponse)
async def get_tier_transactions(
    current_user: auth_dependency,
    db: db_dependency,
    course_id: Optional[int] = Query(None, description="课程ID，不传则返回所有课程"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """获取用户段位变化历史记录"""
    tier_tx_service = TierTransactionService(db)
    result = await tier_tx_service.get_transactions(
        user_id=current_user.id,
        course_id=course_id,
        limit=limit,
        offset=offset,
    )
    return TierTransactionListResponse(**result)


def _generate_tier_message(result: TierUpdateResult, stars_change: int) -> str:
    """生成段位变化消息"""
    if result.promoted:
        new_tier = result.tier
        if new_tier == TierRank.KING:
            return "🎉 恭喜晋升王者段位！"
        return f"🎉 恭喜晋升到{get_full_tier_name(new_tier, result.sub_tier)}！"

    if result.demoted:
        new_tier = result.tier
        return f"📉 降级到{get_full_tier_name(new_tier, result.sub_tier)}"

    if result.used_protection:
        return f"🛡️ 段位保护生效，剩余{result.protection_remaining}次保护机会"

    if stars_change > 0:
        return f"⭐ 获得{stars_change}颗星星"
    elif stars_change < 0:
        return f"💫 失去{abs(stars_change)}颗星星"
    else:
        return "星星数无变化"


logger = logging.getLogger(__name__)