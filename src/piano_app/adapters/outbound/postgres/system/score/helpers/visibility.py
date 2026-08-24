from sqlalchemy import ColumnElement, and_, false, or_

from piano_app.adapters.outbound.postgres.system.schema import ScoreMetaModel


def is_discoverable() -> ColumnElement[bool]:
    """``ScoreMeta.is_discoverable``: published, and its author is still around."""
    return and_(
        ScoreMetaModel.author_id.is_not(None),
        ScoreMetaModel.is_public.is_(True),
    )


def is_readable_by(*, viewer_id: str | None) -> ColumnElement[bool]:
    """Discoverable, or the viewer's own, the read-side counterpart of "you can
    always see what you wrote".
    """

    return and_(
        ScoreMetaModel.author_id.is_not(None),
        or_(
            ScoreMetaModel.is_public.is_(True),
            ScoreMetaModel.author_id == viewer_id if viewer_id is not None else false(),
        ),
    )


def is_authored_by(*, author_id: str) -> ColumnElement[bool]:
    """Rows this actor wrote, public or not."""
    return ScoreMetaModel.author_id == author_id
