"""Regression tests for challenge submission pass/fail parsing."""

from app.services.arena_infinite import ChallengePathService


def test_all_test_cases_passed_requires_non_empty_list():
    assert ChallengePathService._all_test_cases_passed([]) is False


def test_all_test_cases_passed_accepts_explicit_boolean_true():
    test_results = [
        {"passed": True},
        {"passed": True},
    ]

    assert ChallengePathService._all_test_cases_passed(test_results) is True


def test_all_test_cases_passed_rejects_false_like_strings():
    test_results = [
        {"passed": "false"},
        {"passed": "0"},
    ]

    assert ChallengePathService._all_test_cases_passed(test_results) is False


def test_all_test_cases_passed_rejects_mixed_values():
    test_results = [
        {"passed": True},
        {"passed": "false"},
        {"passed": 0},
    ]

    assert ChallengePathService._all_test_cases_passed(test_results) is False
