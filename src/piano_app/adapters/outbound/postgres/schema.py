from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    UniqueConstraint,
    false,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from piano_app.adapters.outbound.shared.codec import ScoreDocumentCodec, SerializedScoreDocument
from piano_app.adapters.outbound.shared.draft_snapshot import DraftSnapshot
from piano_app.domain.score import Score


class Base(DeclarativeBase):
    pass


class ScoreORM(Base):
    __tablename__ = "scores"

    # server-generated, never caller-supplied — every id in this schema is
    # auto-generated, no code path sets one explicitly (see DraftORM.id).
    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    title: Mapped[str] = mapped_column(String)
    author_id: Mapped[str] = mapped_column(
        "author",
        String,
    )
    composer: Mapped[str | None] = mapped_column(String)
    derived_from_id: Mapped[str | None] = mapped_column(
        "derived_from",
        String,
        ForeignKey("scores.id"),
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        server_default=false(),
    )
    document: Mapped[SerializedScoreDocument] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def to_domain(self, *, codec: ScoreDocumentCodec) -> Score:
        return Score(
            id=self.id,
            title=self.title,
            author_id=self.author_id,
            composer=self.composer,
            derived_from_id=self.derived_from_id,
            document=codec.deserialize(self.document),
            is_public=self.is_public,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class DraftORM(Base):
    """Cold-tier draft — mirrors the hot (Redis) shape exactly: a list of
    revisions (each the codec's serialized dict) plus a cursor into it, not
    just the current document. (SETTLED: matches the hot tier one-to-one, not
    the earlier current-document-only simplification.)"""

    __tablename__ = "drafts"
    __table_args__ = (
        UniqueConstraint(
            "author",
            "score",
            name="uq_drafts_author_score",
        ),
    )

    # plain String, not a UUID-typed column: a malformed lookup value (bad HTTP
    # input, a stray caller) then just matches no row instead of asyncpg refusing
    # to even encode the bind param — verified empirically. Costs nothing: this id
    # is never caller-supplied either, so there's no write-time garbage to reject.
    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    author_id: Mapped[str] = mapped_column(
        "author",
        String,
    )
    score_id: Mapped[str | None] = mapped_column(
        "score",
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


metadata: MetaData = Base.metadata
