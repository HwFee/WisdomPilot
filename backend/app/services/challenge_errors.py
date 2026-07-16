class ChallengeError(Exception):
    """Base class for expected generic challenge failures."""


class InvalidChallengeDefinitionError(ChallengeError):
    def __init__(self, challenge_type: str, requirement: str) -> None:
        super().__init__(
            f"Challenge type {challenge_type!r} requires a positive integer {requirement!r}"
        )
