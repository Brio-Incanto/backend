from dataclasses import dataclass
from datetime import datetime

from .document import ScoreDocument


@dataclass(slots=True, kw_only=True)
class ScoreMeta:
    """Identity, provenance and publication state of a score — everything
    EXCEPT its document.
    """

    # `is_public` is the author's stored intent and is never rewritten on their
    # way out, so it is not the same question as "should this be listed" — see
    # `is_discoverable`.

    id: str
    title: str
    author_id: str | None
    composer: str | None = None
    derived_from_id: str | None = None
    is_public: bool = False
    created_at: datetime
    updated_at: datetime

    @property
    def is_frozen(self) -> bool:
        """No author left. Two ways in, one resulting state:

        * the author deleted the score, but something still referenced it, so
          the row was kept instead of removed;
        * the author deleted their account, which freezes every score of theirs
          at once.
        """
        return self.author_id is None

    @property
    def is_discoverable(self) -> bool:
        """Whether the score belongs in a public listing. ``is_public`` alone is
        NOT enough: it records the author's stored intent and is never rewritten
        when they leave, so discoverability is derived, not stored."""
        return self.is_public and not self.is_frozen


@dataclass(slots=True, kw_only=True)
class Score:
    """A score's metadata together with its document."""

    meta: ScoreMeta
    document: ScoreDocument

    @property
    def id(self) -> str:
        return self.meta.id

    @property
    def title(self) -> str:
        return self.meta.title

    @property
    def author_id(self) -> str | None:
        return self.meta.author_id

    @property
    def composer(self) -> str | None:
        return self.meta.composer

    @property
    def derived_from_id(self) -> str | None:
        return self.meta.derived_from_id

    @property
    def is_public(self) -> bool:
        return self.meta.is_public

    @property
    def created_at(self) -> datetime:
        return self.meta.created_at

    @property
    def updated_at(self) -> datetime:
        return self.meta.updated_at
