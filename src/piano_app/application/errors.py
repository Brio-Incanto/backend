class DraftNotFoundError(Exception):
    """Raised when a requested draft has no working copy."""

    def __init__(self, *, draft_id: str) -> None:
        super().__init__(f"No draft with id {draft_id!r}.")
        self.draft_id: str = draft_id


class DraftVersionConflictError(Exception):
    """Raised when an operation is based on an outdated draft version."""

    def __init__(self, *, draft_id: str, version: int | None) -> None:
        super().__init__(f"Draft {draft_id!r} changed while the edit was being applied.")
        self.draft_id: str = draft_id
        self.version: int | None = version


class ScoreEditRejectedError(Exception):
    """Raised when a score edit is rejected by the domain."""

    def __init__(self, *, reason: str) -> None:
        super().__init__(reason)
        self.reason: str = reason


class ScoreNotFoundError(Exception):
    """Raised when a canon score can't be found — missing or not visible to
    the caller, always the same error."""

    def __init__(self, *, score_id: str | None = None) -> None:
        super().__init__("Score not found.")
        self.score_id: str | None = score_id


class ScoreVersionConflictError(Exception):
    """Raised when a concurrent write to the same score already took the
    version this write was trying to append."""

    def __init__(self, *, score_id: str, version: int) -> None:
        super().__init__(f"Version {version} of score {score_id!r} has already moved forward.")
        self.score_id: str = score_id
        self.version: int = version


class ScoreNotOwnedError(Exception):
    """Raised when a caller who isn't a score's author tries to change it."""

    def __init__(self, *, score_id: str) -> None:
        super().__init__(f"Score {score_id!r} is not owned by the caller.")
        self.score_id: str = score_id


class UsernameRequiredError(Exception):
    """Raised when sign-in needs a username to create a new account."""

    def __init__(self) -> None:
        super().__init__("A username is required to create an account.")


class UsernameConflictError(Exception):
    """Raised when the requested username is already taken."""

    def __init__(self, *, username: str) -> None:
        super().__init__("Username is already in use.")
        self.username: str = username


class IdentityAlreadyLinkedError(Exception):
    """Raised when a concurrent sign-in race couldn't be resolved."""

    def __init__(self) -> None:
        super().__init__("Identity is already linked to a user.")


class InvalidExternalCredentialError(Exception):
    """Raised when a sign-in credential fails verification."""

    def __init__(self) -> None:
        super().__init__("External identity credential is invalid.")


class InvalidRefreshTokenError(Exception):
    """Raised when a refresh credential is missing, expired, or already rotated."""

    def __init__(self) -> None:
        super().__init__("Refresh token is invalid or expired.")


class InvalidAccessTokenError(Exception):
    """Raised when a bearer access token is missing, malformed, or expired."""

    def __init__(self) -> None:
        super().__init__("Access token is invalid or expired.")


class InvalidPaginationCursorError(Exception):
    """Raised when a client-supplied pagination cursor can't be decoded."""

    def __init__(self) -> None:
        super().__init__("Pagination cursor is invalid.")
