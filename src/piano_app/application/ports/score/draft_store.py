from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, Self

from piano_app.domain.score.document import ScoreDocument


class DraftStoreNotFoundError(Exception):
    """Raised when a required draft disappears from the store."""

    def __init__(self, *, draft_id: str) -> None:
        super().__init__(f"No stored draft with id {draft_id!r}.")
        self.draft_id: str = draft_id


class DraftStoreVersionConflictError(Exception):
    """Raised when a write is based on an outdated stored draft version."""

    def __init__(self, *, draft_id: str, version: int | None) -> None:
        super().__init__(f"Stored draft {draft_id!r} is no longer at version {version!r}.")
        self.draft_id: str = draft_id
        self.version: int | None = version


@dataclass(frozen=True, slots=True, kw_only=True)
class DraftMeta:
    """Metadata about a draft."""

    draft_id: str
    title: str
    author_id: str
    ref_score_id: str | None
    updated_at: datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class VersionedDraftDocument:
    """A score document paired with the draft version it was loaded from."""

    meta: DraftMeta
    document: ScoreDocument
    version: int

    @property
    def draft_id(self) -> str:
        return self.meta.draft_id

    @classmethod
    def create(
        cls,
        *,
        draft_id: str,
        title: str,
        author_id: str,
        ref_score_id: str | None,
        updated_at: datetime,
        document: ScoreDocument,
        version: int,
    ) -> Self:
        return cls(
            meta=DraftMeta(
                draft_id=draft_id,
                title=title,
                author_id=author_id,
                ref_score_id=ref_score_id,
                updated_at=updated_at,
            ),
            document=document,
            version=version,
        )


class DraftStore(Protocol):
    """Holds the transient working copy (draft) of each editing session, keyed by
    draft id.

    Drafts are either branches from existing scores or a completely new score
    branched from an empty document.
    """

    async def create(
        self,
        *,
        title: str,
        author_id: str,
        ref_score_id: str | None,
        document: ScoreDocument,
    ) -> VersionedDraftDocument:
        """Creates initial draft with a fresh document."""
        ...

    async def get(self, *, draft_id: str) -> VersionedDraftDocument | None:
        """Returns ``None`` if ``draft_id`` has no working copy."""
        ...

    async def list_by_author(self, *, author_id: str) -> Sequence[DraftMeta]:
        """Returns all drafts created by ``author_id``."""
        ...
