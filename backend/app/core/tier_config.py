"""
王者荣耀风格段位配置

段位从低到高：
- 青铜 (Bronze): IV, III, II, I - 每个小段位3星
- 白银 (Silver): IV, III, II, I - 每个小段位3星
- 黄金 (Gold): IV, III, II, I - 每个小段位4星
- 铂金 (Platinum): V, IV, III, II, I - 每个小段位4星
- 钻石 (Diamond): V, IV, III, II, I - 每个小段位5星
- 星耀 (Master): V, IV, III, II, I - 每个小段位5星
- 王者 (King): 无限星星，按星星数排名
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional


class TierRank(str, Enum):
    """段位等级枚举"""
    BRONZE = "bronze"       # 青铜
    SILVER = "silver"       # 白银
    GOLD = "gold"           # 黄金
    PLATINUM = "platinum"   # 铂金
    DIAMOND = "diamond"     # 钻石
    MASTER = "master"       # 星耀
    KING = "king"           # 王者


@dataclass(frozen=True)
class TierConfig:
    """段位配置"""
    rank: TierRank
    name: str                # 中文名称
    sub_tiers: int           # 小段位数量 (4表示IV,III,II,I; 5表示V,IV,III,II,I)
    stars_per_tier: int      # 每个小段位需要的星星数
    color: str               # 颜色代码
    icon: str                # 图标标识
    protection_count: int    # 段位保护次数（降级保护）


# 段位配置表
TIER_CONFIGS: Dict[TierRank, TierConfig] = {
    TierRank.BRONZE: TierConfig(
        rank=TierRank.BRONZE,
        name="青铜",
        sub_tiers=4,         # IV, III, II, I
        stars_per_tier=3,
        color="#CD7F32",     # 青铜色
        icon="bronze",
        protection_count=3,  # 青铜有3次保护
    ),
    TierRank.SILVER: TierConfig(
        rank=TierRank.SILVER,
        name="白银",
        sub_tiers=4,         # IV, III, II, I
        stars_per_tier=3,
        color="#C0C0C0",     # 银色
        icon="silver",
        protection_count=3,
    ),
    TierRank.GOLD: TierConfig(
        rank=TierRank.GOLD,
        name="黄金",
        sub_tiers=4,         # IV, III, II, I
        stars_per_tier=4,
        color="#FFD700",     # 金色
        icon="gold",
        protection_count=2,
    ),
    TierRank.PLATINUM: TierConfig(
        rank=TierRank.PLATINUM,
        name="铂金",
        sub_tiers=5,         # V, IV, III, II, I
        stars_per_tier=4,
        color="#E5E4E2",     # 铂金色
        icon="platinum",
        protection_count=2,
    ),
    TierRank.DIAMOND: TierConfig(
        rank=TierRank.DIAMOND,
        name="钻石",
        sub_tiers=5,         # V, IV, III, II, I
        stars_per_tier=5,
        color="#B9F2FF",     # 钻石色
        icon="diamond",
        protection_count=1,
    ),
    TierRank.MASTER: TierConfig(
        rank=TierRank.MASTER,
        name="星耀",
        sub_tiers=5,         # V, IV, III, II, I
        stars_per_tier=5,
        color="#9370DB",     # 紫色
        icon="master",
        protection_count=1,
    ),
    TierRank.KING: TierConfig(
        rank=TierRank.KING,
        name="王者",
        sub_tiers=0,         # 王者无小段位
        stars_per_tier=0,     # 王者星星无限累计
        color="#FF4500",     # 橙红色
        icon="king",
        protection_count=0,  # 王者无保护
    ),
}


def get_tier_config(tier: TierRank) -> TierConfig:
    """获取段位配置"""
    return TIER_CONFIGS[tier]


def get_tier_order(tier: TierRank) -> int:
    """获取段位顺序（用于比较）"""
    order = {
        TierRank.BRONZE: 0,
        TierRank.SILVER: 1,
        TierRank.GOLD: 2,
        TierRank.PLATINUM: 3,
        TierRank.DIAMOND: 4,
        TierRank.MASTER: 5,
        TierRank.KING: 6,
    }
    return order[tier]


def get_next_tier(tier: TierRank) -> Optional[TierRank]:
    """获取下一个段位"""
    order_to_tier = {
        0: TierRank.BRONZE,
        1: TierRank.SILVER,
        2: TierRank.GOLD,
        3: TierRank.PLATINUM,
        4: TierRank.DIAMOND,
        5: TierRank.MASTER,
        6: TierRank.KING,
    }
    current_order = get_tier_order(tier)
    next_order = current_order + 1
    return order_to_tier.get(next_order)


def get_previous_tier(tier: TierRank) -> Optional[TierRank]:
    """获取上一个段位"""
    order_to_tier = {
        0: TierRank.BRONZE,
        1: TierRank.SILVER,
        2: TierRank.GOLD,
        3: TierRank.PLATINUM,
        4: TierRank.DIAMOND,
        5: TierRank.MASTER,
        6: TierRank.KING,
    }
    current_order = get_tier_order(tier)
    prev_order = current_order - 1
    return order_to_tier.get(prev_order)


def get_sub_tier_name(sub_tier: int) -> str:
    """获取小段位名称（罗马数字）"""
    roman_numerals = {
        1: "I",
        2: "II",
        3: "III",
        4: "IV",
        5: "V",
    }
    return roman_numerals.get(sub_tier, str(sub_tier))


def get_full_tier_name(tier: TierRank, sub_tier: int) -> str:
    """获取完整段位名称"""
    config = get_tier_config(tier)
    if tier == TierRank.KING:
        return f"{config.name}"
    return f"{config.name}{get_sub_tier_name(sub_tier)}"


def get_all_tiers() -> List[TierConfig]:
    """获取所有段位配置（按顺序）"""
    return [
        TIER_CONFIGS[TierRank.BRONZE],
        TIER_CONFIGS[TierRank.SILVER],
        TIER_CONFIGS[TierRank.GOLD],
        TIER_CONFIGS[TierRank.PLATINUM],
        TIER_CONFIGS[TierRank.DIAMOND],
        TIER_CONFIGS[TierRank.MASTER],
        TIER_CONFIGS[TierRank.KING],
    ]


def tier_from_string(tier_str: str) -> TierRank:
    """从字符串转换段位"""
    try:
        return TierRank(tier_str.lower())
    except ValueError:
        return TierRank.BRONZE  # 默认返回青铜
