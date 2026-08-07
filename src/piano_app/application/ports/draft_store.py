from dataclasses import dataclass
from typing import Protocol

from piano_app.domain.score.document import ScoreDocument


class DraftNotFoundError(Exception):
    """Raised by a ``DraftStore``/``DraftHistory`` implementation when a draft id has
    no working copy."""

    def __init__(self, *, draft_id: str) -> None:
        super().__init__(f"No draft with id {draft_id!r}.")
        self.draft_id: str = draft_id


class DraftVersionClashError(Exception):
    """Raised when a draft operation is based on an outdated version."""

    def __init__(self, *, draft_id: str, version: int | None) -> None:
        message: str = (
            f"Draft {draft_id!r} already exists."
            if version is None
            else f"Version {version} of draft {draft_id!r} has already moved forward."
        )
        super().__init__(message)
        self.draft_id: str = draft_id
        self.version: int | None = version


@dataclass(frozen=True, slots=True, kw_only=True)
class VersionedDraftDocument:
    """A score document paired with the draft version it was loaded from."""

    draft_id: str
    document: ScoreDocument
    version: int
    author_id: str
    ref_score_id: str | None


class DraftStore(Protocol):
    """Holds the transient working copy (draft) of each editing session, keyed by
    draft id.

    Drafts are either branches from existing scores or a completely new score
    branched from an empty document.
    """

    async def create(
        self,
        *,
        author_id: str,
        ref_score_id: str | None,
        document: ScoreDocument,
    ) -> VersionedDraftDocument:
        """Creates initial draft with a fresh document."""
        ...

    async def load(self, *, draft_id: str) -> VersionedDraftDocument:
        """Raises ``DraftNotFoundError`` if ``draft_id`` has no working copy."""
        ...
