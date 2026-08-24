"""initial draft archive

Revision ID: d14f7a93c821
Revises:
Create Date: 2026-08-18

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d14f7a93c821"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the cold draft archive schema."""
    op.create_table(
        "drafts",
        sa.Column("id", sa.String(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("author_id", sa.String(), nullable=False),
        sa.Column("score_id", sa.String(), nullable=True),
        sa.Column("revisions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("cursor", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("score_id", "author_id", name="uq_drafts_author_score"),
    )
    op.create_index(op.f("ix_drafts_author_id"), "drafts", ["author_id"], unique=False)


def downgrade() -> None:
    """Drop the cold draft archive schema."""
    op.drop_index(op.f("ix_drafts_author_id"), table_name="drafts")
    op.drop_table("drafts")
