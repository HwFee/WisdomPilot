"""调度层测试（§3.5 P-06 间隔重复调度 / P-08 难度自适应）。

- P-06 due_for_review（service.py）：阈值过滤 + 升序排序 / 空集
- P-06 主任务分发含复习任务分支（router.py build_main_task）：
  到期复习优先 / 无到期回退最低轴
- P-08 difficulty_delta（service.py 纯函数）：升档 / 降档 / 不变 / 无数据
- P-08 审查室难度选择（router.py _next_review_session）：
  高准确率升档 / 低准确率降档 / 中等不变 / 无记录不调整
- P-08 竞技场难度选择（router.py _today_challenge / _pick_by_difficulty）：
  攻克率升降档 / 无记录基准 / 目标难度无挑战回退
- §4 rank_delta（service.rank_delta_7d）：近 7 天排名变化的诚实重放 / 守卫 /
  arena/home 端点暴露
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.auth.models import User
from app.training import router, service
from app.training.models import (
    DeckAbilityAxis,
    DeckArenaAttempt,
    DeckArenaChallenge,
    DeckArenaRating,
    DeckKnowledgePoint,
    DeckReviewAttempt,
    DeckUserMastery,
)
from app.training.seed import seed_deck


async def _place_user(db, user_id: str, weakest_kp: str | None = None) -> None:
    """为测试用户写全部知识点的定级事件（答对），可选再写一条最弱点答错事件。"""
    kps = (await db.execute(select(DeckKnowledgePoint))).scalars().all()
    for kp in kps:
        await service.record_mastery_event(db, user_id, kp.id, "placement", True)
    if weakest_kp:
        kp = (
            await db.execute(
                select(DeckKnowledgePoint).where(DeckKnowledgePoint.name == weakest_kp)
            )
        ).scalar_one()
        await service.record_mastery_event(db, user_id, kp.id, "review_gym", False)
    await db.commit()


async def _set_axes(db, user_id: str, levels: dict[str, int]) -> None:
    """设置三轴经验值使等级等于 levels（等级 = 1 + xp // 400）。"""
    for axis, level in levels.items():
        db.add(DeckAbilityAxis(user_id=user_id, axis=axis, xp=(level - 1) * 400))
    await db.commit()


async def _mastery_rows(db, user_id: str, pairs: list[tuple[str, float]]) -> None:
    """按 (知识点名, p_l) 直接写掌握度缓存行（用于控制到期状态）。"""
    for name, p_l in pairs:
        kp = (
            await db.execute(
                select(DeckKnowledgePoint).where(DeckKnowledgePoint.name == name)
            )
        ).scalar_one()
        db.add(
            DeckUserMastery(user_id=user_id, kp_id=kp.id, p_l=p_l, level="初识")
        )
    await db.commit()


def _review_attempt(user_id: str, session_id: str, accuracy: float) -> DeckReviewAttempt:
    """构造一条审查提交记录（verdict 只带 accuracy，供难度自适应统计）。"""
    return DeckReviewAttempt(
        user_id=user_id,
        session_id=session_id,
        marks=[],
        verdict={"hits": [], "missed": [], "false_alarms": [], "score": 0, "accuracy": accuracy},
    )


def _arena_attempt(user_id: str, solved: int) -> DeckArenaAttempt:
    return DeckArenaAttempt(
        user_id=user_id, challenge_id="DEBUG-0091", solved=solved, passed=5 if solved else 0, total=5
    )


async def _all_challenges(db) -> list[DeckArenaChallenge]:
    rows = (
        await db.execute(select(DeckArenaChallenge).order_by(DeckArenaChallenge.id))
    ).scalars().all()
    return list(rows)


# ── P-06 到期复习知识点筛选 ──────────────────────────────


class TestDueForReview:
    async def test_due_filters_below_threshold_and_sorts(self, db_session, auth_user):
        """阈值过滤（0.6 不包含）+ 按 p_l 升序：最危险的在最前。"""
        await seed_deck(db_session)
        await _mastery_rows(
            db_session,
            auth_user.id,
            [
                ("边界条件处理", 0.7),   # 高于阈值：不出现在到期列表
                ("指针的内存布局", 0.3),
                ("递归出口设计", 0.5),
                ("安全漏洞模式", 0.6),   # 恰好等于阈值：不视为到期（< 0.6）
            ],
        )
        due = await service.due_for_review(db_session, auth_user.id)
        assert [d["name"] for d in due] == ["指针的内存布局", "递归出口设计"]
        assert due[0]["p_l"] == 0.3

    async def test_due_empty_when_all_above_threshold(self, db_session, auth_user):
        """全部知识点掌握度 ≥ 阈值：不产生复习任务。"""
        await seed_deck(db_session)
        await _mastery_rows(
            db_session, auth_user.id, [("边界条件处理", 0.7), ("指针的内存布局", 0.9)]
        )
        assert await service.due_for_review(db_session, auth_user.id) == []

    async def test_due_empty_when_no_mastery(self, db_session, auth_user):
        """无掌握度记录：空列表（未定级用户由 has_placement 先拦截）。"""
        await seed_deck(db_session)
        assert await service.due_for_review(db_session, auth_user.id) == []


# ── P-06 主任务分发含复习任务 ────────────────────────────


class TestMainTaskDueReview:
    async def test_main_task_due_review(self, db_session, auth_user):
        """到期复习优先：主任务为费曼复习最到期的知识点，reason 引用记忆消退与掌握度。"""
        await seed_deck(db_session)
        await _set_axes(db_session, auth_user.id, {"review": 3, "debug": 3, "implement": 3})
        await _mastery_rows(
            db_session, auth_user.id, [("边界条件处理", 0.3), ("指针的内存布局", 0.8)]
        )
        axes = await service.get_axes(db_session, auth_user.id)
        task = await router.build_main_task(db_session, auth_user, axes)
        assert task is not None
        assert task["module"] == "tutor"
        assert "「边界条件处理」的记忆正在消退（掌握度 0.30）" in task["reason"]
        assert task["target_url"] == "/tutor?topic=边界条件处理"
        assert task["related_weakness"] == "边界条件处理"
        # 备用任务合理：不含主任务自身，且都带推荐理由
        assert task["alternates"]
        assert all(alt["id"] != task["id"] for alt in task["alternates"])
        assert all(alt["reason"] for alt in task["alternates"])

    async def test_main_task_no_due_falls_back_to_lowest_axis(self, db_session, auth_user):
        """无到期知识点：保持原最低轴分发（P-01 理由），复习分支不触发。"""
        await seed_deck(db_session)
        await _set_axes(db_session, auth_user.id, {"review": 2, "debug": 4, "implement": 4})
        await _mastery_rows(
            db_session, auth_user.id, [("边界条件处理", 0.7), ("指针的内存布局", 0.8)]
        )
        axes = await service.get_axes(db_session, auth_user.id)
        task = await router.build_main_task(db_session, auth_user, axes)
        assert task["module"] == "review-gym"
        assert "「审阅」轴是三轴最低（LV.2）" in task["reason"]
        assert "记忆正在消退" not in task["reason"]

    async def test_implement_low_still_prefers_cert(self, db_session, auth_user):
        """实现轴 < LV.3 即使存在到期知识点也优先认证（P-06 优先级低于认证入门路径）。"""
        await seed_deck(db_session)
        await _set_axes(db_session, auth_user.id, {"review": 3, "debug": 3, "implement": 2})
        await _mastery_rows(
            db_session, auth_user.id, [("边界条件处理", 0.3), ("指针的内存布局", 0.8)]
        )
        axes = await service.get_axes(db_session, auth_user.id)
        task = await router.build_main_task(db_session, auth_user, axes)
        assert task["module"] == "certification"
        assert "「实现」轴还在 LV.2" in task["reason"]


# ── P-08 难度档位纯函数 ─────────────────────────────────


class TestDifficultyDelta:
    def test_up_when_high_accuracy(self):
        """均值 ≥ 0.9 → +1 档（升档）。"""
        assert service.difficulty_delta(0.95, service.REVIEW_ADAPT_UP, service.REVIEW_ADAPT_DOWN) == 1
        assert service.difficulty_delta(0.9, service.ARENA_ADAPT_UP, service.ARENA_ADAPT_DOWN) == 1

    def test_down_when_low_accuracy(self):
        """均值 ≤ 0.4 → -1 档（降档）。"""
        assert service.difficulty_delta(0.2, service.REVIEW_ADAPT_UP, service.REVIEW_ADAPT_DOWN) == -1
        assert service.difficulty_delta(0.4, service.ARENA_ADAPT_UP, service.ARENA_ADAPT_DOWN) == -1

    def test_stable_in_between(self):
        """均值在 (0.4, 0.9) 之间 → 0（保持难度）。"""
        assert service.difficulty_delta(0.6, service.REVIEW_ADAPT_UP, service.REVIEW_ADAPT_DOWN) == 0

    def test_no_data_returns_zero(self):
        """无记录（None）→ 0（冷启动不扰动难度）。"""
        assert service.difficulty_delta(None, service.REVIEW_ADAPT_UP, service.REVIEW_ADAPT_DOWN) == 0


class TestRecentPerformanceQueries:
    async def test_review_accuracy_none_and_partial(self, db_session, auth_user):
        """审查准确率：无记录 None；不足窗口按已有记录均值。"""
        await seed_deck(db_session)
        assert await service.recent_review_accuracy(db_session, auth_user.id) is None
        db_session.add(_review_attempt(auth_user.id, "REVIEW-0247", 0.8))
        await db_session.commit()
        assert await service.recent_review_accuracy(db_session, auth_user.id) == 0.8

    async def test_arena_win_rate_values(self, db_session, auth_user):
        """竞技场攻克率：无记录 None；3 连过 1.0；3 连败 0.0。"""
        await seed_deck(db_session)
        assert await service.recent_arena_win_rate(db_session, auth_user.id) is None
        for _ in range(3):
            db_session.add(_arena_attempt(auth_user.id, 1))
        await db_session.commit()
        assert await service.recent_arena_win_rate(db_session, auth_user.id) == 1.0

        # 换新会话再测 3 连败（fixture 每测试独立建库）
        db_session.add_all(_arena_attempt(auth_user.id, 0) for _ in range(3))
        await db_session.commit()
        # 新插入 3 条覆盖窗口 → 攻克率 0.0
        assert await service.recent_arena_win_rate(db_session, auth_user.id) == 0.0


# ── P-08 审查室难度自适应（P-05 弱点匹配 + P-08 选难度）──


class TestReviewSessionDifficulty:
    async def test_high_accuracy_prefers_higher_difficulty(self, db_session, auth_user):
        """近 3 次审查全对（accuracy=1.0）→ +1 档：安全漏洞模式候选集内取更高难度关。"""
        await seed_deck(db_session)
        await _place_user(db_session, auth_user.id, weakest_kp="安全漏洞模式")
        # 在非候选关 REVIEW-0247 写 3 条全对记录（同时把它移出待选池）
        for _ in range(3):
            db_session.add(_review_attempt(auth_user.id, "REVIEW-0247", 1.0))
        await db_session.commit()
        session = await router._next_review_session(db_session, auth_user.id)
        # 弱点匹配候选：REVIEW-0250(diff3) / REVIEW-0252(diff4)；升档 → 取 diff4
        assert session.id == "REVIEW-0252"

    async def test_low_accuracy_prefers_lower_difficulty(self, db_session, auth_user):
        """近 3 次审查全错（accuracy=0.0）→ -1 档：边界条件处理候选集内取更低难度关。"""
        await seed_deck(db_session)
        await _place_user(db_session, auth_user.id, weakest_kp="边界条件处理")
        # 在 REVIEW-0250 写 3 条全错记录（把它移出待选池）
        for _ in range(3):
            db_session.add(_review_attempt(auth_user.id, "REVIEW-0250", 0.0))
        await db_session.commit()
        session = await router._next_review_session(db_session, auth_user.id)
        # 弱点匹配候选：REVIEW-0247(diff3) / REVIEW-0249(diff2)；降档 → 取 diff2
        assert session.id == "REVIEW-0249"

    async def test_mid_accuracy_keeps_weakness_priority(self, db_session, auth_user):
        """近 3 次准确率居中 → 0 档：保持 P-05 弱点优先级原行为（取首关）。"""
        await seed_deck(db_session)
        await _place_user(db_session, auth_user.id, weakest_kp="边界条件处理")
        for _ in range(3):
            db_session.add(_review_attempt(auth_user.id, "REVIEW-0250", 0.7))
        await db_session.commit()
        session = await router._next_review_session(db_session, auth_user.id)
        assert session.id == "REVIEW-0247"

    async def test_no_attempts_keeps_weakness_priority(self, db_session, auth_user):
        """无审查记录：不调整难度，仍按 P-05 弱点匹配取首关。"""
        await seed_deck(db_session)
        await _place_user(db_session, auth_user.id, weakest_kp="边界条件处理")
        session = await router._next_review_session(db_session, auth_user.id)
        assert session.id == "REVIEW-0247"


# ── P-08 竞技场今日挑战难度自适应 ───────────────────────


class TestArenaTodayChallenge:
    async def test_no_attempts_returns_rotation_base(self, db_session, auth_user):
        """无竞技场记录：返回日期轮替的基准挑战（原行为不变）。"""
        await seed_deck(db_session)
        base = await _all_challenges(db_session)
        base_ch = base[service.today_bjt().toordinal() % len(base)]
        picked = await router._today_challenge(db_session, auth_user.id)
        assert picked.id == base_ch.id

    async def test_winning_streak_shifts_up(self, db_session, auth_user):
        """近 3 次全攻克 → 升档：今日挑战难度 ≥ 基准挑战难度。"""
        await seed_deck(db_session)
        for _ in range(3):
            db_session.add(_arena_attempt(auth_user.id, 1))
        await db_session.commit()
        base = await _all_challenges(db_session)
        base_ch = base[service.today_bjt().toordinal() % len(base)]
        picked = await router._today_challenge(db_session, auth_user.id)
        assert picked.difficulty >= base_ch.difficulty

    async def test_losing_streak_shifts_down(self, db_session, auth_user):
        """近 3 次全败 → 降档：今日挑战难度 ≤ 基准挑战难度。"""
        await seed_deck(db_session)
        for _ in range(3):
            db_session.add(_arena_attempt(auth_user.id, 0))
        await db_session.commit()
        base = await _all_challenges(db_session)
        base_ch = base[service.today_bjt().toordinal() % len(base)]
        picked = await router._today_challenge(db_session, auth_user.id)
        assert picked.difficulty <= base_ch.difficulty


class TestPickByDifficulty:
    def test_empty_band_returns_none(self):
        """目标难度无挑战：返回 None（_today_challenge 回退基准挑战）。"""
        challenges = [
            DeckArenaChallenge(
                id="DEBUG-0091", title="t", language="python", code="c",
                failing_output="f", time_limit_sec=600, difficulty=3,
            )
        ]
        assert router._pick_by_difficulty(challenges, 4, 100) is None
        assert router._pick_by_difficulty(challenges, 3, 100).id == "DEBUG-0091"

    def test_rotates_within_band(self):
        """同难度多挑战：按日期序数轮替，同一天同一难度同一道题。"""
        challenges = [
            DeckArenaChallenge(
                id=f"DEBUG-{i}", title="t", language="python", code="c",
                failing_output="f", time_limit_sec=600, difficulty=2,
            )
            for i in (1, 2)
        ]
        # 101 % 2 == 1 → 取第二道；100 % 2 == 0 → 取第一道
        assert router._pick_by_difficulty(challenges, 2, 101).id == "DEBUG-2"
        assert router._pick_by_difficulty(challenges, 2, 100).id == "DEBUG-1"


# ── §4 rank_delta 排名变化 ────────────────────────────────


class TestRankDelta7d:
    """service.rank_delta_7d：近 7 天排名变化的诚实重放（不新增表）。

    约定：rating(T) = 1200 + 23 × (T 前攻克次数)（现行规则唯一积分变更点）；
    rank_delta = 7 天前排名 − 当前排名（正数 = 上升）。
    """

    async def _add_opponent(
        self, db, uid: str, rating: int, old_solves: int, recent_solves: int
    ) -> None:
        """建对手用户：User + rating 行 + old_solves 次 10 天前攻克 + recent_solves 次今天攻克。"""
        db.add(
            User(
                id=uid, email=f"{uid}@test.com", username=uid,
                hashed_password="not-a-real-hash", is_active=True,
            )
        )
        db.add(DeckArenaRating(user_id=uid, rating=rating, win_streak=0))
        for _ in range(old_solves):
            db.add(
                DeckArenaAttempt(
                    user_id=uid, challenge_id="DEBUG-0091", solved=1, passed=5, total=5,
                    created_at=datetime.now(timezone.utc) - timedelta(days=10),
                )
            )
        for _ in range(recent_solves):
            db.add(
                DeckArenaAttempt(
                    user_id=uid, challenge_id="DEBUG-0091", solved=1, passed=5, total=5,
                    created_at=datetime.now(timezone.utc),
                )
            )
        await db.commit()

    async def _add_own_attempt(self, db, user_id: str, solved: bool, days_ago: int) -> None:
        db.add(
            DeckArenaAttempt(
                user_id=user_id, challenge_id="DEBUG-0091",
                solved=1 if solved else 0, passed=5 if solved else 0, total=5,
                created_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
            )
        )
        await db.commit()

    async def test_climb_is_positive_delta(self, db_session, auth_user):
        """7 天内反超一名对手：delta = 7 天前排名 − 当前排名 = +1。"""
        await seed_deck(db_session)
        me = auth_user.id
        # 我：10 天前 1 次攻克（7 天前 1223）+ 今天 3 连攻克 → 当前 1292
        db_session.add(DeckArenaRating(user_id=me, rating=1292, win_streak=0))
        await self._add_own_attempt(db_session, me, True, days_ago=10)
        for _ in range(3):
            await self._add_own_attempt(db_session, me, True, days_ago=0)
        # 对手 C：10 天前 2 次攻克 → 7 天前/当前均 1246
        await self._add_opponent(db_session, "opponent-c", 1246, old_solves=2, recent_solves=0)
        # 对手 B：10 天前 1 次攻克 → 7 天前/当前均 1223
        await self._add_opponent(db_session, "opponent-b", 1223, old_solves=1, recent_solves=0)
        # 当前排名：1292 > 1246 > 1223 → rank 1；7 天前排名：1246 > 1223 > 1200 → rank 2
        assert await service.rank_delta_7d(db_session, me, 1) == 1

    async def test_drop_is_negative_delta(self, db_session, auth_user):
        """当前排名较 7 天前下降：delta 为负。"""
        await seed_deck(db_session)
        me = auth_user.id
        # 我：10 天前 1 次攻克 → 7 天前/当前均 1223
        db_session.add(DeckArenaRating(user_id=me, rating=1223, win_streak=0))
        await self._add_own_attempt(db_session, me, True, days_ago=10)
        # 对手 B：今天 3 连攻克 → 7 天前 1200，当前 1269
        await self._add_opponent(db_session, "opponent-b", 1269, old_solves=0, recent_solves=3)
        # 当前排名：1269 > 1223 → rank 2；7 天前排名：1223 > 1200 → rank 1
        assert await service.rank_delta_7d(db_session, me, 2) == -1

    async def test_no_history_before_window_returns_zero(self, db_session, auth_user):
        """7 天前无任何竞技场记录（新进竞技场）：7 天前排名不可定义 → 0，不误算为下降。"""
        await seed_deck(db_session)
        me = auth_user.id
        await self._add_opponent(db_session, "opponent-b", 1269, old_solves=0, recent_solves=3)
        db_session.add(DeckArenaRating(user_id=me, rating=1269, win_streak=0))
        for _ in range(3):
            await self._add_own_attempt(db_session, me, True, days_ago=0)
        # 当前排名 1，但 7 天前无记录 → 守卫返回 0
        assert await service.rank_delta_7d(db_session, me, 1) == 0

    async def test_arena_home_exposes_rank_delta(self, client, db_session, auth_user, auth_headers):
        """/api/arena/home 返回 rank_delta 字段（无历史时为 0，不再是硬编码占位）。"""
        await seed_deck(db_session)
        resp = await client.get("/api/arena/home", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["profile"]["rank_delta"] == 0
