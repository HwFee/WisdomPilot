from __future__ import annotations

from typing import TYPE_CHECKING

from app.models.exercise import Exercise

if TYPE_CHECKING:
    pass

_FALLBACK_TITLE_MAX_LENGTH = 50
_EXERCISE_TYPE_PROGRAMMING = "programming"


def map_exercise_summary(exercise: Exercise, index: int | None = None) -> dict:
    content = exercise.content or {}
    fallback_title = f"题目 {index + 1}" if index is not None else f"题目 {exercise.id}"
    text = content.get("text", "")
    return {
        "id": exercise.id,
        "z_id": exercise.z_id,
        "title": content.get("title", "")
        or (text[:_FALLBACK_TITLE_MAX_LENGTH] if text else fallback_title),
        "type": exercise.type,
        "difficulty": exercise.difficulty,
        "knowledge_points": exercise.knowledge_points or [],
        "content": {
            "text": content.get("text", ""),
            "title": content.get("title", ""),
            "options": content.get("options", []),
            "code_template": content.get("code_template"),
            "description": content.get("description"),
            "samples": content.get("samples", []),
        },
        "test_cases": exercise.test_cases
        if exercise.type == _EXERCISE_TYPE_PROGRAMMING
        else None,
    }


def map_switch_response(result: dict) -> dict:
    exercise = result.get("exercise")
    mapped = {
        key: value
        for key, value in result.items()
        if key != "exercise"
    }
    if exercise is not None:
        mapped["exercise"] = map_exercise_summary(exercise)
    return mapped


def map_exercise_detail_response(result: dict, total_exercises: int) -> dict:
    exercise = result.get("exercise")
    if exercise is None:
        return {
            "exercise": None,
            "exercise_index": result.get("exercise_index"),
            "is_unlocked": result.get("is_unlocked"),
            "is_completed": result.get("is_completed"),
            "is_correct": result.get("is_correct"),
            "saved_code": result.get("saved_code"),
            "current_language": result.get("current_language"),
            "total_exercises": total_exercises,
        }
    content = exercise.content or {}
    return {
        "exercise": {
            "id": exercise.id,
            "title": content.get("title", ""),
            "type": exercise.type,
            "difficulty": exercise.difficulty,
            "knowledge_points": exercise.knowledge_points or [],
            "content": {
                "text": content.get("text", ""),
                "title": content.get("title", ""),
                "description": content.get("description", ""),
                "options": content.get("options", []),
                "code_template": content.get("code_template", ""),
                "input_format": content.get("input_format", ""),
                "output_format": content.get("output_format", ""),
                "sample_input": content.get("sample_input", ""),
                "sample_output": content.get("sample_output", ""),
                "samples": content.get("samples", []),
                "time_limit": content.get("time_limit", 1000),
                "memory_limit": content.get("memory_limit", 256),
            },
            "test_cases": exercise.test_cases
            if exercise.type == _EXERCISE_TYPE_PROGRAMMING
            else None,
        },
        "exercise_index": result["exercise_index"],
        "is_unlocked": result["is_unlocked"],
        "is_completed": result["is_completed"],
        "is_correct": result["is_correct"],
        "saved_code": result["saved_code"],
        "current_language": result["current_language"],
        "total_exercises": total_exercises,
    }
