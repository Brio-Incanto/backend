class MutationRejectedError(Exception):
    """Raised when a mutation is rejected because it is
    impossible to perform or the domain invariant is violated.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason
