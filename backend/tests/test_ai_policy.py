from unittest.mock import AsyncMock, patch

import pytest

from app.services.ai import _build_exercise_hint_prompt
from app.services.ai_policy import (
    AIFeature,
    AI_HINT_COSTS,
    AIPolicy,
    get_ai_policy,
)


def test_challenge_hint_light_policy_has_expected_cost():
    policy = get_ai_policy(AIFeature.CHALLENGE_HINT, hint_level="light")
    assert policy.cost == AI_HINT_COSTS["light"]


def test_challenge_hint_medium_policy_has_expected_cost():
    policy = get_ai_policy(AIFeature.CHALLENGE_HINT, hint_level="medium")
    assert policy.cost == AI_HINT_COSTS["medium"]


def test_challenge_hint_deep_policy_has_expected_cost():
    policy = get_ai_policy(AIFeature.CHALLENGE_HINT, hint_level="deep")
    assert policy.cost == AI_HINT_COSTS["deep"]


@pytest.mark.parametrize("hint_level", ["light", "medium", "deep"])
def test_cached_challenge_hint_policy_is_free_for_all_levels(hint_level):
    policy = get_ai_policy(AIFeature.CHALLENGE_HINT, hint_level=hint_level, cached=True)
    assert policy.cost == 0
    assert policy.cached is True


@pytest.mark.parametrize(
    "hint_level, expected_category",
    [
        ("light", "ai_hint_light"),
        ("medium", "ai_hint_medium"),
        ("deep", "ai_hint_deep"),
    ],
)
def test_challenge_hint_policy_category_matches_spend_category(hint_level, expected_category):
    policy = get_ai_policy(AIFeature.CHALLENGE_HINT, hint_level=hint_level)
    assert policy.category == expected_category


def test_general_chat_policy_is_out_of_demo_scope_and_free():
    policy = get_ai_policy(AIFeature.GENERAL_CHAT)
    assert policy.feature == AIFeature.GENERAL_CHAT
    assert policy.demo_scope == "out_of_demo_scope"
    assert policy.cost == 0


def test_reflection_prompt_policy_is_controlled_demo_scope():
    policy = get_ai_policy(AIFeature.REFLECTION_PROMPT)
    assert policy.feature == AIFeature.REFLECTION_PROMPT
    assert policy.demo_scope == "controlled"
    assert policy.cost == 0


def test_unknown_hint_level_falls_back_to_light_cost():
    # Tests direct policy usage; route-level validation uses Literal["light", "medium", "deep"].
    assert get_ai_policy(AIFeature.CHALLENGE_HINT, hint_level="unknown").cost == AI_HINT_COSTS["light"]


def test_light_hint_prompt_gives_high_level_direction_without_code():
    prompt = _build_exercise_hint_prompt(
        exercise_title="Two Sum",
        exercise_description="Find two numbers that add up to target.",
        difficulty=3,
        knowledge_points=["hash map"],
        hint_level="light",
    )
    assert "轻度提示" in prompt
    assert "只给思路方向" in prompt
    assert "不要写出完整代码" in prompt


def test_medium_hint_prompt_gives_pseudo_code_framework():
    prompt = _build_exercise_hint_prompt(
        exercise_title="Two Sum",
        exercise_description="Find two numbers that add up to target.",
        difficulty=3,
        knowledge_points=["hash map"],
        hint_level="medium",
    )
    assert "中度提示" in prompt
    assert "伪代码框架" in prompt
    assert "关键实现部分用注释代替" in prompt


def test_deep_hint_prompt_gives_full_analysis_with_annotated_reference():
    prompt = _build_exercise_hint_prompt(
        exercise_title="Two Sum",
        exercise_description="Find two numbers that add up to target.",
        difficulty=3,
        knowledge_points=["hash map"],
        hint_level="deep",
    )
    assert "深度解析" in prompt
    assert "带注释的参考代码框架" in prompt
    assert "不要直接给出完整可运行的答案" in prompt


@pytest.mark.asyncio
async def test_hint_router_uses_policy_service_for_cost_lookup(client, auth_headers):
    with patch("app.routers.ai.get_ai_policy") as mock_get_policy:
        mock_get_policy.return_value = AIPolicy(
            feature=AIFeature.CHALLENGE_HINT,
            cost=999,
            cached=False,
            demo_scope="controlled",
        )
        response = await client.get(
            "/api/ai/exercise-hint/cache/ex1/light",
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["cached"] is False
    assert data["cost"] == 999
    mock_get_policy.assert_called_once_with(
        AIFeature.CHALLENGE_HINT, hint_level="light"
    )


@pytest.mark.asyncio
async def test_stream_hint_insufficient_cores_returns_sse_error_and_skips_ai_stream(
    client, auth_user, auth_headers
):
    """Insufficient cores for a new hint emits INSUFFICIENT_CORES SSE and never streams AI."""
    policy = AIPolicy(
        feature=AIFeature.CHALLENGE_HINT,
        cost=7,
        cached=False,
        demo_scope="controlled",
        hint_level="medium",
    )

    with patch("app.routers.ai.get_ai_policy", return_value=policy) as mock_get_policy:
        with patch(
            "app.services.core_service.CoreService.spend_cores",
            new=AsyncMock(side_effect=ValueError("Insufficient cores. Have 0, need 7")),
        ) as mock_spend:
            with patch(
                "app.routers.ai.ai_service.stream_exercise_hint",
                new=AsyncMock(),
            ) as mock_stream:
                response = await client.post(
                    "/api/ai/exercise-hint/stream",
                    json={
                        "exercise_id": "ex-insufficient",
                        "exercise_title": "Two Sum",
                        "exercise_description": "Find two numbers.",
                        "difficulty": 3,
                        "knowledge_points": ["hash map"],
                        "hint_level": "medium",
                        "code_template": "",
                        "sample_input": "",
                        "sample_output": "",
                    },
                    headers=auth_headers,
                )

    assert response.status_code == 200
    body = response.text
    assert "INSUFFICIENT_CORES" in body
    mock_get_policy.assert_called_once_with(
        AIFeature.CHALLENGE_HINT, hint_level="medium"
    )
    mock_spend.assert_awaited_once_with(
        user_id=auth_user.id,
        amount=7,
        category="ai_hint_medium",
        reference_type="exercise_hint",
        reference_id="ex-insufficient",
        description="AI提示 - Two Sum",
    )
    mock_stream.assert_not_awaited()
