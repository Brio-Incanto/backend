from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from piano_app.adapters.outbound.shared.codec import ScoreDocumentCodec, SerializedScoreDocument
from piano_app.adapters.outbound.shared.draft_snapshot import DraftSnapshot

from .base import Base


class DraftORM(Base):
    """Cold-tier draft — mirrors the hot (Redis) shape exactly: a list of
    revisions (each the codec's serialized dict) plus a cursor into it, not
    just the current document. (SETTLED: matches the hot tier one-to-one, not
    the earlier current-document-only simplification.)"""

    __tablename__ = "drafts"
    __table_args__ = (
        UniqueConstraint(
            "score_id",
            "author_id",
            name="uq_drafts_author_score",
        ),
    )

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    author_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    score_id: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("scores.id", ondelete="SET NULL"),
    )
    revisions: Mapped[list[SerializedScoreDocument]] = mapped_column(JSONB)
    cursor: Mapped[int] = mapped_column(Integer)
    version: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def to_snapshot(self, *, codec: ScoreDocumentCodec) -> DraftSnapshot:
        return DraftSnapshot.create(
            draft_id=self.id,
            author_id=self.author_id,
            ref_score_id=self.score_id,
            revisions=[codec.deserialize(revision) for revision in self.revisions],
            cursor=self.cursor,
            version=self.version,
        )
