class ChallengeError(Exception):
    """Base class for expected generic challenge failures."""


class InvalidChallengeDefinitionError(ChallengeError):
    def __init__(self, challenge_type: str, requirement: str) -> None:
        super().__init__(
            f"Challenge type {challenge_type!r} requires a positive integer {requirement!r}"
        )


class ChallengeNotFoundError(ChallengeError):
    def __init__(self, challenge_id: int) -> None:
        super().__init__(f"Challenge {challenge_id} not found")


class ChallengeNotStartedError(ChallengeError):
    def __init__(self) -> None:
        super().__init__("Challenge not started")


class ChallengeAlreadyCompletedError(ChallengeError):
    def __init__(self) -> None:
        super().__init__("Challenge already completed")


class InvalidProgressDeltaError(ChallengeError):
    def __init__(self) -> None:
        super().__init__("Progress delta must be a positive integer")
