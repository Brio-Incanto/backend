from sqlalchemy import ColumnElement, and_, false, or_

from piano_app.adapters.outbound.postgres.system.schema import ScoreMetaORM


def is_discoverable() -> ColumnElement[bool]:
    """``ScoreMeta.is_discoverable``: published, and its author is still around."""
    return and_(
        ScoreMetaORM.author_id.is_not(None),
        ScoreMetaORM.is_public.is_(True),
    )


def is_readable_by(*, viewer_id: str | None) -> ColumnElement[bool]:
    """Discoverable, or the viewer's own, the read-side counterpart of "you can
    always see what you wrote".
    """

    return and_(
        ScoreMetaORM.author_id.is_not(None),
        or_(
            ScoreMetaORM.is_public.is_(True),
            ScoreMetaORM.author_id == viewer_id if viewer_id is not None else false(),
        ),
    )


def is_authored_by(*, author_id: str) -> ColumnElement[bool]:
    """Rows this actor wrote, public or not."""
    return ScoreMetaORM.author_id == author_id
