from app.models.exercise import Exercise


_FALLBACK_TITLE_MAX_LENGTH = 50
_EXERCISE_TYPE_PROGRAMMING = "programming"


def map_exercise_summary(exercise: Exercise, index: int | None = None) -> dict:
    content = exercise.content or {}
    fallback_title = f"题目 {index + 1}" if index is not None else f"题目 {exercise.id}"
    text = content.get("text", "")
    return {
        "id": exercise.id,
        "z_id": exercise.z_id,
        "title": content.get("title", "") or (text[:_FALLBACK_TITLE_MAX_LENGTH] if text else fallback_title),
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
        "test_cases": exercise.test_cases if exercise.type == _EXERCISE_TYPE_PROGRAMMING else None,
    }
