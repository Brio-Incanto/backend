"""collection score identity

Revision ID: 87c1b5e0c6a2
Revises: 4120f7914064
Create Date: 2026-08-18 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "87c1b5e0c6a2"
down_revision: str | Sequence[str] | None = "4120f7914064"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Give a saved collection item stable identity and cascade hard deletes."""
    op.add_column(
        "collection_scores",
        sa.Column(
            "id",
            sa.String(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
    )
    op.create_unique_constraint(
        "uq_collection_scores_collection_content",
        "collection_scores",
        ["collection_id", "score_content_id"],
    )
    op.drop_constraint("collection_scores_pkey", "collection_scores", type_="primary")
    op.create_primary_key("collection_scores_pkey", "collection_scores", ["id"])

    op.drop_constraint(
        "collection_scores_score_content_id_fkey",
        "collection_scores",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "collection_scores_score_content_id_fkey",
        "collection_scores",
        "score_contents",
        ["score_content_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_index(
        op.f("ix_collection_scores_score_content_id"),
        "collection_scores",
        ["score_content_id"],
        unique=False,
    )
    op.create_index(
        "ix_collection_scores_collection_added",
        "collection_scores",
        ["collection_id", "added_at", "id"],
        unique=False,
    )


def downgrade() -> None:
    """Restore content identity and restrictive content deletion."""
    op.drop_index("ix_collection_scores_collection_added", table_name="collection_scores")
    op.drop_index(
        op.f("ix_collection_scores_score_content_id"),
        table_name="collection_scores",
    )

    op.drop_constraint(
        "collection_scores_score_content_id_fkey",
        "collection_scores",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "collection_scores_score_content_id_fkey",
        "collection_scores",
        "score_contents",
        ["score_content_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.drop_constraint("collection_scores_pkey", "collection_scores", type_="primary")
    op.drop_constraint(
        "uq_collection_scores_collection_content",
        "collection_scores",
        type_="unique",
    )
    op.create_primary_key(
        "collection_scores_pkey",
        "collection_scores",
        ["collection_id", "score_content_id"],
    )
    op.drop_column("collection_scores", "id")
