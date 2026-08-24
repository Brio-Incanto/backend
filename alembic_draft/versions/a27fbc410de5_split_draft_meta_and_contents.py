"""split draft meta and contents

Revision ID: a27fbc410de5
Revises: d14f7a93c821
Create Date: 2026-08-20

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a27fbc410de5"
down_revision: str | Sequence[str] | None = "d14f7a93c821"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Replace the single `drafts` table with `draft_meta` (light, listed by
    author) and `draft_contents` (heavy, revisions history) — the same
    meta/content split already used for canon scores."""
    op.drop_index(op.f("ix_drafts_author_id"), table_name="drafts")
    op.drop_table("drafts")

    op.create_table(
        "draft_meta",
        sa.Column("id", sa.String(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("author_id", sa.String(), nullable=False),
        sa.Column("score_id", sa.String(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("author_id", "score_id", name="uq_draft_author_score"),
    )
    op.create_index(op.f("ix_draft_meta_author_id"), "draft_meta", ["author_id"], unique=False)
    op.create_index(op.f("ix_draft_meta_score_id"), "draft_meta", ["score_id"], unique=False)

    op.create_table(
        "draft_contents",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("revisions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("cursor", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["id"], ["draft_meta.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Recreate the single `drafts` table, dropping the meta/content split."""
    op.drop_table("draft_contents")
    op.drop_index(op.f("ix_draft_meta_score_id"), table_name="draft_meta")
    op.drop_index(op.f("ix_draft_meta_author_id"), table_name="draft_meta")
    op.drop_table("draft_meta")

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
