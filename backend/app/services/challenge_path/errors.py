class ChallengeSubmissionError(Exception):
    """Base class for expected Arena submission failures."""


class ChallengeExerciseNotFoundError(ChallengeSubmissionError):
    def __init__(self, exercise_id: int) -> None:
        super().__init__(f"Exercise {exercise_id} not found")


class ChallengeProgressNotFoundError(ChallengeSubmissionError):
    def __init__(self, exercise_id: int) -> None:
        super().__init__(f"Progress record for exercise {exercise_id} not found")


class UnsupportedChallengeLanguageError(ChallengeSubmissionError):
    def __init__(self, language: str) -> None:
        super().__init__(f"Unsupported language for judging: {language}")


class MissingChallengeTestCasesError(ChallengeSubmissionError):
    def __init__(self, exercise_id: int) -> None:
        super().__init__(
            f"Programming exercise {exercise_id} has no backend test cases"
        )


class JudgeUnavailableError(ChallengeSubmissionError):
    def __init__(self, message: str = "Judge service unavailable") -> None:
        super().__init__(message)
