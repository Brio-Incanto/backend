class EditDraftNotFoundError(Exception):
    """Raised when an edit targets a draft id that has no working copy."""

    def __init__(self, *, draft_id: str) -> None:
        super().__init__(f"No draft with id {draft_id!r}.")
        self.draft_id = draft_id


class EditRejectedError(Exception):
    """Raised when an edit is rejected in the mutation engine."""

    def __init__(self, *, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason
