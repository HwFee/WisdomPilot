from dataclasses import dataclass
from enum import Enum


# Tiered core costs for challenge hints. These values are intentionally
# small integers so that hint consumption remains cheap but not free.
_LIGHT_HINT_COST = 1
_MEDIUM_HINT_COST = 3
_DEEP_HINT_COST = 5

AI_HINT_COSTS = {
    "light": _LIGHT_HINT_COST,
    "medium": _MEDIUM_HINT_COST,
    "deep": _DEEP_HINT_COST,
}

_DEFAULT_HINT_LEVEL = "light"

_DEMO_SCOPE_CONTROLLED = "controlled"
_DEMO_SCOPE_OUT_OF_DEMO_SCOPE = "out_of_demo_scope"


class AIFeature(str, Enum):
    CHALLENGE_HINT = "challenge_hint"
    # GENERAL_CHAT is classified as out_of_demo_scope because the deterministic
    # teaching backbone is the defense focus. General chat is a convenience
    # feature outside the controlled demo scope and is not part of the official
    # defense demo flow.
    GENERAL_CHAT = "general_chat"
    REFLECTION_PROMPT = "reflection_prompt"


@dataclass(frozen=True)
class AIPolicy:
    feature: AIFeature
    cost: int
    cached: bool = False
    admin_only: bool = False
    demo_scope: str = _DEMO_SCOPE_CONTROLLED


def get_ai_policy(
    feature: AIFeature,
    *,
    hint_level: str = _DEFAULT_HINT_LEVEL,
    cached: bool = False,
) -> AIPolicy:
    if feature == AIFeature.CHALLENGE_HINT:
        cost = 0 if cached else AI_HINT_COSTS.get(hint_level, _LIGHT_HINT_COST)
        return AIPolicy(
            feature=feature,
            cost=cost,
            cached=cached,
            demo_scope=_DEMO_SCOPE_CONTROLLED,
        )

    if feature == AIFeature.GENERAL_CHAT:
        return AIPolicy(
            feature=feature,
            cost=0,
            demo_scope=_DEMO_SCOPE_OUT_OF_DEMO_SCOPE,
        )

    if feature == AIFeature.REFLECTION_PROMPT:
        return AIPolicy(
            feature=feature,
            cost=0,
            demo_scope=_DEMO_SCOPE_CONTROLLED,
        )

    raise ValueError(f"Unsupported AI feature: {feature}")
