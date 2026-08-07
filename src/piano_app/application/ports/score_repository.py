from typing import Protocol

from piano_app.domain.score import Score
from piano_app.domain.score.document import ScoreDocument


class ScoreNotFoundError(Exception):
    """Raised by a ``ScoreRepository`` implementation when a score id has no
    canon row."""

    def __init__(self, *, score_id: str) -> None:
        super().__init__(f"No score with id {score_id!r}.")
        self.score_id: str = score_id


class ScoreRepository(Protocol):
    """Durable canon storage: saved scores and their derived branches.

    Unlike a draft, a canon row has no undo/redo journal — a "save" writes a
    new current state, it doesn't append to a history. Lineage (``derived_from``)
    and ownership are first-class here, unlike ``DraftHistory``/``DraftArchive``.

    The repository lifetime is scoped by the surrounding unit of work.
    """

    async def get(self, *, score_id: str) -> Score | None: ...

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

    async def update(self, *, score_id: str, document: ScoreDocument) -> None:
        """Overwrites a canon row's current document (promotion). Caller is
        responsible for the owner-only check — this port does not know identity."""
        ...
