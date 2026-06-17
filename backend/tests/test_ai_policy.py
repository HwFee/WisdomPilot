from app.services.ai_policy import (
    AIFeature,
    AI_HINT_COSTS,
    get_ai_policy,
)


def test_challenge_hint_policy_costs_match_existing_behavior():
    assert get_ai_policy(AIFeature.CHALLENGE_HINT, hint_level="light").cost == AI_HINT_COSTS["light"]
    assert get_ai_policy(AIFeature.CHALLENGE_HINT, hint_level="medium").cost == AI_HINT_COSTS["medium"]
    assert get_ai_policy(AIFeature.CHALLENGE_HINT, hint_level="deep").cost == AI_HINT_COSTS["deep"]


def test_cached_challenge_hint_is_free():
    policy = get_ai_policy(AIFeature.CHALLENGE_HINT, hint_level="deep", cached=True)
    assert policy.cost == 0
    assert policy.cached is True


def test_general_chat_policy_is_explicitly_classified():
    policy = get_ai_policy(AIFeature.GENERAL_CHAT)
    assert policy.feature == AIFeature.GENERAL_CHAT
    assert policy.demo_scope == "out_of_demo_scope"


def test_unknown_hint_level_falls_back_to_light_cost():
    # Tests direct policy usage; route-level validation uses Literal["light", "medium", "deep"].
    assert get_ai_policy(AIFeature.CHALLENGE_HINT, hint_level="unknown").cost == AI_HINT_COSTS["light"]
