"""徽章系统测试（app/training/badges.py）。

- 规则单测：构造 BadgeFacts 直接测每条 check（纯函数，不碰 DB）
- 引擎集成：内存库验证幂等、智核账本流水、动态流写入
- 端点契约：cert submit（含 placement）响应含 new_badges；home 含 badges 且 hidden 脱敏
"""

from datetime import datetime

from sqlalchemy import select

from app.training import badges
from app.training.badges import BADGE_BY_ID, BADGES, BadgeFacts
from app.training.models import (
    DeckAbilityAxis,
    DeckCoreTransaction,
    DeckFeedEvent,
    DeckMasteryEvent,
    DeckUserBadge,
)
from app.training.seed import seed_deck


def make_facts(**overrides) -> BadgeFacts:
    """默认全部不满足的事实，按需覆盖"""
    base = dict(
        has_placement=False,
        cert_count=0,
        cert_levels=frozenset(),
        cert_topic_count=0,
        cert_max_score=0,
        review_attempt_count=0,
        review_has_perfect=False,
        arena_win_count=0,
        arena_win_streak=0,
        feynman_pass_count=0,
        feynman_best_grade=None,
        streak_days=0,
        night_event_count=0,
        topic_all_mastered=False,
        has_comeback=False,
    )
    base.update(overrides)
    return BadgeFacts(**base)


def check(badge_id: str, facts: BadgeFacts, ctx: dict | None = None) -> bool:
    return BADGE_BY_ID[badge_id].check(facts, ctx)


# ── 清单完整性 ──────────────────────────────────────────


class TestBadgeCatalog:
    def test_catalog_size_and_tiers(self):
        assert len(BADGES) == 17
        tiers = [b.tier for b in BADGES]
        assert tiers.count("bronze") == 7
        assert tiers.count("silver") == 7
        assert tiers.count("gold") == 3

    def test_hidden_count(self):
        assert sum(1 for b in BADGES if b.hidden) == 3

    def test_rewards_by_tier(self):
        for b in BADGES:
            expected = {"bronze": 5, "silver": 10, "gold": 20}[b.tier]
            assert b.reward_cores == expected

    def test_ids_unique(self):
        assert len({b.id for b in BADGES}) == len(BADGES)


# ── 规则单测（纯函数）────────────────────────────────────


class TestBronzeRules:
    def test_placement_done(self):
        assert check("placement-done", make_facts(has_placement=True))
        assert not check("placement-done", make_facts())

    def test_first_cert(self):
        assert check("first-cert", make_facts(cert_count=1))
        assert not check("first-cert", make_facts(cert_count=0))

    def test_review_first(self):
        assert check("review-first", make_facts(review_attempt_count=1))
        assert not check("review-first", make_facts())

    def test_arena_first_win(self):
        assert check("arena-first-win", make_facts(arena_win_count=1))
        assert not check("arena-first-win", make_facts())

    def test_feynman_first(self):
        assert check("feynman-first", make_facts(feynman_pass_count=1))
        assert not check("feynman-first", make_facts())

    def test_streak_3(self):
        assert check("streak-3", make_facts(streak_days=3))
        assert not check("streak-3", make_facts(streak_days=2))

    def test_night_owl(self):
        assert check("night-owl", make_facts(night_event_count=1))
        assert not check("night-owl", make_facts())


class TestSilverRules:
    def test_cert_adept(self):
        assert check("cert-adept", make_facts(cert_levels=frozenset({"熟练"})))
        # 精通隐含覆盖熟练档
        assert check("cert-adept", make_facts(cert_levels=frozenset({"精通"})))
        assert not check("cert-adept", make_facts(cert_levels=frozenset({"合格"})))

    def test_cert_multi_topic(self):
        assert check("cert-multi-topic", make_facts(cert_topic_count=2))
        assert not check("cert-multi-topic", make_facts(cert_topic_count=1))

    def test_review_perfect(self):
        assert check("review-perfect", make_facts(review_has_perfect=True))
        assert not check("review-perfect", make_facts())

    def test_arena_streak_3_from_facts(self):
        assert check("arena-streak-3", make_facts(arena_win_streak=3))
        assert not check("arena-streak-3", make_facts(arena_win_streak=2))

    def test_arena_streak_3_from_ctx(self):
        # 瞬时上下文：连胜发生的本次提交可触发，即使 facts 里当前值不足
        assert check("arena-streak-3", make_facts(), ctx={"arena_win_streak": 3})
        assert not check("arena-streak-3", make_facts(), ctx={"arena_win_streak": 2})
        assert not check("arena-streak-3", make_facts(), ctx=None)

    def test_feynman_star(self):
        assert check("feynman-star", make_facts(feynman_best_grade="优秀"))
        assert not check("feynman-star", make_facts(feynman_best_grade="良好"))

    def test_streak_7(self):
        assert check("streak-7", make_facts(streak_days=7))
        assert not check("streak-7", make_facts(streak_days=6))

    def test_perfect_score(self):
        assert check("perfect-score", make_facts(cert_max_score=100))
        assert not check("perfect-score", make_facts(cert_max_score=99))
        # 瞬时上下文：本次考试得分
        assert check("perfect-score", make_facts(), ctx={"cert_score": 100})
        assert not check("perfect-score", make_facts(), ctx={"cert_score": 80})


class TestGoldRules:
    def test_cert_master(self):
        assert check("cert-master", make_facts(cert_levels=frozenset({"精通"})))
        assert not check("cert-master", make_facts(cert_levels=frozenset({"熟练"})))

    def test_topic_ascend(self):
        assert check("topic-ascend", make_facts(topic_all_mastered=True))
        assert not check("topic-ascend", make_facts())

    def test_comeback(self):
        assert check("comeback", make_facts(has_comeback=True))
        assert not check("comeback", make_facts())


# ── 事件扫描（夜间 / comeback 序列）──────────────────────


def _event(kp_id: str, correct: bool, source: str, created_at: datetime) -> DeckMasteryEvent:
    return DeckMasteryEvent(
        user_id="u", kp_id=kp_id, correct=correct, source=source, created_at=created_at
    )


class TestScanEvents:
    def test_night_count_by_beijing_hour(self):
        # UTC 16:00 = 北京时间 00:00（夜间）；UTC 12:00 = 北京 20:00（非夜间）
        events = [
            _event("kp1", True, "review_gym", datetime(2026, 7, 26, 16, 30)),
            _event("kp1", True, "review_gym", datetime(2026, 7, 26, 12, 0)),
        ]
        night_count, _ = badges._scan_events(events)
        assert night_count == 1

    def test_comeback_wrong_then_review_correct(self):
        events = [
            _event("kp1", False, "certification", datetime(2026, 7, 20, 10, 0)),
            _event("kp1", True, "review_gym", datetime(2026, 7, 21, 10, 0)),
        ]
        _, has_comeback = badges._scan_events(events)
        assert has_comeback

    def test_comeback_requires_review_gym_source(self):
        # 先错后对，但答对来自 arena（理论值）→ 不算
        events = [
            _event("kp1", False, "certification", datetime(2026, 7, 20, 10, 0)),
            _event("kp1", True, "feynman", datetime(2026, 7, 21, 10, 0)),
        ]
        _, has_comeback = badges._scan_events(events)
        assert not has_comeback

    def test_comeback_requires_wrong_first(self):
        # 先对后错不算起死回生
        events = [
            _event("kp1", True, "review_gym", datetime(2026, 7, 20, 10, 0)),
            _event("kp1", False, "certification", datetime(2026, 7, 21, 10, 0)),
        ]
        _, has_comeback = badges._scan_events(events)
        assert not has_comeback


# ── 引擎集成（内存库）────────────────────────────────────


async def _pass_certification(db, user_id: str, topic: str = "指针", score: int = 100):
    """直接落一条认证记录 + 掌握度行，模拟通过认证后的事实状态"""
    from app.training.models import DeckCertification, DeckKnowledgePoint, DeckUserMastery

    db.add(
        DeckCertification(
            user_id=user_id, topic=topic, level="精通",
            score=score, verify_code=f"WP-T-{topic}-{score}",
        )
    )
    kp = DeckKnowledgePoint(name=f"KP-{topic}", category=f"CAT-{topic}", axis="implement")
    db.add(kp)
    await db.flush()
    db.add(DeckUserMastery(user_id=user_id, kp_id=kp.id, p_l=0.9, level="精通"))
    await db.commit()


class TestEvaluateAndAward:
    async def test_unlocks_and_writes_ledger_and_feed(self, db_session, test_user):
        await _pass_certification(db_session, test_user.id)

        unlocked = await badges.evaluate_and_award(db_session, test_user.id)
        await db_session.commit()
        ids = {b["id"] for b in unlocked}

        # 精通认证一次解锁：首证 / 熟练 / 精通 / 满分 / 一域通天
        assert {"first-cert", "cert-adept", "cert-master",
                "perfect-score", "topic-ascend"} <= ids
        assert all(b["reward_cores"] > 0 and b["title"] for b in unlocked)

        # 账本：每枚一条「解锁徽章 · …」流水
        transactions = (
            await db_session.execute(
                select(DeckCoreTransaction).where(DeckCoreTransaction.user_id == test_user.id)
            )
        ).scalars().all()
        badge_tx = [t for t in transactions if t.reason.startswith("解锁徽章 · ")]
        assert len(badge_tx) == len(unlocked)
        assert sum(t.delta for t in badge_tx) == sum(b["reward_cores"] for b in unlocked)

        # 动态流：每枚一条 kind=badge
        feeds = (
            await db_session.execute(
                select(DeckFeedEvent).where(
                    DeckFeedEvent.user_id == test_user.id, DeckFeedEvent.kind == "badge"
                )
            )
        ).scalars().all()
        assert len(feeds) == len(unlocked)

        # 解锁事实落表
        rows = (
            await db_session.execute(
                select(DeckUserBadge).where(DeckUserBadge.user_id == test_user.id)
            )
        ).scalars().all()
        assert {r.badge_id for r in rows} == ids

    async def test_idempotent_second_run_awards_nothing(self, db_session, test_user):
        await _pass_certification(db_session, test_user.id)
        first = await badges.evaluate_and_award(db_session, test_user.id)
        await db_session.commit()
        assert first
        balance_after_first = test_user.cores

        second = await badges.evaluate_and_award(db_session, test_user.id)
        await db_session.commit()
        assert second == []
        assert test_user.cores == balance_after_first  # 不重复发智核

        # 流水数量没翻倍：当前总数 == 第一次发的条数
        all_tx = (
            await db_session.execute(
                select(DeckCoreTransaction).where(DeckCoreTransaction.user_id == test_user.id)
            )
        ).scalars().all()
        assert len(all_tx) == len(first)

    async def test_unknown_user_returns_empty(self, db_session):
        assert await badges.evaluate_and_award(db_session, "no-such-user") == []


# ── 端点契约 ────────────────────────────────────────────


def _cert_answers(questions: list[tuple[str, str]]) -> list[dict]:
    return [{"question_id": qid, "answer": answer} for qid, answer in questions]


# placement 5 题全对答案（与 seed.py 一致；code 题需命中强化后的 answer_includes）
PLACEMENT_ANSWERS = _cert_answers([
    ("p1", "越界访问 arr[n]"),
    ("p2", "while (x != 0) { x = x - 2; }（x 为奇数正数）"),
    ("p3", "与 pivot 相等的元素"),
    ("p4", "def first_unique(s):\n    for i, ch in enumerate(s):\n"
           "        if s.count(ch) == 1:\n            return i\n    return -1"),
    ("p5", "def is_power_of_two(n):\n    return n > 0 and (n & (n - 1)) == 0"),
])

# cert-pointer 6 题全对答案（与 seed.py 一致）
POINTER_ANSWERS = _cert_answers([
    ("q1", "10"),
    ("q2", "悬空指针（值不变但目标已释放）"),
    ("q3", "值相等"),
    ("q4", "4"),
    ("q5", "void swap(int *a, int *b) { int t=*a; *a=*b; *b=t; }"),
    ("q6", "int* find(int *arr, int n) {\n"
           "    if (n <= 0) return NULL;\n"
           "    int *best = arr;\n"
           "    for (int i = 1; i < n; i++) if (arr[i] > *best) best = &arr[i];\n"
           "    return best;\n}"),
])


class TestCertificationEndpoints:
    async def test_placement_submit_returns_new_badges(
        self, client, db_session, auth_user, auth_headers
    ):
        await seed_deck(db_session)
        resp = await client.post(
            "/api/certification/submit",
            json={"exam_id": "placement", "answers": PLACEMENT_ANSWERS},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "new_badges" in data
        ids = {b["id"] for b in data["new_badges"]}
        assert "placement-done" in ids
        for b in data["new_badges"]:
            assert {"id", "tier", "title", "reward_cores"} <= set(b)

    async def test_cert_submit_pass_returns_new_badges(
        self, client, db_session, auth_user, auth_headers
    ):
        await seed_deck(db_session)
        resp = await client.post(
            "/api/certification/submit",
            json={"exam_id": "cert-pointer", "answers": POINTER_ANSWERS},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["passed"] is True
        ids = {b["id"] for b in data["new_badges"]}
        assert "first-cert" in ids

        # 重复评估幂等：home 的徽章墙里 first-cert 只出现一次且已解锁
        home = await client.get("/api/certification/home", headers=auth_headers)
        wall = home.json()["badges"]
        first_cert = [b for b in wall if b["id"] == "first-cert"]
        assert len(first_cert) == 1 and first_cert[0]["unlocked"] is True

    async def test_placement_after_formal_cert_overwrites_axes_not_500(
        self, client, db_session, auth_user, auth_headers
    ):
        """先考正式认证（add_axis_xp 建轴行）再考 placement：不撞 UNIQUE，三轴 xp 被定级规则覆盖。

        回归缺陷：placement 分支对已有 deck_ability_axes 行的用户盲插，
        撞复合主键 (user_id, axis) 的 UNIQUE 约束 → 500。
        """
        await seed_deck(db_session)
        # 先考正式认证：通过后 add_axis_xp 建 implement 轴行（40 xp）
        resp = await client.post(
            "/api/certification/submit",
            json={"exam_id": "cert-pointer", "answers": POINTER_ANSWERS},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        # 再考 placement（满分）：修复前此处盲插 DeckAbilityAxis → 500
        resp = await client.post(
            "/api/certification/submit",
            json={"exam_id": "placement", "answers": PLACEMENT_ANSWERS},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        # 三轴 xp 被定级规则覆盖（§8：xp=(level-1)×400+200，满分 debug 恒低一档）
        rows = (
            await db_session.execute(select(DeckAbilityAxis))
        ).scalars().all()
        assert {r.axis: r.xp for r in rows} == {
            "review": 1800, "debug": 1400, "implement": 1800,
        }

    async def test_home_badges_shape_and_hidden_masking(
        self, client, db_session, auth_user, auth_headers
    ):
        await seed_deck(db_session)
        resp = await client.get("/api/certification/home", headers=auth_headers)
        assert resp.status_code == 200
        wall = resp.json()["badges"]

        assert len(wall) == 17
        assert {b["id"] for b in wall} == {b.id for b in BADGES}
        for b in wall:
            assert {"id", "tier", "title", "condition_desc", "hidden",
                    "unlocked", "reward_cores", "unlocked_at"} == set(b)
            if b["hidden"] and not b["unlocked"]:
                # 隐藏未解锁：名称与条件脱敏
                assert b["title"] == "???"
                assert b["condition_desc"] == "???"
            else:
                assert b["title"] != "???"
            if not b["unlocked"]:
                assert b["unlocked_at"] is None
