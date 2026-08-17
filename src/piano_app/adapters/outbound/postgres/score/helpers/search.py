"""How a text query narrows a listing. Callers apply this without knowing what it does,
so replacing ILIKE with full-text search is rewriting this function and nothing else."""

from sqlalchemy import ColumnElement, or_, true

from piano_app.adapters.outbound.postgres.schema.core import ScoreMetaORM


def matches(*, query: str | None) -> ColumnElement[bool]:
    """A no-op for an absent query, so callers never branch on whether one was given."""
    if not query:
        return true()

    pattern: str = f"%{query}%"

    return or_(
        ScoreMetaORM.title.ilike(pattern),
        ScoreMetaORM.composer.ilike(pattern),
    )
