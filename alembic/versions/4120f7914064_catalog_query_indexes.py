"""catalog query indexes

Revision ID: 4120f7914064
Revises: 9697fc113dc0
Create Date: 2026-08-16 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4120f7914064"
down_revision: str | Sequence[str] | None = "9697fc113dc0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # search(): keyset order is (created_at DESC, id DESC) over exactly the rows
    # `search()` filters to (is_public AND author_id IS NOT NULL) — a partial index
    # scoped to that predicate serves the whole query (filter + order) in one scan,
    # and stays small since it excludes every private/orphaned row.
    op.execute(
        "CREATE INDEX ix_scores_public_catalog ON scores (created_at DESC, id DESC) "
        "WHERE is_public AND author_id IS NOT NULL"
    )
    # search_mine(): filters by author_id, same (created_at DESC, id DESC) keyset
    # order. Composite index serves both the equality filter and the ordering, and
    # subsumes the old single-column ix_scores_author_id (same leftmost column) --
    # dropped as redundant, one index to maintain instead of two.
    op.drop_index("ix_scores_author_id", table_name="scores")
    op.execute(
        "CREATE INDEX ix_scores_author_created ON scores (author_id, created_at DESC, id DESC)"
    )
    # get_score_branches(): filters by derived_from, which had NO index at all
    # (Postgres does not auto-index FK columns) -- every branches lookup was a
    # sequential scan over the whole scores table.
    op.create_index(op.f("ix_scores_derived_from"), "scores", ["derived_from"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_scores_derived_from"), table_name="scores")
    op.execute("DROP INDEX IF EXISTS ix_scores_author_created")
    op.create_index(op.f("ix_scores_author_id"), "scores", ["author_id"], unique=False)
    op.execute("DROP INDEX IF EXISTS ix_scores_public_catalog")
