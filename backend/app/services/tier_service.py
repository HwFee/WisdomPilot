"""
段位服务层 - 王者荣耀风格段位系统

处理星星增减、晋级降级、段位保护等核心逻辑
"""

from dataclasses import dataclass
from typing import Optional
from app.core.tier_config import (
    TierRank,
    get_tier_config,
    get_next_tier,
    get_previous_tier,
    get_tier_order,
    tier_from_string,
)


@dataclass
class TierUpdateResult:
    """段位更新结果"""
    tier: TierRank
    sub_tier: int
    stars: int
    promoted: bool = False
    demoted: bool = False
    used_protection: bool = False
    protection_remaining: int = 0


class TierService:
    """段位服务类"""

    def add_stars(
        self,
        tier: TierRank,
        sub_tier: int,
        current_stars: int,
        stars_earned: int,
    ) -> TierUpdateResult:
        """
        增加星星（胜利时调用）

        Args:
            tier: 当前段位
            sub_tier: 当前小段位 (1=I, 2=II, 3=III, 4=IV, 5=V)
            current_stars: 当前星星数
            stars_earned: 获得的星星数

        Returns:
            TierUpdateResult 包含新段位信息
        """
        config = get_tier_config(tier)

        # 王者段位特殊处理：星星无限累计
        if tier == TierRank.KING:
            new_stars = current_stars + stars_earned
            return TierUpdateResult(
                tier=TierRank.KING,
                sub_tier=0,
                stars=new_stars,
            )

        # 计算新星星数
        new_stars = current_stars + stars_earned
        stars_needed = config.stars_per_tier

        # 检查是否晋级
        if new_stars >= stars_needed:
            return self._handle_promotion(tier, sub_tier, new_stars, stars_needed)

        # 未晋级，保持当前状态
        return TierUpdateResult(
            tier=tier,
            sub_tier=sub_tier,
            stars=new_stars,
        )

    def _handle_promotion(
        self,
        tier: TierRank,
        sub_tier: int,
        excess_stars: int,
        stars_needed: int,
    ) -> TierUpdateResult:
        """处理晋级逻辑"""
        config = get_tier_config(tier)

        # 检查是否是小段位晋级还是大段位晋级
        if sub_tier > 1:
            # 小段位晋级（如青铜IV -> 青铜III）
            new_sub_tier = sub_tier - 1
            return TierUpdateResult(
                tier=tier,
                sub_tier=new_sub_tier,
                stars=0,  # 晋级后星星重置为0
                promoted=True,
            )
        else:
            # 大段位晋级（如青铜I -> 白银IV）
            next_tier = get_next_tier(tier)
            if next_tier is None:
                # 已经是最高段位（理论上不会到达这里，因为王者特殊处理）
                return TierUpdateResult(
                    tier=tier,
                    sub_tier=sub_tier,
                    stars=excess_stars,
                )

            next_config = get_tier_config(next_tier)

            # 新段位从最低小段位开始
            if next_tier == TierRank.KING:
                # 晋级到王者
                return TierUpdateResult(
                    tier=TierRank.KING,
                    sub_tier=0,
                    stars=1,  # 王者第一颗星
                    promoted=True,
                )

            new_sub_tier = next_config.sub_tiers  # 最低小段位（如IV或V）
            return TierUpdateResult(
                tier=next_tier,
                sub_tier=new_sub_tier,
                stars=0,  # 晋级后星星重置为0
                promoted=True,
            )

    def remove_stars(
        self,
        tier: TierRank,
        sub_tier: int,
        current_stars: int,
        stars_lost: int,
        protection_remaining: int = 0,
    ) -> TierUpdateResult:
        """
        减少星星（失败时调用）

        Args:
            tier: 当前段位
            sub_tier: 当前小段位
            current_stars: 当前星星数
            stars_lost: 失去的星星数
            protection_remaining: 剩余保护次数

        Returns:
            TierUpdateResult 包含新段位信息
        """
        # 青铜IV 0星是最低，不会降
        if tier == TierRank.BRONZE and sub_tier == 4 and current_stars == 0:
            return TierUpdateResult(
                tier=TierRank.BRONZE,
                sub_tier=4,
                stars=0,
                protection_remaining=protection_remaining,
            )

        # 王者段位：星星可以减少但不能降级
        if tier == TierRank.KING:
            new_stars = max(0, current_stars - stars_lost)
            return TierUpdateResult(
                tier=TierRank.KING,
                sub_tier=0,
                stars=new_stars,
                protection_remaining=0,
            )

        # 计算新星星数
        new_stars = current_stars - stars_lost

        # 检查是否降级
        if new_stars < 0:
            # 检查段位保护
            if protection_remaining > 0:
                # 使用保护
                return TierUpdateResult(
                    tier=tier,
                    sub_tier=sub_tier,
                    stars=0,
                    used_protection=True,
                    protection_remaining=protection_remaining - 1,
                )

            # 没有保护，执行降级
            return self._handle_demotion(tier, sub_tier, new_stars, protection_remaining)

        # 未降级，保持当前状态
        return TierUpdateResult(
            tier=tier,
            sub_tier=sub_tier,
            stars=new_stars,
            protection_remaining=protection_remaining,
        )

    def _handle_demotion(
        self,
        tier: TierRank,
        sub_tier: int,
        negative_stars: int,
        protection_remaining: int,
    ) -> TierUpdateResult:
        """处理降级逻辑"""
        config = get_tier_config(tier)

        # 检查是否是小段位降级还是大段位降级
        if sub_tier < config.sub_tiers:
            # 小段位降级（如青铜III -> 青铜IV）
            new_sub_tier = sub_tier + 1
            # 降级后星星 = 该段位满星 - |负星星|
            new_stars = config.stars_per_tier + negative_stars
            return TierUpdateResult(
                tier=tier,
                sub_tier=new_sub_tier,
                stars=max(0, new_stars),
                demoted=True,
                protection_remaining=protection_remaining,
            )
        else:
            # 大段位降级（如白银IV -> 青铜I）
            prev_tier = get_previous_tier(tier)
            if prev_tier is None:
                # 已经是最低段位（青铜IV）
                return TierUpdateResult(
                    tier=tier,
                    sub_tier=sub_tier,
                    stars=0,
                    protection_remaining=protection_remaining,
                )

            prev_config = get_tier_config(prev_tier)

            # 降到上一段位的最高小段位
            new_sub_tier = 1  # I (最高小段位)
            # 星星 = 上一段位满星 - |负星星|
            new_stars = prev_config.stars_per_tier + negative_stars

            # 重置保护次数
            new_protection = prev_config.protection_count

            return TierUpdateResult(
                tier=prev_tier,
                sub_tier=new_sub_tier,
                stars=max(0, new_stars),
                demoted=True,
                protection_remaining=new_protection,
            )

    def calculate_stars_earned(
        self,
        accuracy: float,
        difficulty: int,
    ) -> int:
        """
        根据正确率和难度计算获得的星星数

        Args:
            accuracy: 正确率 (0.0 - 1.0)
            difficulty: 难度等级 (1-5)

        Returns:
            星星数（正数=获得，负数=失去）
        """
        # 基础星星计算（基于正确率）
        if accuracy >= 0.90:
            base_stars = 2
        elif accuracy >= 0.70:
            base_stars = 1
        elif accuracy >= 0.50:
            base_stars = 0
        elif accuracy >= 0.30:
            base_stars = -1
        else:
            base_stars = -2

        # 难度加成
        difficulty_bonus = 0
        if difficulty >= 5 and accuracy >= 0.90:
            difficulty_bonus = 1  # 高难度+高正确率额外奖励
        elif difficulty <= 2 and accuracy < 0.50:
            difficulty_bonus = -1  # 低难度+低正确率额外惩罚

        return base_stars + difficulty_bonus

    def has_protection(self, tier: TierRank) -> bool:
        """
        检查是否有段位保护

        Args:
            tier: 段位

        Returns:
            是否有保护
        """
        config = get_tier_config(tier)
        return config.protection_count > 0

    def get_protection_count(self, tier: TierRank) -> int:
        """
        获取段位保护次数

        Args:
            tier: 段位

        Returns:
            保护次数
        """
        config = get_tier_config(tier)
        return config.protection_count

    def update_highest_tier(
        self,
        current_highest_tier: Optional[str],
        current_highest_sub_tier: Optional[int],
        new_tier: TierRank,
        new_sub_tier: int,
    ) -> tuple[TierRank, int]:
        """
        更新历史最高段位

        Args:
            current_highest_tier: 当前历史最高段位
            current_highest_sub_tier: 当前历史最高小段位
            new_tier: 新段位
            new_sub_tier: 新小段位

        Returns:
            (最高段位, 最高小段位)
        """
        if current_highest_tier is None:
            return (new_tier, new_sub_tier)

        old_tier = tier_from_string(current_highest_tier)
        old_order = get_tier_order(old_tier)
        new_order = get_tier_order(new_tier)

        if new_order > old_order:
            return (new_tier, new_sub_tier)
        elif new_order == old_order and new_sub_tier < (current_highest_sub_tier or 5):
            # 同一段位，小段位数字越小越高（I > II > III > IV > V）
            return (new_tier, new_sub_tier)

        return (old_tier, current_highest_sub_tier or 1)


# 单例实例
tier_service = TierService()
