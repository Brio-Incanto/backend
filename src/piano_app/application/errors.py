class DraftNotFoundError(Exception):
    """Raised when a draft id has no working copy in the store."""

    def __init__(self, *, draft_id: str) -> None:
        super().__init__(f"No draft with id {draft_id!r}.")
        self.draft_id = draft_id


class EditRejectedError(Exception):
    """Raised when an edit is rejected in the mutation engine."""

    def __init__(self, *, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class EditHistoryEmptyError(Exception):
    """Raised when an edit cannot be undone or redone because the edit history is empty."""

    def __init__(self, *, operation: str) -> None:
        super().__init__(f"Nothing to {operation}.")
        self.operation = operation
