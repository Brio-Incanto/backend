"""SQL translations of the score-visibility rules that ``ScoreMeta`` defines.

The rules themselves live in the domain (``ScoreMeta.is_discoverable`` and
friends) — that is the one place they are *stated*. Listings cannot use those
predicates directly: keyset pagination has to know how many rows survive
filtering BEFORE ``LIMIT``, so the filter has to run in the database. What lives
here is therefore only the translation, kept in one place so the same rule isn't
spelled out again in every query, and pinned to the domain by an equivalence
test (see the visibility tests).

Anything that loads a score and then decides — every command path — skips this
module entirely and asks ``ScoreMeta`` instead.
"""

from sqlalchemy import ColumnElement, and_, false, or_

from piano_app.adapters.outbound.postgres.schema.core import ScoreMetaORM


def is_discoverable() -> ColumnElement[bool]:
    """``ScoreMeta.is_discoverable``: published, and its author is still around.

    ``is_public`` on its own is not enough — it keeps recording the author's
    intent after they are gone, so an orphaned row would otherwise stay in the
    public catalogue forever."""
    return and_(
        ScoreMetaORM.author_id.is_not(None),
        ScoreMetaORM.is_public.is_(True),
    )


def is_readable_by(*, viewer_id: str | None) -> ColumnElement[bool]:
    """Discoverable, or the viewer's own — the read-side counterpart of "you can
    always see what you wrote".

    ``viewer_id`` is compared with an explicit ``false()`` branch when absent:
    ``author_id == None`` would be rewritten by SQLAlchemy into ``author_id IS
    NULL``, which is exactly the orphaned rows, and would hand every anonymous
    caller the private ones."""
    return and_(
        ScoreMetaORM.author_id.is_not(None),
        or_(
            ScoreMetaORM.is_public.is_(True),
            ScoreMetaORM.author_id == viewer_id if viewer_id is not None else false(),
        ),
    )


def is_authored_by(*, author_id: str) -> ColumnElement[bool]:
    """Rows this actor wrote, public or not — "my scores", not a permission
    check (those happen on a loaded ``ScoreMeta``)."""
    return ScoreMetaORM.author_id == author_id
