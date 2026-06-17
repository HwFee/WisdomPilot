from unittest.mock import MagicMock

from app.services.challenge_path.responses import (
    map_exercise_detail_response,
    map_switch_response,
)


def _make_exercise(**overrides):
    exercise = MagicMock()
    exercise.id = overrides.get("id", 42)
    exercise.z_id = overrides.get("z_id", "z-42")
    exercise.type = overrides.get("type", "programming")
    exercise.difficulty = overrides.get("difficulty", 3)
    exercise.knowledge_points = overrides.get("knowledge_points", ["hash map"])
    exercise.content = overrides.get("content", {
        "title": "Two Sum",
        "text": "Find two numbers that add up to target.",
        "options": [],
        "code_template": "def two_sum(nums, target):",
        "description": "Classic array problem",
        "samples": [{"input": "[2,7,11,15]", "output": "[0,1]"}],
        "input_format": "First line: n",
        "output_format": "Indices",
        "sample_input": "4\n2 7 11 15\n9",
        "sample_output": "0 1",
        "time_limit": 1000,
        "memory_limit": 256,
    })
    exercise.test_cases = overrides.get("test_cases", [{"input": "in", "output": "out"}])
    return exercise


class TestMapSwitchResponse:
    def test_maps_exercise_with_summary_fields(self):
        exercise = _make_exercise()
        service_result = {
            "current_index": 2,
            "exercise": exercise,
            "is_unlocked": True,
            "is_completed": False,
            "is_correct": False,
            "saved_code": "print('hi')",
            "current_language": "python",
        }
        mapped = map_switch_response(service_result)

        assert mapped["current_index"] == 2
        assert mapped["is_unlocked"] is True
        assert mapped["is_completed"] is False
        assert mapped["is_correct"] is False
        assert mapped["saved_code"] == "print('hi')"
        assert mapped["current_language"] == "python"

        ex = mapped["exercise"]
        assert ex["id"] == 42
        assert ex["title"] == "Two Sum"
        assert ex["type"] == "programming"
        assert ex["difficulty"] == 3
        assert ex["knowledge_points"] == ["hash map"]
        assert "text" in ex["content"]
        assert "code_template" in ex["content"]
        assert ex["test_cases"] is not None

    def test_handles_missing_exercise(self):
        service_result = {
            "current_index": 0,
            "is_unlocked": True,
        }
        mapped = map_switch_response(service_result)
        assert "exercise" not in mapped or mapped.get("exercise") is None


class TestMapExerciseDetailResponse:
    def test_maps_full_detail_with_all_content_fields(self):
        exercise = _make_exercise()
        service_result = {
            "exercise": exercise,
            "exercise_index": 5,
            "is_unlocked": True,
            "is_completed": True,
            "is_correct": True,
            "saved_code": "def solve(): pass",
            "current_language": "python",
        }
        mapped = map_exercise_detail_response(service_result, total_exercises=10)

        assert mapped["exercise_index"] == 5
        assert mapped["is_unlocked"] is True
        assert mapped["is_completed"] is True
        assert mapped["is_correct"] is True
        assert mapped["saved_code"] == "def solve(): pass"
        assert mapped["current_language"] == "python"
        assert mapped["total_exercises"] == 10

        ex = mapped["exercise"]
        assert ex["id"] == 42
        assert ex["title"] == "Two Sum"
        assert ex["type"] == "programming"
        assert ex["difficulty"] == 3
        assert ex["knowledge_points"] == ["hash map"]
        content = ex["content"]
        assert content["input_format"] == "First line: n"
        assert content["output_format"] == "Indices"
        assert content["sample_input"] == "4\n2 7 11 15\n9"
        assert content["sample_output"] == "0 1"
        assert content["time_limit"] == 1000
        assert content["memory_limit"] == 256
        assert ex["test_cases"] is not None

    def test_non_programming_type_hides_test_cases(self):
        exercise = _make_exercise(type="choice", test_cases=[])
        service_result = {
            "exercise": exercise,
            "exercise_index": 0,
            "is_unlocked": True,
            "is_completed": False,
            "is_correct": False,
            "saved_code": None,
            "current_language": None,
        }
        mapped = map_exercise_detail_response(service_result, total_exercises=5)
        assert mapped["exercise"]["test_cases"] is None
