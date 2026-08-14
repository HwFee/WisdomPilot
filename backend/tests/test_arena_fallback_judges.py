"""竞技场降级判题（关键字匹配）测试：ARENA_JUDGES 必须覆盖全部种子挑战。

每个挑战两条断言：
1. 缺陷代码（种子原文）判不通过 —— 保证降级路径不会误放
2. 参考修复实现判通过 —— 保证降级路径在 Judge0 不可用时仍然可攻克

参考修复实现复用 scripts.verify_arena_local 的 REFERENCE_FIXES / C_FIXES，
与「缺陷必失败、修复必全过」的本地实测共用同一份事实源。
"""

from __future__ import annotations

from app.training.seed import ARENA_CHALLENGES
from app.training.service import ARENA_JUDGES, judge_arena_code
from scripts.verify_arena_local import C_FIXES, REFERENCE_FIXES

CHALLENGES_BY_ID = {ch["id"]: ch for ch in ARENA_CHALLENGES}


def _fix_for(challenge_id: str, language: str) -> str:
    fixes = REFERENCE_FIXES if language == "python" else C_FIXES
    return fixes[challenge_id]


def test_fallback_judges_cover_all_seeded_challenges() -> None:
    missing = [ch["id"] for ch in ARENA_CHALLENGES if ch["id"] not in ARENA_JUDGES]
    assert not missing, f"降级判题缺失挑战: {missing}"


def test_fallback_judges_reject_defect_code() -> None:
    for ch in ARENA_CHALLENGES:
        result = judge_arena_code(ch["code"], ch["id"], ch["failing_output"])
        assert not result["solved"], f"{ch['id']} 缺陷代码被误判为攻克"
        assert result["total"] == len(ch["test_cases"]), (
            f"{ch['id']} total={result['total']} 与测试用例数 "
            f"{len(ch['test_cases'])} 不一致"
        )
        assert result["passed"] < result["total"]


def test_fallback_judges_accept_reference_fixes() -> None:
    for ch in ARENA_CHALLENGES:
        fix = _fix_for(ch["id"], ch["language"])
        result = judge_arena_code(fix, ch["id"], ch["failing_output"])
        assert result["solved"], f"{ch['id']} 参考修复未被降级判题接受"
        assert result["passed"] == result["total"]
        assert result["score_delta"] == 23


def test_fallback_judges_do_not_trivially_pass() -> None:
    """空提交 / 无关代码不得判过（降级判定的最低判别力）。"""
    for ch in ARENA_CHALLENGES:
        for bogus in ("", "pass", "# 不会写", ch["code"]):
            result = judge_arena_code(bogus, ch["id"], ch["failing_output"])
            assert not result["solved"], (
                f"{ch['id']} 对无关提交 {bogus!r} 误判攻克"
            )
