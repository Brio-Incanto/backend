class EditDraftNotFoundError(Exception):
    """Raised when an edit targets a draft id that has no working copy."""

    def __init__(self, *, draft_id: str) -> None:
        super().__init__(f"No draft with id {draft_id!r}.")
        self.draft_id = draft_id


class EditConflictError(Exception):
    """Raised when a draft changes while an edit is being applied."""

    def __init__(self, *, draft_id: str) -> None:
        super().__init__(f"Draft {draft_id!r} changed while the edit was being applied.")
        self.draft_id: str = draft_id


class EditRejectedError(Exception):
    """Raised when an edit is rejected in the mutation engine."""

    def __init__(self, *, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class MissingScoreError(Exception):
    """Raised when the application layer needs a canon score and there isn't
    one — no lookup case vs. no-reference-at-all case, always the same error.
    ``score_id`` is metadata only (may legitimately be unset, e.g. promoting a
    rootless draft), never interpolated into the message."""

    def __init__(self, *, score_id: str | None = None) -> None:
        super().__init__("Score not found.")
        self.score_id: str | None = score_id
