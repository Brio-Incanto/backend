from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, false, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from piano_app.adapters.outbound.shared.codec import SerializedScoreDocument

from .base import Base


class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    username: Mapped[str] = mapped_column(
        String(64),
        unique=True,
    )
    bio: Mapped[str | None] = mapped_column(String)


class ScoreMetaORM(Base):
    __tablename__ = "scores"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    title: Mapped[str] = mapped_column(String)
    # None is set when a user is deleted or they delete the score,
    # but someone else still references it.
    author_id: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
    )
    composer: Mapped[str | None] = mapped_column(String)
    derived_from_id: Mapped[str | None] = mapped_column(
        "derived_from",
        String,
        ForeignKey("scores.id", ondelete="SET NULL"),
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        server_default=false(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class ScoreContentORM(Base):
    __tablename__ = "score_contents"
    __table_args__ = (
        UniqueConstraint(
            "score_id",
            "version",
            name="uq_score_contents_score_version",
        ),
    )

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    score_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("scores.id", ondelete="CASCADE"),
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer)
    document: Mapped[SerializedScoreDocument] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class CollectionScoreORM(Base):
    __tablename__ = "collection_scores"

    collection_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("collections.id", ondelete="CASCADE"),
        primary_key=True,
    )
    score_content_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("score_contents.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class CollectionORM(Base):
    __tablename__ = "collections"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    author_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String)
    scores: Mapped[list[ScoreContentORM]] = relationship(
        secondary=CollectionScoreORM.__table__,
        order_by=CollectionScoreORM.added_at,
        lazy="selectin",
        passive_deletes=True,
    )
