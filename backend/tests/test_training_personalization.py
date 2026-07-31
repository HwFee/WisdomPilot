"""Dashboard 个性化链路测试（§3.5 P-01 / P-04 / P-05）。

- P-01 主任务推荐理由（router.py: build_main_task / _task_reason）：
  三轴最低 / 实现轴<LV.3（认证、费曼两个子分支）/ 未定级
- P-04 弱点来源标注（router.py: _weak_point_source / _weak_point_source_text）：
  有事件 / 无事件知识点 + 端点级验证
- P-05 审查关卡按弱点匹配（router.py: _next_review_session）：
  弱点匹配优先 / 无匹配回退顺序
"""

from sqlalchemy import select

from app.training import router, service
from app.training.models import (
    DeckAbilityAxis,
    DeckCertification,
    DeckKnowledgePoint,
    DeckUserMastery,
)
from app.training.seed import seed_deck

# placement 5 题全对答案（与 seed.py 一致）
PLACEMENT_ANSWERS = [
    {"question_id": "p1", "answer": "越界访问 arr[n]"},
    {"question_id": "p2", "answer": "while (x > 0) { x -= 2; }（x 为奇数正数）"},
    {"question_id": "p3", "answer": "与 pivot 相等的元素"},
    {"question_id": "p4", "answer": "def f(s):\n    return -1"},
    {"question_id": "p5", "answer": "def f(n):\n    return n>0 and True"},
]


async def _place_user(db, user_id: str, weakest_kp: str | None = None) -> None:
    """为测试用户写全部知识点的定级事件（答对）。

    Args:
        db: 异步数据库会话
        user_id: 用户 ID
        weakest_kp: 可选，再写一条该知识点的答错事件，让它成为全局最弱点
    """
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


async def _kp_id(db, name: str) -> str:
    return (
        await db.execute(
            select(DeckKnowledgePoint).where(DeckKnowledgePoint.name == name)
        )
    ).scalar_one().id


# ── P-01 主任务推荐理由 ──────────────────────────────────


class TestMainTaskReason:
    async def test_lowest_axis_reason(self, db_session, auth_user):
        """三轴最低分支：最低轴=debug → 主任务竞技场，理由引用轴等级 + 最弱点知识点。"""
        await seed_deck(db_session)
        await _place_user(db_session, auth_user.id, weakest_kp="指针的内存布局")
        await _set_axes(db_session, auth_user.id, {"review": 2, "debug": 1, "implement": 5})
        axes = await service.get_axes(db_session, auth_user.id)
        task = await router.build_main_task(db_session, auth_user, axes)
        assert task is not None
        assert task["module"] == "arena"
        assert "「调试」轴是三轴最低（LV.1）" in task["reason"]
        assert "「指针的内存布局」" in task["reason"]
        # 备用任务也都带推荐理由
        assert task["alternates"]
        assert all(alt["reason"] for alt in task["alternates"])

    async def test_implement_low_reason_cert(self, db_session, auth_user):
        """实现轴 < LV.3 且无冷却：主任务认证，理由引用实现轴等级。"""
        await seed_deck(db_session)
        await _place_user(db_session, auth_user.id)
        await _set_axes(db_session, auth_user.id, {"review": 3, "debug": 3, "implement": 1})
        axes = await service.get_axes(db_session, auth_user.id)
        task = await router.build_main_task(db_session, auth_user, axes)
        assert task is not None
        assert task["module"] == "certification"
        assert "「实现」轴还在 LV.1" in task["reason"]

    async def test_implement_low_reason_tutor(self, db_session, auth_user):
        """实现轴 < LV.3 且在认证冷却期：退到费曼检验，理由引用最弱点知识点。"""
        await seed_deck(db_session)
        await _place_user(db_session, auth_user.id, weakest_kp="递归出口设计")
        await _set_axes(db_session, auth_user.id, {"review": 3, "debug": 3, "implement": 2})
        # 已有认证记录 → 冷却期内不可再考
        db_session.add(
            DeckCertification(
                user_id=auth_user.id, topic="指针", level="合格", score=80,
                verify_code="WP-TEST-COOLDOWN",
            )
        )
        await db_session.commit()
        axes = await service.get_axes(db_session, auth_user.id)
        task = await router.build_main_task(db_session, auth_user, axes)
        assert task is not None
        assert task["module"] == "tutor"
        assert "「实现」轴还在 LV.2" in task["reason"]
        assert "「递归出口设计」" in task["reason"]

    async def test_no_placement_returns_none(self, db_session, auth_user):
        """未定级：主任务为 null（无 reason）。"""
        await seed_deck(db_session)
        axes = await service.get_axes(db_session, auth_user.id)
        task = await router.build_main_task(db_session, auth_user, axes)
        assert task is None


# ── P-04 弱点来源标注 ────────────────────────────────────


class TestWeakPointSource:
    def test_source_label_pure(self):
        """来源短语纯函数：答错/答对双分支 + 费曼待加强 + 未知来源兜底。"""
        assert router._weak_point_source("review_gym", False) == "审查漏报"
        assert router._weak_point_source("review_gym", True) == "审查命中"
        assert router._weak_point_source("arena", False) == "竞技场失败"
        assert router._weak_point_source("arena", True) == "竞技场攻克"
        assert router._weak_point_source("feynman", False) == "费曼待加强"
        assert router._weak_point_source("feynman", True) == "费曼检验"
        assert router._weak_point_source("certification", False) == "认证考试"
        assert router._weak_point_source("placement", True) == "定级测试"
        assert router._weak_point_source("unknown", False) == "练习记录"

    async def test_source_text_with_event(self, db_session, auth_user):
        """有事件的知识点：来源描述带时间标签与来源短语。"""
        await seed_deck(db_session)
        kp_id = await _kp_id(db_session, "指针的内存布局")
        await service.record_mastery_event(db_session, auth_user.id, kp_id, "review_gym", False)
        text = await router._weak_point_source_text(db_session, auth_user.id, kp_id)
        assert " · " in text
        assert "审查漏报" in text

    async def test_source_text_without_event(self, db_session, auth_user):
        """无事件的知识点：返回兜底文案。"""
        await seed_deck(db_session)
        kp_id = await _kp_id(db_session, "指针的内存布局")
        text = await router._weak_point_source_text(db_session, auth_user.id, kp_id)
        assert text == "暂无近期练习记录"


# ── P-05 审查关卡按弱点匹配 ──────────────────────────────


class TestNextReviewSession:
    async def test_weakness_match_priority(self, db_session, auth_user):
        """弱点匹配优先：最弱点=指针的内存布局 → 跳过 ID 靠前的 REVIEW-0247，取 REVIEW-0248。"""
        await seed_deck(db_session)
        await _place_user(db_session, auth_user.id, weakest_kp="指针的内存布局")
        session = await router._next_review_session(db_session, auth_user.id)
        assert session.id == "REVIEW-0248"

    async def test_no_match_falls_back_to_order(self, db_session, auth_user):
        """无匹配回退顺序：掌握度行只含不与任何关卡 related_weakness 匹配的知识点 → 取第一关。"""
        await seed_deck(db_session)
        for name, p_l in [
            ("栈与调用帧", 0.1),
            ("日志定位法", 0.2),
            ("断点与单步策略", 0.3),
        ]:
            db_session.add(
                DeckUserMastery(
                    user_id=auth_user.id, kp_id=await _kp_id(db_session, name),
                    p_l=p_l, level="初识",
                )
            )
        await db_session.commit()
        session = await router._next_review_session(db_session, auth_user.id)
        assert session.id == "REVIEW-0247"


# ── 端点级契约 ──────────────────────────────────────────


class TestDashboardEndpoint:
    async def test_dashboard_personalized_after_placement(
        self, client, db_session, auth_user, auth_headers
    ):
        """定级前 main_task=null；定级后 main_task.reason 与 weak_points[].source 有真实内容。"""
        await seed_deck(db_session)
        before = (await client.get("/api/dashboard", headers=auth_headers)).json()
        assert before["main_task"] is None
        assert before["weak_points"] == []

        resp = await client.post(
            "/api/certification/submit",
            json={"exam_id": "placement", "answers": PLACEMENT_ANSWERS},
            headers=auth_headers,
        )
        assert resp.status_code == 200

        after = (await client.get("/api/dashboard", headers=auth_headers)).json()
        assert after["main_task"] is not None
        assert after["main_task"]["reason"]
        assert after["weak_points"]
        for w in after["weak_points"]:
            assert w["source"]


# ── P-11 路径唯一性标识 ──────────────────────────────────


class TestTrainingFingerprint:
    """训练指纹短码（service.training_fingerprint）+ 认证首页字段。"""

    def test_design_example_shape(self):
        """设计稿示例：审阅 LV.3 / 调试 LV.1 / 实现 LV.4 → R3-D1-I4。"""
        axes = [
            {"key": "review", "label": "审阅", "level": 3},
            {"key": "debug", "label": "调试", "level": 1},
            {"key": "implement", "label": "实现", "level": 4},
        ]
        assert service.training_fingerprint(axes) == "R3-D1-I4"

    def test_all_level_1_unplaced_user(self):
        """未定级/无记录用户：三轴均 LV.1。"""
        assert service.training_fingerprint([]) == "R1-D1-I1"

    def test_order_fixed_review_debug_implement(self):
        """输出顺序固定为 R-D-I，与传入顺序无关。"""
        axes = [
            {"key": "implement", "level": 4},
            {"key": "debug", "level": 1},
            {"key": "review", "level": 3},
        ]
        assert service.training_fingerprint(axes) == "R3-D1-I4"

    async def test_certification_home_returns_fingerprint(
        self, client, db_session, auth_user, auth_headers
    ):
        """认证首页响应带 fingerprint 字段（新用户默认 R1-D1-I1）。"""
        await seed_deck(db_session)
        resp = await client.get("/api/certification/home", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["fingerprint"] == "R1-D1-I1"

    async def test_certification_home_fingerprint_reflects_axes(
        self, client, db_session, auth_user, auth_headers
    ):
        """设置三轴等级后指纹随之变化（只暴露轴等级粗粒度信息）。"""
        await seed_deck(db_session)
        await _set_axes(db_session, auth_user.id, {"review": 3, "debug": 1, "implement": 4})
        data = (await client.get("/api/certification/home", headers=auth_headers)).json()
        assert data["fingerprint"] == "R3-D1-I4"
