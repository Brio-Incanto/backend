from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, MetaData, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from piano_app.adapters.outbound.shared.codec import (
    SerializedScoreDocument,
)
from piano_app.application.ports.score import DraftMeta


class DraftBase(DeclarativeBase):
    pass


draft_metadata: MetaData = DraftBase.metadata


class DraftMetaORM(DraftBase):
    """System database metadata for drafts."""

    __tablename__ = "draft_meta"
    __table_args__ = (
        UniqueConstraint(
            "author_id",
            "score_id",
            name="uq_draft_author_score",
        ),
    )

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    title: Mapped[str] = mapped_column(String)
    author_id: Mapped[str] = mapped_column(String, index=True)
    score_id: Mapped[str | None] = mapped_column(String, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def to_meta(self) -> DraftMeta:
        return DraftMeta(
            draft_id=self.id,
            title=self.title,
            author_id=self.author_id,
            ref_score_id=self.score_id,
            updated_at=self.updated_at,
        )


class DraftContentORM(DraftBase):
    """Cold-tier draft state stored independently from the system database."""

    __tablename__ = "draft_contents"

    id: Mapped[str] = mapped_column(
        String,
        ForeignKey("draft_meta.id", ondelete="CASCADE"),
        primary_key=True,
    )
    revisions: Mapped[list[SerializedScoreDocument]] = mapped_column(JSONB)
    cursor: Mapped[int] = mapped_column(Integer)
    version: Mapped[int] = mapped_column(Integer)
