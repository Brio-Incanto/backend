from typing import Protocol

from piano_app.domain.score import Score, ScoreMeta
from piano_app.domain.score.document import ScoreDocument


class ScoreRepositoryNotFoundError(Exception):
    """Raised when a required score row disappears during a write."""

    def __init__(self, *, score_id: str) -> None:
        super().__init__(f"No stored score with id {score_id!r}.")
        self.score_id: str = score_id


class ScoreRepositoryVersionConflictError(Exception):
    """Raised when a write loses a concurrent score-version race."""

    def __init__(self, *, score_id: str, version: int) -> None:
        super().__init__(f"Stored score {score_id!r} is no longer at version {version}.")
        self.score_id: str = score_id
        self.version: int = version


class ScoreRepository(Protocol):
    """Durable canon storage: saved scores and their derived branches.

    Unlike a draft, a canon row has no undo/redo journal — a "save" writes a
    new current state, it doesn't append to a history. Lineage (``derived_from``)
    and ownership are first-class here, unlike ``DraftHistory``/``DraftArchive``.

    The repository lifetime is scoped by the surrounding unit of work.
    """

    async def get(self, *, score_id: str) -> Score | None: ...

    async def get_meta(self, *, score_id: str) -> ScoreMeta | None: ...

    async def exists(self, *, score_id: str) -> bool: ...

    # TODO settle atomic handling of author/derived-from deletion between
    async def create(
        self,
        *,
        title: str,
        author_id: str,
        composer: str | None = None,
        derived_from_id: str | None = None,
        document: ScoreDocument,
        is_public: bool = False,
    ) -> Score:
        """Creates a new canon row with a server-generated id — no id is ever
        caller-supplied, same as ``DraftStore``/``DraftArchive``. ``derived_from_id=None``
        for a fresh/root score; set (the parent's id — the caller has this from
        context, not a loaded ``Score``) for a branch. An author may have any number
        of branches of the same score, no cardinality limit."""
        ...

    # TODO settle an atomic boundary for the application access check and
    async def update_content(self, *, score_id: str, document: ScoreDocument) -> None:
        # this write without moving authorization policy into the repository.
        """Overwrites a canon row's current document (promotion)."""
        ...

    # The writes below are UNAUTHORIZED primitives on purpose: whether this actor
    # may write is an identity question decided by the caller. Keeping the rule out
    # of here is what lets an admin override exist later without a second write path.
    # TODO settle the same atomic check/write boundary before wiring these methods.
    async def set_title(self, *, score_id: str, title: str) -> None:
        """Raises ``ScoreRepositoryNotFoundError`` if the row is gone."""
        ...

    async def set_composer(self, *, score_id: str, composer: str | None) -> None:
        """``composer=None`` clears it — a legitimate target value, not a
        "leave alone" marker. Raises ``ScoreRepositoryNotFoundError`` if the row is gone."""
        ...

    async def set_visibility(self, *, score_id: str, is_public: bool) -> None:
        """Raises ``ScoreRepositoryNotFoundError`` if the row is gone."""
        ...
