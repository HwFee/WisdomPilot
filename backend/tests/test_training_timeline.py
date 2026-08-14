"""训练轨迹时间线与能力演化测试（§3.5 P-09 / P-10）。

- P-09 训练档案路径时间线（service.build_timeline）：
  定级画像 / 轴升级重放 / 知识点里程碑 / 认证通过 + 端点级契约
- P-10 能力演化对比（service.placement_snapshot / placement_levels_from_score）：
  定级分数 → 初始三轴等级复算 + 能力图谱端点 placement 字段
- 定级 feed 结构化载荷（placement_score_from_feed）：
  新格式 payload.placement.score / 旧格式 segments 文案兜底
"""

from datetime import timedelta

from sqlalchemy import select

from app.training import service
from app.training.models import (
    DeckAbilityAxis,
    DeckArenaAttempt,
    DeckArenaChallenge,
    DeckCertification,
    DeckFeedEvent,
    DeckKnowledgePoint,
    DeckMasteryEvent,
    DeckReviewAttempt,
)
from app.training.seed import seed_deck
from app.utils.time import utc_now

# placement 5 题全对答案（与 seed.py 一致，score=100）
PLACEMENT_ANSWERS = [
    {"question_id": "p1", "answer": "越界访问 arr[n]"},
    {"question_id": "p2", "answer": "while (x > 0) { x -= 2; }（x 为奇数正数）"},
    {"question_id": "p3", "answer": "与 pivot 相等的元素"},
    {"question_id": "p4", "answer": "def f(s):\n    return -1"},
    {"question_id": "p5", "answer": "def f(n):\n    return n>0 and True"},
]


async def _add_arena_challenges(db, count: int) -> None:
    """补充测试专用的竞技场挑战行（partial unique index 下每场攻克需要不同挑战）。"""
    db.add_all(
        DeckArenaChallenge(
            id=f"TST-{i:03d}", title=f"t{i}", language="python", code="c",
            failing_output="f", time_limit_sec=600, difficulty=1,
        )
        for i in range(count)
    )
    await db.flush()


async def _seed_placement(
    db, user_id: str, score: int = 100, structured: bool = True
) -> None:
    """为测试用户写入定级数据（掌握度事件 + 初始轴经验 + 定级 feed 事件）。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID
        score: 定级分数（决定初始三轴等级）
        structured: True 写新格式 feed 载荷（含 placement 结构），
                    False 写旧格式（只有 segments 文案）
    """
    kps = (await db.execute(select(DeckKnowledgePoint))).scalars().all()
    for kp in kps:
        await service.record_mastery_event(db, user_id, kp.id, "placement", score >= 60)
    for axis, xp in service.placement_axis_xp(score).items():
        db.add(DeckAbilityAxis(user_id=user_id, axis=axis, xp=xp))
    extra = (
        {"placement": {"score": score, "levels": service.placement_levels_from_score(score)}}
        if structured
        else None
    )
    await service.add_feed(
        db,
        user_id,
        "cert",
        [
            {"t": "完成定级测试，"},
            {"t": f"{score} 分", "tone": "strong"},
            {"t": "，能力图谱已生成", "tone": "ok"},
        ],
        extra=extra,
    )
    await db.commit()


# ── P-10 定级分数解析与等级复算（纯函数） ────────────────


class TestPlacementScoreFromFeed:
    def test_structured_new_format(self):
        """新格式：payload.placement.score 结构化字段直接读取。"""
        payload = {
            "segments": [{"t": "完成定级测试，"}],
            "placement": {"score": 80, "levels": {"review": 4, "debug": 3, "implement": 4}},
        }
        assert service.placement_score_from_feed(payload) == 80

    def test_old_format_parses_segments_text(self):
        """旧格式：从「完成定级测试，100 分」文案中解析分数。"""
        payload = {
            "segments": [
                {"t": "完成定级测试，"},
                {"t": "100 分", "tone": "strong"},
                {"t": "，能力图谱已生成", "tone": "ok"},
            ]
        }
        assert service.placement_score_from_feed(payload) == 100

    def test_old_format_handles_compact_text(self):
        """旧格式：无空格的「80分」也能解析。"""
        payload = {"segments": [{"t": "完成定级测试，"}, {"t": "80分", "tone": "strong"}]}
        assert service.placement_score_from_feed(payload) == 80

    def test_non_placement_feed_returns_none(self):
        """非定级 feed（如认证通过动态）不含定级标记 → None。"""
        payload = {
            "segments": [
                {"t": "通过基本功认证 "},
                {"t": "指针", "tone": "strong"},
                {"t": " · 80 分", "tone": "ok"},
            ]
        }
        assert service.placement_score_from_feed(payload) is None

    def test_malformed_returns_none(self):
        """定级 feed 但缺分数段 → None（不误解析）。"""
        payload = {"segments": [{"t": "完成定级测试，"}, {"t": "能力图谱已生成"}]}
        assert service.placement_score_from_feed(payload) is None


class TestPlacementLevelsFromScore:
    def test_full_score(self):
        """满分 100：base=5，debug 低一档。"""
        assert service.placement_levels_from_score(100) == {
            "review": 5, "debug": 4, "implement": 5,
        }

    def test_debug_never_below_one(self):
        """低分时 debug 兜底 LV.1。"""
        assert service.placement_levels_from_score(0)["debug"] == 1
        assert service.placement_levels_from_score(24)["debug"] == 1

    def test_score_bucket_boundaries(self):
        """score//25 分桶：24/25、49/50、59/60 各跨一档。"""
        assert service.placement_levels_from_score(24)["review"] == 1
        assert service.placement_levels_from_score(25)["review"] == 2
        assert service.placement_levels_from_score(49)["review"] == 2
        assert service.placement_levels_from_score(50)["review"] == 3
        assert service.placement_levels_from_score(59)["debug"] == 2
        assert service.placement_levels_from_score(60)["review"] == 3
        assert service.placement_levels_from_score(75)["implement"] == 4
        assert service.placement_levels_from_score(100)["review"] == 5

    def test_axis_xp_formula(self):
        """初始经验 = (level-1)×400 + 200（§8）。"""
        assert service.placement_axis_xp(100) == {
            "review": 1800, "debug": 1400, "implement": 1800,
        }
        assert service.placement_axis_xp(0) == {"review": 200, "debug": 200, "implement": 200}


# ── P-10 定级画像快照 ────────────────────────────────────


class TestPlacementSnapshot:
    async def test_none_without_placement(self, db_session, auth_user):
        """未定级：快照为 None。"""
        await seed_deck(db_session)
        assert await service.placement_snapshot(db_session, auth_user.id) is None

    async def test_snapshot_from_structured_feed(self, db_session, auth_user):
        """新格式 feed：快照带分数/日期/初始等级/指纹。"""
        await seed_deck(db_session)
        await _seed_placement(db_session, auth_user.id, score=100)
        snap = await service.placement_snapshot(db_session, auth_user.id)
        assert snap == {
            "score": 100,
            "date": snap["date"],  # 日期为定级当天
            "levels": {"review": 5, "debug": 4, "implement": 5},
            "fingerprint": "R5-D4-I5",
        }

    async def test_snapshot_falls_back_to_old_feed_format(self, db_session, auth_user):
        """旧格式 feed（无结构化字段）：从 segments 文案解析分数再复算等级。"""
        await seed_deck(db_session)
        await _seed_placement(db_session, auth_user.id, score=60, structured=False)
        snap = await service.placement_snapshot(db_session, auth_user.id)
        assert snap is not None
        assert snap["score"] == 60
        assert snap["levels"] == {"review": 3, "debug": 2, "implement": 3}
        assert snap["fingerprint"] == "R3-D2-I3"


# ── P-09 训练轨迹时间线 ──────────────────────────────────


class TestBuildTimeline:
    async def test_empty_without_placement(self, db_session, auth_user):
        """未定级：时间线为空列表。"""
        await seed_deck(db_session)
        assert await service.build_timeline(db_session, auth_user.id) == []

    async def test_placement_entry_only(self, db_session, auth_user):
        """只定级无训练：时间线仅一条定级画像。"""
        await seed_deck(db_session)
        await _seed_placement(db_session, auth_user.id, score=80)
        timeline = await service.build_timeline(db_session, auth_user.id)
        assert len(timeline) == 1
        entry = timeline[0]
        assert entry["type"] == "placement"
        assert entry["score"] == 80
        assert entry["fingerprint"] == "R4-D3-I4"
        assert entry["levels"] == {"review": 4, "debug": 3, "implement": 4}
        assert entry["date"]

    async def test_axis_upgrade_replay(self, db_session, auth_user):
        """轴升级重放：初始 debug xp=200（LV.1）+ 9 场攻克×23=207 → 407 跨过 400 边界升 LV.2。"""
        await seed_deck(db_session)
        await _seed_placement(db_session, auth_user.id, score=0)
        # 安全审计修复：partial unique index 要求同挑战仅一条 solved=1，创建 9 个测试挑战
        await _add_arena_challenges(db_session, 9)
        for i in range(9):
            db_session.add(
                DeckArenaAttempt(
                    user_id=auth_user.id, challenge_id=f"TST-{i:03d}",
                    solved=1, passed=5, total=5,
                )
            )
        await db_session.commit()
        timeline = await service.build_timeline(db_session, auth_user.id)
        upgrades = [e for e in timeline if e["type"] == "axis_upgrade"]
        assert len(upgrades) == 1
        assert upgrades[0]["axis"] == "debug"
        assert upgrades[0]["label"] == "调试"
        assert upgrades[0]["from_level"] == 1
        assert upgrades[0]["to_level"] == 2

    async def test_axis_upgrade_only_emits_on_boundary(self, db_session, auth_user):
        """未跨过 400 边界的经验增量不产生升级条目。"""
        await seed_deck(db_session)
        await _seed_placement(db_session, auth_user.id, score=100)  # implement 初始 1800（LV.5）
        # 认证通过 +40 → 1840 仍 LV.5，不产生 implement 升级条目
        db_session.add(
            DeckCertification(
                user_id=auth_user.id, topic="指针", level="熟练",
                score=88, verify_code="WP-TEST-NO-UPGRADE",
            )
        )
        await db_session.commit()
        timeline = await service.build_timeline(db_session, auth_user.id)
        assert all(e["type"] != "axis_upgrade" for e in timeline)
        assert any(e["type"] == "cert" for e in timeline)

    async def test_mastery_milestones(self, db_session, auth_user):
        """4 次跨天实战答对：第 3 次达到熟练、第 4 次（间隔≥3 天 + 实战源）达到精通。"""
        await seed_deck(db_session)
        await _seed_placement(db_session, auth_user.id, score=100)
        kp = (
            await db_session.execute(
                select(DeckKnowledgePoint).where(DeckKnowledgePoint.name == "链表操作")
            )
        ).scalar_one()
        base = utc_now() + timedelta(days=1)
        for i in range(4):
            db_session.add(
                DeckMasteryEvent(
                    user_id=auth_user.id, kp_id=kp.id, source="review_gym",
                    correct=True, created_at=base + timedelta(days=i),
                )
            )
        await db_session.commit()
        timeline = await service.build_timeline(db_session, auth_user.id)
        milestones = [e for e in timeline if e["type"] == "mastery"]
        assert [e["level"] for e in milestones] == ["熟练", "精通"]
        assert all(e["kp_name"] == "链表操作" for e in milestones)
        # 精通在第 4 天（base+3），晚于熟练（base+2）
        assert milestones[0]["date"] < milestones[1]["date"]

    async def test_chronological_merge_all_types(self, db_session, auth_user):
        """四类条目按时间升序合并：定级 → 轴升级 → 知识点里程碑 → 认证。"""
        await seed_deck(db_session)
        await _seed_placement(db_session, auth_user.id, score=0)  # 三轴均 LV.1（xp=200）
        now = utc_now() + timedelta(days=1)
        # 第 1 天：9 场竞技场攻克 → debug 407 跨 400 边界 → LV.2
        # （partial unique index：同挑战仅一条 solved=1，创建 9 个测试挑战）
        await _add_arena_challenges(db_session, 9)
        for i in range(9):
            db_session.add(
                DeckArenaAttempt(
                    user_id=auth_user.id, challenge_id=f"TST-{i:03d}",
                    solved=1, passed=5, total=5, created_at=now,
                )
            )
        # 第 2~4 天：3 次实战答对 → 第 3 次（now+2 天）达到熟练
        kp = (
            await db_session.execute(
                select(DeckKnowledgePoint).where(DeckKnowledgePoint.name == "链表操作")
            )
        ).scalar_one()
        for i in range(3):
            db_session.add(
                DeckMasteryEvent(
                    user_id=auth_user.id, kp_id=kp.id, source="review_gym",
                    correct=True, created_at=now + timedelta(days=1 + i),
                )
            )
        # 第 5 天：认证通过
        db_session.add(
            DeckCertification(
                user_id=auth_user.id, topic="指针", level="熟练", score=88,
                verify_code="WP-TEST-ORDER", created_at=now + timedelta(days=4),
            )
        )
        await db_session.commit()
        timeline = await service.build_timeline(db_session, auth_user.id)
        assert [e["type"] for e in timeline] == [
            "placement", "axis_upgrade", "mastery", "cert",
        ]
        dates = [e["date"] for e in timeline]
        assert dates == sorted(dates)
        # 认证通过的日期与 implement 升级条目互不干扰（实现轴未升级）
        assert timeline[-1]["topic"] == "指针"

    async def test_review_hits_contribute_review_xp(self, db_session, auth_user):
        """审查命中计入 review 轴重放：10 处命中 ×20=200 + 初始 200 = 400 → LV.2。"""
        await seed_deck(db_session)
        await _seed_placement(db_session, auth_user.id, score=0)
        db_session.add(
            DeckReviewAttempt(
                user_id=auth_user.id, session_id="REVIEW-0247",
                marks=[], verdict={"hits": [{"line": 1, "type": "logic"}] * 10},
            )
        )
        await db_session.commit()
        timeline = await service.build_timeline(db_session, auth_user.id)
        upgrades = [e for e in timeline if e["type"] == "axis_upgrade"]
        assert len(upgrades) == 1
        assert upgrades[0]["axis"] == "review"
        assert upgrades[0]["to_level"] == 2


# ── 端点级契约 ───────────────────────────────────────────


class TestProfileTimelineEndpoint:
    async def test_profile_timeline_after_placement(
        self, client, db_session, auth_user, auth_headers
    ):
        """GET /api/profile：未定级 timeline=[]，定级后首条为 placement。"""
        await seed_deck(db_session)
        before = (await client.get("/api/profile", headers=auth_headers)).json()
        assert before["timeline"] == []

        resp = await client.post(
            "/api/certification/submit",
            json={"exam_id": "placement", "answers": PLACEMENT_ANSWERS},
            headers=auth_headers,
        )
        assert resp.status_code == 200

        after = (await client.get("/api/profile", headers=auth_headers)).json()
        assert after["timeline"][0]["type"] == "placement"
        assert after["timeline"][0]["score"] == 100
        assert after["timeline"][0]["fingerprint"] == "R5-D4-I5"

    async def test_placement_submit_writes_structured_payload(
        self, client, db_session, auth_user, auth_headers
    ):
        """定级提交端点的 feed 载荷带结构化 placement 字段（P-10 精确复算数据源）。"""
        await seed_deck(db_session)
        resp = await client.post(
            "/api/certification/submit",
            json={"exam_id": "placement", "answers": PLACEMENT_ANSWERS},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        rows = (
            await db_session.execute(
                select(DeckFeedEvent).where(
                    DeckFeedEvent.user_id == auth_user.id,
                    DeckFeedEvent.kind == "cert",
                )
            )
        ).scalars().all()
        assert len(rows) == 1
        assert rows[0].payload["placement"]["score"] == 100
        assert rows[0].payload["placement"]["levels"] == {
            "review": 5, "debug": 4, "implement": 5,
        }
        # 前端渲染只依赖 segments，结构化字段不破坏原契约
        assert rows[0].payload["segments"][1]["t"] == "100 分"


class TestAbilityMapPlacementEndpoint:
    async def test_ability_map_placement_snapshot(
        self, client, db_session, auth_user, auth_headers
    ):
        """GET /api/ability-map：未定级 placement=None，定级后带完整快照。"""
        await seed_deck(db_session)
        before = (await client.get("/api/ability-map", headers=auth_headers)).json()
        assert before["placement"] is None

        resp = await client.post(
            "/api/certification/submit",
            json={"exam_id": "placement", "answers": PLACEMENT_ANSWERS},
            headers=auth_headers,
        )
        assert resp.status_code == 200

        after = (await client.get("/api/ability-map", headers=auth_headers)).json()
        assert after["placement"]["score"] == 100
        assert after["placement"]["levels"] == {"review": 5, "debug": 4, "implement": 5}
        assert after["placement"]["fingerprint"] == "R5-D4-I5"
        assert after["placement"]["date"]
