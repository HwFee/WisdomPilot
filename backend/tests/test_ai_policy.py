from unittest.mock import patch

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


def test_cached_challenge_hint_is_free():
    policy = get_ai_policy(AIFeature.CHALLENGE_HINT, hint_level="deep", cached=True)
    assert policy.cost == 0
    assert policy.cached is True


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
