from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from piano_app.application.ports.shared.pagination import Page


@dataclass(frozen=True, slots=True, kw_only=True)
class ScoreMetaItem:
    """A lightweight catalog row — metadata only, NEVER the score document. Listing
    endpoints read this without deserializing ``score_contents.document``."""

    id: str
    title: str
    composer: str | None
    author_id: str | None
    author_name: str | None
    is_public: bool
    created_at: datetime
    updated_at: datetime


class ScoreCatalogQuery(Protocol):
    async def search(
        self,
        *,
        query: str | None,
        limit: int,
        cursor: str | None,
    ) -> Page[ScoreMetaItem]:
        """PUBLIC scores only — no viewer widening, unconditionally anonymous; see
        ``search_mine`` for a caller's own (incl. private) scores.

        ``query`` None/empty is no filter at all; how a non-empty one is matched is the
        read side's business. ``cursor`` is an opaque token from a previous page's
        ``next_cursor`` — it raises ``PaginationCursorDecodingError`` if it cannot be decoded, and
        the caller resets it to None whenever the filter changes."""
        ...

    async def search_mine(
        self,
        *,
        viewer_id: str,
        query: str | None,
        limit: int,
        cursor: str | None,
    ) -> Page[ScoreMetaItem]: ...

    async def search_author_scores(
        self,
        *,
        author_id: str,
        query: str | None,
        limit: int,
        cursor: str | None,
    ) -> Page[ScoreMetaItem]: ...

    async def get_score_branches(
        self,
        *,
        score_id: str,
        viewer_id: str | None,
        limit: int,
        cursor: str | None,
    ) -> Page[ScoreMetaItem]: ...
