from typing import Protocol

from piano_app.domain.score import Score, ScoreMeta
from piano_app.domain.score.document import ScoreDocument


class ScoreNotFoundError(Exception):
    """Raised by a ``ScoreRepository`` implementation when a score id has no
    canon row."""

    def __init__(self, *, score_id: str) -> None:
        super().__init__(f"No score with id {score_id!r}.")
        self.score_id: str = score_id


class ScoreVersionClashError(Exception):
    """Raised by a ``ScoreRepository`` implementation when a concurrent write to
    the same score already took the version this write was trying to append."""

    def __init__(self, *, score_id: str, version: int) -> None:
        super().__init__(f"Version {version} of score {score_id!r} has already moved forward.")
        self.score_id: str = score_id
        self.version: int = version


class ScoreRepository(Protocol):
    """Durable canon storage: saved scores and their derived branches.

    Unlike a draft, a canon row has no undo/redo journal — a "save" writes a
    new current state, it doesn't append to a history. Lineage (``derived_from``)
    and ownership are first-class here, unlike ``DraftHistory``/``DraftArchive``.

    The repository lifetime is scoped by the surrounding unit of work.
    """

    async def get(self, *, score_id: str, viewer_id: str | None) -> Score | None:
        """Returns the score if it's public OR ``viewer_id`` is its author; ``None``
        otherwise — for a missing row AND a private-and-not-yours row alike (never
        distinguishable, so callers don't leak a private score's existence).
        ``viewer_id=None`` is an anonymous caller — only ever sees public scores."""
        ...

    async def get_meta(self, *, score_id: str) -> ScoreMeta | None:
        """Loads a score's metadata WITHOUT its document and WITHOUT applying any
        visibility rule — the raw state, for a caller that is about to decide
        something from it (``ScoreMeta``'s own state rules, plus the application
        layer's identity check). ``None`` only ever means "no such row"."""
        ...

    async def get_meta_for_update(self, *, score_id: str) -> ScoreMeta | None:
        """``get_meta``, but locking the row for the rest of the transaction.

        The check-then-write flows (promote, metadata edits) decide from the
        metadata and then write; without the lock another writer can change the
        author or the publication state in between and the decision is applied
        to a state that no longer holds. The lock is per-score, so writers to
        other scores are unaffected."""
        ...

    async def exists(self, *, score_id: str) -> bool: ...

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

    async def update_content(self, *, score_id: str, document: ScoreDocument) -> None:
        """Overwrites a canon row's current document (promotion)."""
        ...

    # The writes below are UNAUTHORIZED primitives on purpose: whether this actor
    # may write is an identity question, decided by the caller from a
    # `get_meta_for_update` snapshot taken in the same transaction — which is what
    # makes the decision still hold when the write lands. Keeping the rule out of
    # here is what lets an admin override exist later without a second write path.
    async def set_title(self, *, score_id: str, title: str) -> None:
        """Raises ``ScoreNotFoundError`` if the row is gone."""
        ...

    async def set_composer(self, *, score_id: str, composer: str | None) -> None:
        """``composer=None`` clears it — a legitimate target value, not a
        "leave alone" marker. Raises ``ScoreNotFoundError`` if the row is gone."""
        ...

    async def set_visibility(self, *, score_id: str, is_public: bool) -> None:
        """Raises ``ScoreNotFoundError`` if the row is gone."""
        ...
