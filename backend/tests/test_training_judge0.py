"""Judge0 判题接入层测试（app/training/service.py 的 judge_arena_code_submit / judge_cert_code_answer）。

覆盖场景：
- Judge0 正常判题：竞技场全过 / 部分过 / 编译错误，认证 code 题全过判对 / 部分过判错
- 降级路径：Judge0 未配置 / 抛异常 / 无测试用例 → 回退关键字匹配（竞技场 + 认证）
- mcq 判分不回归（judge_cert_answer 的 mcq 分支不受影响）
- 种子数据 test_cases 结构合法，且每个 code 题都有对应判题驱动
- 端点冒烟：全局 Judge0 未配置时 /api/arena/run 与 /api/certification/submit 走降级返回 200
"""

import pytest

from app.training import service
from app.training.seed import ARENA_CHALLENGES, CERT_QUESTIONS, seed_deck

# 竞技场 DEBUG-0091 的种子测试用例（驱动 + 语言映射与种子保持一致）
SEED_0091 = next(c["test_cases"] for c in ARENA_CHALLENGES if c["id"] == "DEBUG-0091")
# 认证 cert-pointer:q5 的种子测试用例
SEED_Q5 = next(
    r[8] for r in CERT_QUESTIONS if r[0] == "cert-pointer" and r[1] == "q5"
)
# DEBUG-0091 的修复版代码（同时满足关键字匹配的修复模式）
FIXED_0091 = """def median(nums):
    nums = sorted(nums)
    n = len(nums)
    mid = n // 2
    if n % 2 == 1:
        return nums[mid]
    lo = mid - 1
    return (nums[lo] + nums[mid]) / 2"""


class FakeJudge:
    """测试用假 Judge0 服务：可控返回与异常，并记录每次调用参数。"""

    def __init__(self, batch_result=None, error=None):
        self._batch_result = batch_result
        self._error = error
        self.calls: list[dict] = []

    async def execute_batch(self, code, language_id, test_cases):
        self.calls.append({"code": code, "language_id": language_id, "test_cases": test_cases})
        if self._error is not None:
            raise self._error
        return self._batch_result


def _batch(passed: int, total: int = 5) -> dict:
    """构造 Judge0 批量判题结果：前 passed 个用例通过，其余输出不匹配。"""
    inputs = ["[1]", "[3, 1, 2]", "[4, 1, 2, 5]", "[-1, -4, -3, -5]", "[9, 5, 2, 7, 8, 1]"]
    results = []
    for i in range(total):
        if i < passed:
            results.append(
                {"passed": True, "input": inputs[i], "expected": "1", "actual": "1", "message": "通过"}
            )
        else:
            results.append(
                {
                    "passed": False,
                    "input": inputs[i],
                    "expected": "3.0",
                    "actual": "4.5",
                    "message": "输出错误",
                }
            )
    return {
        "token": "tok",
        "status_id": 3 if passed == total else 4,
        "status": "Accepted" if passed == total else "Wrong Answer",
        "passed_count": passed,
        "total_count": total,
        "results": results,
        "time": None,
        "memory": None,
        "compile_output": None,
        "message": "通过 3/5 个测试点" if passed != total else None,
    }


def _compile_error_batch(total: int = 5) -> dict:
    """构造全部编译失败的批量判题结果。"""
    results = [
        {
            "passed": False,
            "input": "",
            "expected": "",
            "actual": "",
            "message": "⚠️ Compilation Error: 语法错误",
        }
        for _ in range(total)
    ]
    return {
        "token": "tok",
        "status_id": 5,
        "status": "Compilation Error",
        "passed_count": 0,
        "total_count": total,
        "results": results,
        "time": None,
        "memory": None,
        "compile_output": None,
        "message": None,
    }


@pytest.fixture(autouse=True)
def _judge0_disabled():
    """确保测试中全局 Judge0 未配置（端点冒烟走降级路径）。"""
    service.configure_judge0("")
    yield
    service.configure_judge0("")


# ── 竞技场：Judge0 正常判题 ─────────────────────────────


class TestArenaJudge0:
    @pytest.mark.asyncio
    async def test_all_pass_returns_solved_with_full_output(self):
        judge = FakeJudge(batch_result=_batch(5, 5))
        result = await service.judge_arena_code_submit(
            FIXED_0091, "DEBUG-0091", "failing", SEED_0091, "python", judge=judge
        )
        assert result["passed"] == 5
        assert result["total"] == 5
        assert result["solved"] is True
        assert result["score_delta"] == service.ARENA_SOLVED_SCORE_DELTA
        assert "PASSED" in result["output"] and "通过 5 个" in result["output"]

    @pytest.mark.asyncio
    async def test_partial_pass_not_solved(self):
        judge = FakeJudge(batch_result=_batch(3, 5))
        result = await service.judge_arena_code_submit(
            FIXED_0091, "DEBUG-0091", "failing", SEED_0091, "python", judge=judge
        )
        assert result["passed"] == 3
        assert result["total"] == 5
        assert result["solved"] is False
        assert result["score_delta"] == 0
        assert "FAILED" in result["output"]

    @pytest.mark.asyncio
    async def test_compile_error_returns_zero_passed(self):
        judge = FakeJudge(batch_result=_compile_error_batch(5))
        result = await service.judge_arena_code_submit(
            FIXED_0091, "DEBUG-0091", "failing", SEED_0091, "python", judge=judge
        )
        assert result["passed"] == 0
        assert result["solved"] is False
        # 消息来自 Judge0Service 的状态翻译（STATUS_MESSAGES[5] = "⚠️ Compilation Error"）
        assert "Compilation Error" in result["output"]

    @pytest.mark.asyncio
    async def test_driver_appended_and_language_mapped(self):
        judge = FakeJudge(batch_result=_batch(5, 5))
        await service.judge_arena_code_submit(
            FIXED_0091, "DEBUG-0091", "failing", SEED_0091, "python", judge=judge
        )
        call = judge.calls[0]
        # 驱动追加在用户代码之后：stdin 读 JSON 数组，调用 median 打印结果
        assert "print(median(json.loads(sys.stdin.read())))" in call["code"]
        assert call["code"].startswith(FIXED_0091)
        assert call["language_id"] == 71  # LANGUAGE_PYTHON
        assert call["test_cases"] == SEED_0091

    @pytest.mark.asyncio
    async def test_unknown_challenge_without_driver_falls_back(self):
        judge = FakeJudge(batch_result=_batch(5, 5))
        result = await service.judge_arena_code_submit(
            FIXED_0091, "DEBUG-9999", "failing", SEED_0091, "python", judge=judge
        )
        assert judge.calls == []  # 无驱动 → 不发起 Judge0 调用
        assert result == {"passed": 0, "total": 0, "output": "failing",
                          "solved": False, "score_delta": 0}


# ── 竞技场：降级路径 ─────────────────────────────────────


class TestArenaFallback:
    @pytest.mark.asyncio
    async def test_judge0_not_configured_falls_back_to_keyword(self):
        # judge=None 等价于全局未配置（_judge0 为 None）
        result = await service.judge_arena_code_submit(
            FIXED_0091, "DEBUG-0091", "failing", SEED_0091, "python", judge=None
        )
        assert result["solved"] is True
        assert result["passed"] == 5
        assert result["score_delta"] == 23

    @pytest.mark.asyncio
    async def test_judge0_error_falls_back_to_keyword(self):
        judge = FakeJudge(error=RuntimeError("connection refused"))
        result = await service.judge_arena_code_submit(
            FIXED_0091, "DEBUG-0091", "failing", SEED_0091, "python", judge=judge
        )
        assert result["solved"] is True  # 降级到关键字判定
        assert result["passed"] == 5

    @pytest.mark.asyncio
    async def test_no_test_cases_falls_back_without_calling_judge0(self):
        judge = FakeJudge(batch_result=_batch(5, 5))
        result = await service.judge_arena_code_submit(
            FIXED_0091, "DEBUG-0091", "failing", None, "python", judge=judge
        )
        assert judge.calls == []
        assert result["solved"] is True


# ── 认证 code 题：Judge0 判分与降级 ──────────────────────


class TestCertCodeJudge0:
    @pytest.mark.asyncio
    async def test_all_pass_is_correct_with_c_language(self):
        judge = FakeJudge(batch_result=_batch(4, 4))
        ok = await service.judge_cert_code_answer(
            "void swap(int *a, int *b) { int t = *a; *a = *b; *b = t; }",
            "cert-pointer",
            "q5",
            ["*a=*b", "*b="],
            SEED_Q5,
            judge=judge,
        )
        assert ok is True
        call = judge.calls[0]
        assert call["language_id"] == 50  # LANGUAGE_C
        # C 驱动追加在用户代码之后：读取两个 int 并调用 swap
        assert "swap(&x, &y)" in call["code"]
        assert call["test_cases"] == SEED_Q5

    @pytest.mark.asyncio
    async def test_partial_pass_is_incorrect(self):
        judge = FakeJudge(batch_result=_batch(2, 4))
        ok = await service.judge_cert_code_answer(
            "void swap(int *a, int *b) {}",
            "cert-pointer",
            "q5",
            ["*a=*b", "*b="],
            SEED_Q5,
            judge=judge,
        )
        assert ok is False  # 部分通过 ≠ 正确

    @pytest.mark.asyncio
    async def test_judge0_error_falls_back_to_includes(self):
        judge = FakeJudge(error=RuntimeError("timeout"))
        answer = "void swap(int *a, int *b) {\n    int t = *a;\n    *a = *b;\n    *b = t;\n}"
        ok = await service.judge_cert_code_answer(
            answer, "cert-pointer", "q5", ["*a=*b", "*b="], SEED_Q5, judge=judge
        )
        assert ok is True  # 降级：包含全部关键片段

    @pytest.mark.asyncio
    async def test_no_test_cases_falls_back_to_includes(self):
        judge = FakeJudge(batch_result=_batch(4, 4))
        # 答案不含关键片段 → 降级判错，且不调用 Judge0
        ok = await service.judge_cert_code_answer(
            "void swap(int *a, int *b) {}", "cert-pointer", "q5", ["*a=*b", "*b="], None, judge=judge
        )
        assert judge.calls == []
        assert ok is False


# ── mcq 判分不回归 ──────────────────────────────────────


class TestCertMcq:
    def test_exact_match_is_correct(self):
        assert service.judge_cert_answer("mcq", "10", "10", None) is True

    def test_wrong_answer_is_incorrect(self):
        assert service.judge_cert_answer("mcq", "5", "10", None) is False

    def test_empty_correct_answer_is_incorrect(self):
        assert service.judge_cert_answer("mcq", "10", None, None) is False


# ── 种子数据 test_cases 结构合法 ─────────────────────────


class TestSeedTestCases:
    def test_arena_challenges_have_valid_test_cases(self):
        for c in ARENA_CHALLENGES:
            tc = c.get("test_cases")
            assert tc, f"{c['id']} 缺少 test_cases"
            assert len(tc) >= 2
            for case in tc:
                assert set(case.keys()) == {"input", "expected_output"}
                assert isinstance(case["input"], str)
                assert isinstance(case["expected_output"], str)
            # 每个挑战都有对应的判题驱动与语言映射（Judge0 路径可执行）
            assert c["id"] in service.ARENA_DRIVERS
            assert c["language"] in service.ARENA_LANGUAGE_IDS

    def test_cert_code_questions_have_valid_test_cases(self):
        for row in CERT_QUESTIONS:
            exam_id, qid, kind = row[0], row[1], row[2]
            tc = row[8]
            if kind == "mcq":
                assert tc is None, f"{exam_id}:{qid} mcq 题不应有 test_cases"
                continue
            assert tc, f"{exam_id}:{qid} code 题缺少 test_cases"
            assert f"{exam_id}:{qid}" in service.CERT_CODE_DRIVERS
            assert exam_id in service.CERT_EXAM_LANGUAGE_IDS
            for case in tc:
                assert set(case.keys()) == {"input", "expected_output"}
                assert isinstance(case["input"], str)
                assert isinstance(case["expected_output"], str)


# ── 端点冒烟（全局 Judge0 未配置时走降级）───────────────


class TestJudge0EndpointFallback:
    @pytest.mark.asyncio
    async def test_arena_run_falls_back_when_judge0_unconfigured(
        self, client, db_session, auth_headers
    ):
        await seed_deck(db_session)
        resp = await client.post(
            "/api/arena/run",
            json={"challenge_id": "DEBUG-0091", "code": FIXED_0091},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        # 契约字段保持不变（ArenaRunResult + new_badges）
        assert {"passed", "total", "output", "solved", "score_delta", "new_badges"} <= set(data)
        assert data["solved"] is True
        assert data["passed"] == 5
        assert data["score_delta"] == 23

    @pytest.mark.asyncio
    async def test_cert_submit_falls_back_when_judge0_unconfigured(
        self, client, db_session, auth_headers
    ):
        await seed_deck(db_session)
        resp = await client.post(
            "/api/certification/submit",
            json={
                "exam_id": "cert-pointer",
                "answers": [
                    {"question_id": "q1", "answer": "10"},
                    {"question_id": "q2", "answer": "悬空指针（值不变但目标已释放）"},
                    {"question_id": "q3", "answer": "值相等"},
                    {"question_id": "q4", "answer": "4"},
                    # code 题（q5）：Judge0 未配置 → 关键片段降级，答案包含全部片段
                    {
                        "question_id": "q5",
                        "answer": "void swap(int *a, int *b) {\n    int t = *a;\n    *a = *b;\n    *b = t;\n}",
                    },
                    # q6 未作答 → 判错
                    {"question_id": "q6", "answer": ""},
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        # 契约字段保持不变（CertResult）
        assert {"score", "passed", "certificate", "per_question", "new_badges"} <= set(data)
        per_q = {p["question_id"]: p["correct"] for p in data["per_question"]}
        assert per_q["q1"] is True and per_q["q2"] is True and per_q["q3"] is True
        assert per_q["q4"] is True and per_q["q5"] is True and per_q["q6"] is False
        assert data["score"] == round(5 / 6 * 100)  # 5/6 对
