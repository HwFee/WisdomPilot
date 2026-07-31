"""导师 LLM 接入层测试（app/training/service.py 的 tutor_llm_reply / feynman_evaluate）。

覆盖场景：
- LLM 正常返回：苏格拉底追问带对话历史上下文、费曼按量规评级
- 降级路径：AI 未配置 / 调用抛异常 / 脏 JSON / 空响应 → 回退脚本实现
- feynman 三档 grade 的边界（feynman_grade_from_coverage 量规）
"""

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.training import mastery, service
from app.training.models import (
    DeckAbilityAxis,
    DeckKnowledgePoint,
    DeckMasteryEvent,
    DeckUserMastery,
)
from app.training.seed import seed_deck
from app.training.service import (
    FEYNMAN_SYSTEM_PROMPT,
    SOCRATIC_SYSTEM_PROMPT,
    QUESTION_POLISH_SYSTEM_PROMPT,
    parse_feynman_llm_result,
    feynman_evaluate,
    feynman_llm_evaluate,
    question_polish,
    tutor_llm_reply,
)

# 测试用评分要点（与 seed.py 结构一致：label + keys 同义词列表）
KEY_POINTS = [
    {"keys": ["越界", "arr[n]"], "label": "越界访问"},
    {"keys": ["<= n", "i < n", "边界"], "label": "循环边界"},
    {"keys": ["下标", "索引"], "label": "下标从 0 开始"},
    {"keys": ["段错误", "未定义"], "label": "后果"},
    {"keys": ["内存"], "label": "内存布局"},
]
LABELS = [p["label"] for p in KEY_POINTS]


class FakeAI:
    """测试用假 AI 服务：可控配置、响应与异常，并记录每次调用参数。"""

    def __init__(self, configured=True, response=None, error=None):
        self._configured = configured
        self._response = response
        self._error = error
        self.calls: list[dict] = []

    def is_configured(self):
        return self._configured

    async def generate_messages(self, messages, system_prompt=None):
        self.calls.append({"messages": messages, "system_prompt": system_prompt})
        if self._error is not None:
            raise self._error
        return self._response


# ── 苏格拉底追问 ─────────────────────────────────────────


class TestSocraticMessages:
    def test_without_history_uses_bare_latest_text(self):
        messages = service._socratic_messages("指针是什么？", [])
        content = messages[0]["content"]
        assert "指针是什么？" in content
        assert "对话历史" not in content

    def test_with_history_prepends_recent_roles(self):
        history = [("user", "你好"), ("tutor", "你遇到什么问题了？")]
        content = service._socratic_messages("排序怎么写", history)[0]["content"]
        assert "学生：你好" in content
        assert "导师：你遇到什么问题了？" in content
        assert "学生最新发言" in content and "排序怎么写" in content


class TestTutorLlmReply:
    @pytest.mark.asyncio
    async def test_configured_returns_llm_text_with_system_prompt(self, db_session, test_user):
        fake = FakeAI(response="你说的「正确」具体指什么？")
        reply = await tutor_llm_reply(db_session, test_user.id, "这段代码对吗", [], ai=fake)
        assert reply == "你说的「正确」具体指什么？"
        assert fake.calls[0]["system_prompt"] == SOCRATIC_SYSTEM_PROMPT
        assert fake.calls[0]["messages"][0]["role"] == "user"

    @pytest.mark.asyncio
    async def test_provided_history_is_passed_as_context(self, db_session, test_user):
        # 调用方携带的对话历史（会话不持久化）被拼进传给 LLM 的上下文
        fake = FakeAI(response="追问")
        await tutor_llm_reply(
            db_session,
            test_user.id,
            "第二问",
            [("user", "第一问"), ("tutor", "第一答")],
            ai=fake,
        )
        content = fake.calls[0]["messages"][0]["content"]
        assert "学生：第一问" in content
        assert "导师：第一答" in content
        assert "学生最新发言" in content and "第二问" in content

    @pytest.mark.asyncio
    async def test_not_configured_falls_back_to_script(self, db_session, test_user):
        fake = FakeAI(configured=False)
        # 关键词「指针」触发脚本定向追问（KEYWORD_PROBES 第一条）
        reply = await tutor_llm_reply(db_session, test_user.id, "指针是什么", [], ai=fake)
        assert reply == service.KEYWORD_PROBES[0][1]
        assert fake.calls == []  # 未配置时不应发起 LLM 调用

    @pytest.mark.asyncio
    async def test_llm_error_falls_back_to_script(self, db_session, test_user):
        fake = FakeAI(response="ignored", error=RuntimeError("boom"))
        reply = await tutor_llm_reply(db_session, test_user.id, "指针是什么", [], ai=fake)
        assert reply == service.KEYWORD_PROBES[0][1]

    @pytest.mark.asyncio
    async def test_blank_response_falls_back_to_script(self, db_session, test_user):
        fake = FakeAI(response="   \n ")
        reply = await tutor_llm_reply(db_session, test_user.id, "指针是什么", [], ai=fake)
        assert reply == service.KEYWORD_PROBES[0][1]

    @pytest.mark.asyncio
    async def test_generic_fallback_uses_history_length_rotation(self, db_session, test_user):
        # 无关键词命中：按携带历史的条数轮替通用追问
        fake = FakeAI(configured=False)
        history = [("user", "a"), ("tutor", "b")]
        reply = await tutor_llm_reply(db_session, test_user.id, "这段代码哪里有问题", history, ai=fake)
        assert reply == service.GENERIC_PROBES[2 % len(service.GENERIC_PROBES)]


class TestQuestionPolish:
    """苏格拉底问题润色：LLM 优先，未配置/异常/空响应回退原文。"""

    @pytest.mark.asyncio
    async def test_not_configured_returns_original_text(self):
        fake = FakeAI(configured=False)
        assert await question_polish("指针怎么搞不明白", ai=fake) == "指针怎么搞不明白"
        assert fake.calls == []  # 未配置时不应发起 LLM 调用

    @pytest.mark.asyncio
    async def test_llm_error_falls_back_to_original_text(self):
        fake = FakeAI(response="ignored", error=RuntimeError("boom"))
        assert await question_polish("指针怎么搞不明白", ai=fake) == "指针怎么搞不明白"

    @pytest.mark.asyncio
    async def test_blank_response_falls_back_to_original_text(self):
        fake = FakeAI(response="   \n ")
        assert await question_polish("指针怎么搞不明白", ai=fake) == "指针怎么搞不明白"

    @pytest.mark.asyncio
    async def test_configured_returns_polished_question(self):
        fake = FakeAI(response="指针在函数间传递时为什么改了形参不影响实参？")
        result = await question_polish("我传指针进去改不动外面的变量", ai=fake)
        assert result == "指针在函数间传递时为什么改了形参不影响实参？"
        assert fake.calls[0]["system_prompt"] == QUESTION_POLISH_SYSTEM_PROMPT


class TestTutorUserContextInjection:
    """P-07：导师追问注入用户能力上下文（三轴等级 + 薄弱知识点 + 近期失败）。"""

    async def _seed_ability(self, db, user_id: str) -> None:
        """写入三轴等级 + 全量知识点定级 + 一个跌破阈值的最弱点及失败事件。"""
        await seed_deck(db)
        # 三轴等级：审阅 LV.3 / 调试 LV.1 / 实现 LV.4（等级 = 1 + xp // 400）
        db.add_all(
            [
                DeckAbilityAxis(user_id=user_id, axis="review", xp=800),
                DeckAbilityAxis(user_id=user_id, axis="debug", xp=0),
                DeckAbilityAxis(user_id=user_id, axis="implement", xp=1200),
            ]
        )
        # 10 天前全部知识点定级答对（HLR：此后 p_l 随天数自然衰减）
        old = datetime.now(timezone.utc) - timedelta(days=10)
        kps = (await db.execute(select(DeckKnowledgePoint))).scalars().all()
        for kp in kps:
            db.add(
                DeckMasteryEvent(
                    user_id=user_id, kp_id=kp.id, source="placement",
                    correct=True, created_at=old,
                )
            )
        await db.flush()
        # 除「指针的内存布局」外：今天再次答对，p_l 回到 ≈1.0（不进入薄弱区）
        for kp in kps:
            if kp.name != "指针的内存布局":
                await service.record_mastery_event(db, user_id, kp.id, "review_gym", True)
        # 最弱点：10 天未巩固且今天答错 → p_l 跌破阈值（HLR：Δ=10 天、h=0.9 → p≈0.0005），
        # 同时成为「近期失败」记录
        weak_kp = next(kp for kp in kps if kp.name == "指针的内存布局")
        await service.record_mastery_event(db, user_id, weak_kp.id, "review_gym", False)
        await db.commit()

    async def _set_kp_p_l(self, db, user_id: str, kp_name: str, p_l: float) -> None:
        """把某知识点的缓存 p_l 落成指定值（读模型可自由重建，用于阈值边界测试）。"""
        kp = (
            await db.execute(
                select(DeckKnowledgePoint).where(DeckKnowledgePoint.name == kp_name)
            )
        ).scalar_one()
        row = await db.get(DeckUserMastery, {"user_id": user_id, "kp_id": kp.id})
        assert row is not None
        row.p_l = p_l
        await db.commit()

    @pytest.mark.asyncio
    async def test_ability_context_injected_into_system_prompt(self, db_session, test_user):
        """有能力的用户：system prompt 注入三轴等级、最弱点与近期失败，核心规则保留。"""
        await self._seed_ability(db_session, test_user.id)
        fake = FakeAI(response="追问")
        await tutor_llm_reply(db_session, test_user.id, "这段代码哪里有问题", [], ai=fake)
        system_prompt = fake.calls[0]["system_prompt"]
        # 核心苏格拉底规则不变，上下文块追加在其后
        assert system_prompt.startswith(SOCRATIC_SYSTEM_PROMPT)
        assert "绝不直接给出答案" in system_prompt
        assert "审阅 LV.3" in system_prompt
        assert "调试 LV.1" in system_prompt
        assert "实现 LV.4" in system_prompt
        assert "指针的内存布局" in system_prompt  # 跌破阈值的最弱点知识点名
        assert "掌握度" in system_prompt          # 弱点带 p_l 百分比与掌握等级
        assert "近期失败" in system_prompt

    @pytest.mark.asyncio
    async def test_all_kps_above_threshold_renders_placeholder(self, db_session, test_user):
        """全部知识点 p_l ≥ 阈值（定级后常态）：薄弱知识点行渲染「（暂无）」，不注入 kp 名。"""
        await seed_deck(db_session)
        db_session.add_all(
            [
                DeckAbilityAxis(user_id=test_user.id, axis="review", xp=800),
                DeckAbilityAxis(user_id=test_user.id, axis="debug", xp=0),
                DeckAbilityAxis(user_id=test_user.id, axis="implement", xp=1200),
            ]
        )
        kps = (await db_session.execute(select(DeckKnowledgePoint))).scalars().all()
        for kp in kps:
            await service.record_mastery_event(db_session, test_user.id, kp.id, "placement", True)
        await db_session.commit()
        fake = FakeAI(response="追问")
        await tutor_llm_reply(db_session, test_user.id, "这段代码哪里有问题", [], ai=fake)
        system_prompt = fake.calls[0]["system_prompt"]
        assert "薄弱知识点：（暂无）" in system_prompt
        # 没有任何知识点名被当作薄弱点注入（轴文本只含轴名与等级）
        for kp in kps:
            assert kp.name not in system_prompt

    @pytest.mark.asyncio
    async def test_weak_threshold_boundary(self, db_session, test_user):
        """阈值边界：p_l 恰等于 DUE_MASTERY_THRESHOLD（0.6）不注入，略低于则注入。"""
        await seed_deck(db_session)
        db_session.add_all(
            [
                DeckAbilityAxis(user_id=test_user.id, axis="review", xp=800),
                DeckAbilityAxis(user_id=test_user.id, axis="debug", xp=0),
                DeckAbilityAxis(user_id=test_user.id, axis="implement", xp=1200),
            ]
        )
        kps = (await db_session.execute(select(DeckKnowledgePoint))).scalars().all()
        for kp in kps:
            await service.record_mastery_event(db_session, test_user.id, kp.id, "placement", True)
        await db_session.commit()
        # p_l 恰等于阈值 → 严格小于不成立，不注入
        await self._set_kp_p_l(
            db_session, test_user.id, "指针的内存布局", service.DUE_MASTERY_THRESHOLD
        )
        fake = FakeAI(response="追问")
        await tutor_llm_reply(db_session, test_user.id, "这段代码哪里有问题", [], ai=fake)
        assert "指针的内存布局" not in fake.calls[0]["system_prompt"]
        assert "薄弱知识点：（暂无）" in fake.calls[0]["system_prompt"]
        # p_l 略低于阈值 → 注入为薄弱知识点
        await self._set_kp_p_l(
            db_session, test_user.id, "指针的内存布局", service.DUE_MASTERY_THRESHOLD - 0.01
        )
        fake = FakeAI(response="追问")
        await tutor_llm_reply(db_session, test_user.id, "这段代码哪里有问题", [], ai=fake)
        assert "指针的内存布局" in fake.calls[0]["system_prompt"]

    @pytest.mark.asyncio
    async def test_unplaced_user_no_context_block(self, db_session, test_user):
        """未定级用户无任何能力数据 → 不注入，system prompt 与原来完全一致。"""
        fake = FakeAI(response="追问")
        await tutor_llm_reply(db_session, test_user.id, "指针是什么", [], ai=fake)
        assert fake.calls[0]["system_prompt"] == SOCRATIC_SYSTEM_PROMPT

    @pytest.mark.asyncio
    async def test_context_query_error_degrades_to_context_free_llm(
        self, db_session, test_user, monkeypatch
    ):
        """第一层降级：上下文查询异常只丢弃上下文，仍走无上下文 LLM 调用。"""
        async def boom(db, user_id):
            raise RuntimeError("db down")

        monkeypatch.setattr(service, "_tutor_user_context", boom)
        fake = FakeAI(response="追问")
        reply = await tutor_llm_reply(db_session, test_user.id, "指针是什么", [], ai=fake)
        assert reply == "追问"
        # 降级后 system prompt 不含能力档案块
        assert fake.calls[0]["system_prompt"] == SOCRATIC_SYSTEM_PROMPT

    @pytest.mark.asyncio
    async def test_context_error_then_llm_error_falls_back_to_script(
        self, db_session, test_user, monkeypatch
    ):
        """两层降级链：上下文失败 → 无上下文 LLM；LLM 也失败 → 脚本式回复。"""
        async def boom(db, user_id):
            raise RuntimeError("db down")

        monkeypatch.setattr(service, "_tutor_user_context", boom)
        fake = FakeAI(response="ignored", error=RuntimeError("llm down"))
        reply = await tutor_llm_reply(db_session, test_user.id, "指针是什么", [], ai=fake)
        # 第二层降级：LLM 调用异常 → 脚本关键词回复（KEYWORD_PROBES 第一条）
        assert reply == service.KEYWORD_PROBES[0][1]


# ── 费曼检验评分 ─────────────────────────────────────────


class TestParseFeynmanResult:
    def test_plain_json(self):
        response = json.dumps(
            {"covered": ["越界访问"], "structure": True, "feedback": "好"},
            ensure_ascii=False,
        )
        result = parse_feynman_llm_result(response, "文本", LABELS)
        assert result["covered"] == ["越界访问"]
        assert result["missed"] == [l for l in LABELS if l != "越界访问"]
        assert result["structure"] is True
        assert result["feedback"] == "好"

    def test_json_codeblock_wrapped(self):
        response = '```json\n{"covered": ["越界访问"], "feedback": "好"}\n```'
        result = parse_feynman_llm_result(response, "文本", LABELS)
        assert result["covered"] == ["越界访问"]

    def test_dirty_response_returns_none(self):
        assert parse_feynman_llm_result("很抱歉，我暂时无法回答。", "文本", LABELS) is None

    def test_invalid_covered_type_returns_none(self):
        assert parse_feynman_llm_result('{"covered": "越界访问"}', "文本", LABELS) is None

    def test_unknown_labels_filtered_and_missed_recomputed(self):
        response = '{"covered": ["越界访问", "不存在的要点"], "feedback": "x"}'
        result = parse_feynman_llm_result(response, "文本", LABELS)
        assert result["covered"] == ["越界访问"]
        assert result["missed"] == [l for l in LABELS if l != "越界访问"]

    def test_missing_structure_falls_back_to_text_markers(self):
        # 文本含因果（因为）+ 举例（比如）→ structure=True
        result = parse_feynman_llm_result('{"covered": []}', "因为 x 所以 y，比如 z", LABELS)
        assert result["structure"] is True

    def test_non_string_feedback_becomes_empty(self):
        result = parse_feynman_llm_result('{"covered": [], "feedback": 123}', "文本", LABELS)
        assert result["feedback"] == ""


class TestFeynmanGradeFromCoverage:
    """量规边界（与 docs/backend-api/01 §5 对齐）"""

    def test_excellent_requires_80_and_structure(self):
        assert mastery.feynman_grade_from_coverage(0.8, True, True) == "优秀"
        assert mastery.feynman_grade_from_coverage(0.9, True, True) == "优秀"

    def test_80_without_structure_is_good(self):
        assert mastery.feynman_grade_from_coverage(0.8, False, True) == "良好"

    def test_50_is_good_even_without_structure(self):
        assert mastery.feynman_grade_from_coverage(0.5, False, True) == "良好"

    def test_one_third_with_structure_is_good(self):
        # COVERAGE_GOOD_WITH_STRUCTURE = 0.34（略高于 1/3）
        assert mastery.feynman_grade_from_coverage(0.34, True, True) == "良好"

    def test_below_one_third_without_structure_is_weak(self):
        assert mastery.feynman_grade_from_coverage(0.33, True, True) == "待加强"
        assert mastery.feynman_grade_from_coverage(0.4, False, True) == "待加强"

    def test_no_points_uses_structure_only(self):
        assert mastery.feynman_grade_from_coverage(0.0, True, False) == "良好"
        assert mastery.feynman_grade_from_coverage(0.0, False, False) == "待加强"


class TestFeynmanLlmEvaluate:
    @pytest.mark.asyncio
    async def test_full_coverage_with_structure_is_excellent(self):
        fake = FakeAI(
            response=(
                '{"covered": ["越界访问", "循环边界", "下标从 0 开始", "后果"], '
                '"structure": true, "feedback": "讲得很清楚，但内存布局没提到。"}'
            )
        )
        result = await feynman_llm_evaluate("text", "指针的内存布局", KEY_POINTS, ai=fake)
        assert result["grade"] == "优秀"  # 4/5 = 0.8 且有结构
        assert result["feedback"] == "讲得很清楚，但内存布局没提到。"

    @pytest.mark.asyncio
    async def test_half_coverage_is_good(self):
        fake = FakeAI(
            response='{"covered": ["越界访问", "循环边界", "下标从 0 开始"], "structure": false, "feedback": "好"}'
        )
        result = await feynman_llm_evaluate("text", "kp", KEY_POINTS, ai=fake)
        assert result["grade"] == "良好"  # 3/5 = 0.6 ≥ 0.5

    @pytest.mark.asyncio
    async def test_low_coverage_without_structure_is_weak(self):
        fake = FakeAI(response='{"covered": ["越界访问"], "structure": false, "feedback": "好"}')
        result = await feynman_llm_evaluate("text", "kp", KEY_POINTS, ai=fake)
        assert result["grade"] == "待加强"  # 1/5 = 0.2

    @pytest.mark.asyncio
    async def test_missing_feedback_falls_back_to_script_feedback(self):
        fake = FakeAI(response='{"covered": [], "structure": true}')
        result = await feynman_llm_evaluate("text", "kp", KEY_POINTS, ai=fake)
        assert result["grade"] == "待加强"  # 0/5 无覆盖
        assert "没讲到的要点" in result["feedback"]  # feynman_feedback 兜底

    @pytest.mark.asyncio
    async def test_not_configured_returns_none(self):
        fake = FakeAI(configured=False)
        assert await feynman_llm_evaluate("text", "kp", KEY_POINTS, ai=fake) is None


class TestFeynmanEvaluate:
    """统一入口：LLM 优先，异常/脏 JSON/未配置回退关键词评分"""

    @pytest.mark.asyncio
    async def test_llm_ok_uses_llm_grade_and_feedback(self):
        fake = FakeAI(
            response='{"covered": ["越界访问", "循环边界", "下标从 0 开始", "后果"], "structure": true, "feedback": "LLM 点评"}'
        )
        grade, verdict = await feynman_evaluate("text", "kp", KEY_POINTS, ai=fake)
        assert (grade, verdict) == ("优秀", "LLM 点评")

    @pytest.mark.asyncio
    async def test_not_configured_falls_back_to_keyword_grade(self):
        fake = FakeAI(configured=False)
        text = "因为索引从 0 开始，所以 i < n 才对，比如越界 arr[n] 未定义。"
        grade, verdict = await feynman_evaluate(text, "kp", KEY_POINTS, ai=fake)
        assert grade == "优秀"  # 关键词 4/5 命中 + 因果/举例结构
        assert "没讲到的要点" not in verdict  # 优秀分支脚本点评不含遗漏（脚本现有行为）
        assert fake.calls == []

    @pytest.mark.asyncio
    async def test_not_configured_good_verdict_names_missed_points(self):
        fake = FakeAI(configured=False)
        text = "因为 i < n，所以不会越界访问 arr[n]，比如最后一个元素是 arr[n-1]。"
        grade, verdict = await feynman_evaluate(text, "kp", KEY_POINTS, ai=fake)
        assert grade == "良好"  # 2/5 = 0.4 ≥ 1/3 且有结构
        assert "没讲到的要点" in verdict  # 脚本点评点名遗漏的关键点

    @pytest.mark.asyncio
    async def test_dirty_json_falls_back_to_keyword_grade(self):
        fake = FakeAI(response="模型暂时不可用，请稍后再试。")
        text = "因为索引从 0 开始，所以 i < n 才对，比如越界 arr[n] 未定义。"
        grade, _ = await feynman_evaluate(text, "kp", KEY_POINTS, ai=fake)
        assert grade == "优秀"

    @pytest.mark.asyncio
    async def test_llm_error_falls_back_to_keyword_grade(self):
        fake = FakeAI(response="x", error=RuntimeError("timeout"))
        text = "因为索引从 0 开始，所以 i < n 才对，比如越界 arr[n] 未定义。"
        grade, _ = await feynman_evaluate(text, "kp", KEY_POINTS, ai=fake)
        assert grade == "优秀"


# ── 端点级冒烟（全局 AI 未配置时契约与降级）──────────────


class TestTutorEndpoints:
    @pytest.mark.asyncio
    async def test_message_endpoint_falls_back_to_script_when_ai_unconfigured(
        self, client, auth_user, auth_headers
    ):
        resp = await client.post(
            "/api/tutor/message",
            json={"text": "指针是什么", "mode": "socratic"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        msg = data["message"]
        assert msg["role"] == "tutor"
        assert msg["mode"] == "socratic"
        assert "cores_balance" in data
        # 全局 ai_service 未配置（测试环境不跑 lifespan configure）→ 降级脚本回复
        assert msg["text"] == service.KEYWORD_PROBES[0][1]
        # polished_question：未配置 → 润色降级回原文
        assert data["polished_question"] == "指针是什么"

    @pytest.mark.asyncio
    async def test_feynman_check_endpoint_shape(
        self, client, db_session, auth_user, auth_headers
    ):
        await seed_deck(db_session)
        # 开启费曼会话
        resp = await client.post(
            "/api/tutor/feynman",
            json={"topic": "指针的内存布局"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        session_id = resp.json()["feynman_session_id"]
        # 提交讲解（AI 未配置 → 脚本评分降级），契约字段逐项校验
        text = "因为指针存地址，解引用 *p 拿到指向的值，free 之后会变成悬空指针，比如 p++ 步长是类型字节数，NULL 不能解引用。"
        resp = await client.post(
            "/api/tutor/feynman/check",
            json={"session_id": session_id, "text": text},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["grade"] in ("优秀", "良好", "待加强")
        assert data["message"]["role"] == "tutor"
        assert data["message"]["mode"] == "feynman"
        assert data["mastery_update"]["kp_name"] == "指针的内存布局"
        assert "p_l_before" in data["mastery_update"]
        assert "p_l_after" in data["mastery_update"]

    @pytest.mark.asyncio
    async def test_feynman_start_returns_session_only(
        self, client, db_session, auth_user, auth_headers
    ):
        """start_feynman 仅返回 session_id（无开场白消息），且不写任何消息表。"""
        await seed_deck(db_session)
        for topic in ["指针的内存布局", "递归出口设计"]:
            resp = await client.post(
                "/api/tutor/feynman", json={"topic": topic}, headers=auth_headers
            )
            assert resp.status_code == 200
            data = resp.json()
            # 契约：只返回 feynman_session_id + cores_balance，无 message 字段
            assert "message" not in data
            assert data["feynman_session_id"]
            assert "cores_balance" in data
        # GET /tutor/state 的 messages 为空数组（会话不持久化）
        resp = await client.get("/api/tutor/state", headers=auth_headers)
        assert resp.status_code == 200
        assert [m for m in resp.json()["messages"] if m["mode"] == "feynman"] == []

    @pytest.mark.asyncio
    async def test_feynman_check_writes_no_messages(
        self, client, db_session, auth_user, auth_headers
    ):
        """费曼会话完全不持久化（消息表已删除）：check 作答不落库，
        掌握度事件照常写入事件表，点评为临时消息。"""
        await seed_deck(db_session)
        resp = await client.post(
            "/api/tutor/feynman",
            json={"topic": "指针的内存布局"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        session_id = resp.json()["feynman_session_id"]
        resp = await client.post(
            "/api/tutor/feynman/check",
            json={
                "session_id": session_id,
                "text": "因为指针存的是地址，解引用 *p 拿到指向的值，free 之后成悬垂指针，比如 NULL 不能解引用。",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        # 点评是临时消息：id 以 feynman-reply- 开头，role/mode 契约不变
        assert data["message"]["id"].startswith("feynman-reply-")
        assert data["message"]["role"] == "tutor"
        assert data["message"]["mode"] == "feynman"
        assert data["grade"] in ("优秀", "良好", "待加强")
        # 掌握度事件照常写入（事实源保留，徽章/图谱依赖它）
        events = (
            await db_session.execute(
                select(DeckMasteryEvent).where(DeckMasteryEvent.user_id == auth_user.id)
            )
        ).scalars().all()
        assert len(events) == 1
        assert events[0].source == "feynman"
        assert events[0].grade is not None

    @pytest.mark.asyncio
    async def test_feynman_multiple_sessions_no_persistence(
        self, client, db_session, auth_user, auth_headers
    ):
        """start → check → 再 start 新 topic：全程不落库（消息表已删除），
        get_tutor_state 的 messages 恒为空数组。"""
        await seed_deck(db_session)
        resp = await client.post(
            "/api/tutor/feynman",
            json={"topic": "指针的内存布局"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        session_id = resp.json()["feynman_session_id"]
        resp = await client.post(
            "/api/tutor/feynman/check",
            json={
                "session_id": session_id,
                "text": "因为指针存的是地址，解引用 *p 拿到指向的值，free 之后成悬垂指针，比如 NULL 不能解引用。",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        # 再 start 新 topic
        resp = await client.post(
            "/api/tutor/feynman",
            json={"topic": "递归出口设计"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        # GET /tutor/state 的 messages 为空数组
        resp = await client.get("/api/tutor/state", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["messages"] == []

    @pytest.mark.asyncio
    async def test_tutor_message_persists_no_messages_and_uses_history(
        self, client, db_session, auth_user, auth_headers
    ):
        """send_tutor_message 不落库（消息表已删除）；携带 history 影响脚本回复轮换。"""
        # 带 3 条历史、无关键词文本 → 脚本降级按 len(history)=3 轮换通用追问
        resp = await client.post(
            "/api/tutor/message",
            json={
                "text": "这段代码哪里有问题",
                "mode": "socratic",
                "history": [
                    {"role": "user", "text": "你好"},
                    {"role": "tutor", "text": "什么问题？"},
                    {"role": "user", "text": "递归"},
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"]["role"] == "tutor"
        assert data["message"]["text"] == service.GENERIC_PROBES[3 % len(service.GENERIC_PROBES)]

    @pytest.mark.asyncio
    async def test_tutor_state_returns_empty_messages(
        self, client, db_session, auth_user, auth_headers
    ):
        """get_tutor_state：会话不持久化，messages 恒为空数组，其余契约字段保留。"""
        await seed_deck(db_session)
        resp = await client.get("/api/tutor/state", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["messages"] == []
        assert "cores_balance" in data
        assert data["cost_per_question"] == service.TUTOR_COST
        assert isinstance(data["suggested_topics"], list)
