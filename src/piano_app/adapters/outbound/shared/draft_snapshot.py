from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from piano_app.domain.score.document import ScoreDocument


@dataclass(frozen=True, slots=True, kw_only=True)
class DraftSnapshot:
    """A draft's whole restorable state — its author and undo/redo history,
    mirroring the hot tier one-to-one.

    A plain value model, NOT a domain entity: revisions+cursor is undo/redo
    bookkeeping, not a business concept (the domain has `Score`/`ScoreDocument`,
    no `Draft`). Carries domain `ScoreDocument` objects, not serialized dicts —
    serialization is each adapter's internal business, so the snapshot stays
    framework-free at the port boundary. It's the currency of the cold tier
    (`DraftArchive`) and of spill/hydrate between tiers; the hot tier still moves
    the cursor as its own atomic op (undo/redo), it does NOT round-trip a whole
    snapshot per move.

    Lives in `shared/` (not with the tiering protocols) because several adapters
    depend on it — `tiered_draft_history` speaks it, the Postgres cold adapter
    produces it — so it must not be owned by any one adapter file.
    """

    draft_id: str
    title: str
    author_id: str
    ref_score_id: str | None
    updated_at: datetime
    revisions: tuple[ScoreDocument, ...]
    cursor: int
    version: int

    @classmethod
    def create(
        cls,
        *,
        draft_id: str,
        title: str,
        author_id: str,
        ref_score_id: str | None,
        updated_at: datetime,
        revisions: Sequence[ScoreDocument],
        cursor: int,
        version: int,
    ) -> DraftSnapshot:
        return cls(
            draft_id=draft_id,
            title=title,
            author_id=author_id,
            ref_score_id=ref_score_id,
            updated_at=updated_at,
            revisions=tuple(revisions),
            cursor=cursor,
            version=version,
        )

    def __post_init__(self) -> None:
        if not self.draft_id:
            raise ValueError("draft_id must not be empty")
        if not self.title:
            raise ValueError("title must not be empty")
        if not self.author_id:
            raise ValueError("author_id must not be empty")

        revisions_count: int = len(self.revisions)
        if self.cursor < 0 or self.cursor >= revisions_count:
            raise ValueError(f"cursor out of range: {self.cursor} (n={revisions_count})")
