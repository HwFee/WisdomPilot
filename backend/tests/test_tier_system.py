"""
王者荣耀风格段位系统测试

TDD: 先写测试，再实现功能
"""

import pytest
from app.core.tier_config import (
    TierRank,
    TierConfig,
    get_tier_config,
    get_next_tier,
    get_previous_tier,
    get_tier_order,
    get_sub_tier_name,
    get_full_tier_name,
    tier_from_string,
)


class TestTierConfig:
    """测试段位配置"""

    def test_tier_order_from_low_to_high(self):
        """测试段位顺序从低到高"""
        expected_order = [
            TierRank.BRONZE,
            TierRank.SILVER,
            TierRank.GOLD,
            TierRank.PLATINUM,
            TierRank.DIAMOND,
            TierRank.MASTER,
            TierRank.KING,
        ]
        assert get_tier_order(TierRank.BRONZE) == 0
        assert get_tier_order(TierRank.SILVER) == 1
        assert get_tier_order(TierRank.GOLD) == 2
        assert get_tier_order(TierRank.PLATINUM) == 3
        assert get_tier_order(TierRank.DIAMOND) == 4
        assert get_tier_order(TierRank.MASTER) == 5
        assert get_tier_order(TierRank.KING) == 6

    def test_bronze_config(self):
        """测试青铜段位配置"""
        config = get_tier_config(TierRank.BRONZE)
        assert config.rank == TierRank.BRONZE
        assert config.name == "青铜"
        assert config.sub_tiers == 4  # IV, III, II, I
        assert config.stars_per_tier == 3
        assert config.protection_count == 3

    def test_diamond_config(self):
        """测试钻石段位配置"""
        config = get_tier_config(TierRank.DIAMOND)
        assert config.rank == TierRank.DIAMOND
        assert config.name == "钻石"
        assert config.sub_tiers == 5  # V, IV, III, II, I
        assert config.stars_per_tier == 5
        assert config.protection_count == 1

    def test_master_config(self):
        """测试星耀段位配置"""
        config = get_tier_config(TierRank.MASTER)
        assert config.rank == TierRank.MASTER
        assert config.name == "星耀"
        assert config.sub_tiers == 5
        assert config.stars_per_tier == 5
        assert config.protection_count == 1

    def test_king_config(self):
        """测试王者段位配置"""
        config = get_tier_config(TierRank.KING)
        assert config.rank == TierRank.KING
        assert config.name == "王者"
        assert config.sub_tiers == 0  # 无小段位
        assert config.stars_per_tier == 0  # 无限星星
        assert config.protection_count == 0

    def test_get_next_tier(self):
        """测试获取下一段位"""
        assert get_next_tier(TierRank.BRONZE) == TierRank.SILVER
        assert get_next_tier(TierRank.SILVER) == TierRank.GOLD
        assert get_next_tier(TierRank.GOLD) == TierRank.PLATINUM
        assert get_next_tier(TierRank.PLATINUM) == TierRank.DIAMOND
        assert get_next_tier(TierRank.DIAMOND) == TierRank.MASTER
        assert get_next_tier(TierRank.MASTER) == TierRank.KING
        assert get_next_tier(TierRank.KING) is None  # 王者无下一级

    def test_get_previous_tier(self):
        """测试获取上一段位"""
        assert get_previous_tier(TierRank.BRONZE) is None  # 青铜无上一级
        assert get_previous_tier(TierRank.SILVER) == TierRank.BRONZE
        assert get_previous_tier(TierRank.GOLD) == TierRank.SILVER
        assert get_previous_tier(TierRank.MASTER) == TierRank.DIAMOND
        assert get_previous_tier(TierRank.KING) == TierRank.MASTER

    def test_sub_tier_names(self):
        """测试小段位名称"""
        assert get_sub_tier_name(1) == "I"
        assert get_sub_tier_name(2) == "II"
        assert get_sub_tier_name(3) == "III"
        assert get_sub_tier_name(4) == "IV"
        assert get_sub_tier_name(5) == "V"

    def test_full_tier_name(self):
        """测试完整段位名称"""
        assert get_full_tier_name(TierRank.BRONZE, 4) == "青铜IV"
        assert get_full_tier_name(TierRank.BRONZE, 1) == "青铜I"
        assert get_full_tier_name(TierRank.GOLD, 3) == "黄金III"
        assert get_full_tier_name(TierRank.DIAMOND, 5) == "钻石V"
        assert get_full_tier_name(TierRank.KING, 0) == "王者"  # 王者无小段位

    def test_tier_from_string(self):
        """测试从字符串转换段位"""
        assert tier_from_string("bronze") == TierRank.BRONZE
        assert tier_from_string("BRONZE") == TierRank.BRONZE
        assert tier_from_string("Silver") == TierRank.SILVER
        assert tier_from_string("invalid") == TierRank.BRONZE  # 无效返回默认


class TestTierService:
    """测试段位服务层逻辑"""

    @pytest.fixture
    def tier_service(self):
        from app.services.tier_service import TierService
        return TierService()

    def test_add_stars_promotion_within_tier(self, tier_service):
        """测试小段位内升级（青铜IV 3星 -> +1星 -> 青铜III 0星）"""
        result = tier_service.add_stars(
            tier=TierRank.BRONZE,
            sub_tier=4,  # IV
            current_stars=3,
            stars_earned=1,
        )
        assert result.tier == TierRank.BRONZE
        assert result.sub_tier == 3  # 升到III
        assert result.stars == 0
        assert result.promoted is True

    def test_add_stars_major_promotion(self, tier_service):
        """测试大段位晋级（青铜I 3星 -> +1星 -> 白银IV 0星）"""
        result = tier_service.add_stars(
            tier=TierRank.BRONZE,
            sub_tier=1,  # I (最高小段位)
            current_stars=3,  # 满星
            stars_earned=1,
        )
        assert result.tier == TierRank.SILVER
        assert result.sub_tier == 4  # 新段位从最低开始
        assert result.stars == 0
        assert result.promoted is True

    def test_add_stars_to_master(self, tier_service):
        """测试晋级到星耀"""
        result = tier_service.add_stars(
            tier=TierRank.DIAMOND,
            sub_tier=1,  # I
            current_stars=5,  # 满星
            stars_earned=1,
        )
        assert result.tier == TierRank.MASTER
        assert result.sub_tier == 5
        assert result.stars == 0
        assert result.promoted is True

    def test_add_stars_to_king(self, tier_service):
        """测试晋级到王者"""
        result = tier_service.add_stars(
            tier=TierRank.MASTER,
            sub_tier=1,  # I
            current_stars=5,  # 满星
            stars_earned=1,
        )
        assert result.tier == TierRank.KING
        assert result.sub_tier == 0
        assert result.stars == 1  # 王者累计星星
        assert result.promoted is True

    def test_add_stars_king_accumulates(self, tier_service):
        """测试王者段位星星累计"""
        result = tier_service.add_stars(
            tier=TierRank.KING,
            sub_tier=0,
            current_stars=10,
            stars_earned=2,
        )
        assert result.tier == TierRank.KING
        assert result.sub_tier == 0
        assert result.stars == 12
        assert result.promoted is False

    def test_remove_stars_demotion_within_tier(self, tier_service):
        """测试小段位内降星"""
        result = tier_service.remove_stars(
            tier=TierRank.SILVER,
            sub_tier=2,  # II
            current_stars=0,
            stars_lost=1,
        )
        assert result.tier == TierRank.SILVER
        assert result.sub_tier == 3  # 降到III
        assert result.stars == 2  # 3-1=2
        assert result.demoted is True

    def test_remove_stars_major_demotion(self, tier_service):
        """测试大段位降级（白银IV 0星 -> -1星 -> 青铜I 2星）"""
        result = tier_service.remove_stars(
            tier=TierRank.SILVER,
            sub_tier=4,  # IV (最低小段位)
            current_stars=0,
            stars_lost=1,
        )
        assert result.tier == TierRank.BRONZE
        assert result.sub_tier == 1  # 降到上一段位的最高小段
        assert result.stars == 2  # 3-1=2
        assert result.demoted is True

    def test_remove_stars_bronze_cannot_demote(self, tier_service):
        """测试青铜段位不会继续降级"""
        result = tier_service.remove_stars(
            tier=TierRank.BRONZE,
            sub_tier=4,  # IV (最低)
            current_stars=0,
            stars_lost=1,
        )
        # 青铜IV 0星是最低，不会继续降
        assert result.tier == TierRank.BRONZE
        assert result.sub_tier == 4
        assert result.stars == 0
        assert result.demoted is False

    def test_remove_stars_with_protection(self, tier_service):
        """测试段位保护"""
        result = tier_service.remove_stars(
            tier=TierRank.GOLD,
            sub_tier=4,  # IV
            current_stars=0,
            stars_lost=1,
            protection_remaining=2,
        )
        # 使用保护，不降级
        assert result.tier == TierRank.GOLD
        assert result.sub_tier == 4
        assert result.stars == 0
        assert result.demoted is False
        assert result.used_protection is True
        assert result.protection_remaining == 1

    def test_calculate_stars_earned_high_accuracy(self, tier_service):
        """测试高正确率获得2星"""
        stars = tier_service.calculate_stars_earned(accuracy=0.90, difficulty=3)
        assert stars == 2

    def test_calculate_stars_earned_medium_accuracy(self, tier_service):
        """测试中等正确率获得1星"""
        stars = tier_service.calculate_stars_earned(accuracy=0.75, difficulty=3)
        assert stars == 1

    def test_calculate_stars_earned_low_accuracy(self, tier_service):
        """测试低正确率无变化"""
        stars = tier_service.calculate_stars_earned(accuracy=0.55, difficulty=3)
        assert stars == 0

    def test_calculate_stars_earned_fail(self, tier_service):
        """测试失败扣除星星"""
        stars = tier_service.calculate_stars_earned(accuracy=0.30, difficulty=3)
        assert stars == -1

    def test_calculate_stars_high_difficulty_bonus(self, tier_service):
        """测试高难度奖励"""
        # 高难度+高正确率 = 3星
        stars = tier_service.calculate_stars_earned(accuracy=0.95, difficulty=5)
        assert stars == 3

    def test_has_protection_bronze(self, tier_service):
        """测试青铜有保护"""
        assert tier_service.has_protection(TierRank.BRONZE) is True

    def test_has_protection_king(self, tier_service):
        """测试王者无保护"""
        assert tier_service.has_protection(TierRank.KING) is False


class TestTierIntegration:
    """测试段位与用户Profile集成"""

    # 注意：Profile 集成测试需要完整的数据库设置（用户、课程存在）
    # 这里我们只测试服务层逻辑，Profile 数据库集成测试放在 test_arena.py 中

    def test_tier_service_singleton(self):
        """测试段位服务单例"""
        from app.services.tier_service import tier_service

        assert tier_service is not None
        assert hasattr(tier_service, 'add_stars')
        assert hasattr(tier_service, 'remove_stars')
        assert hasattr(tier_service, 'calculate_stars_earned')
