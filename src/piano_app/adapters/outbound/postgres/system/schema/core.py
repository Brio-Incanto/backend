from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    false,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from piano_app.adapters.outbound.shared.codec import SerializedScoreDocument

from .base import Base


class UserModel(Base):
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


class ScoreMetaModel(Base):
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


class ScoreContentModel(Base):
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


# addition of several versions of a score to a collection should be
# prohibited at the repository level
class CollectionScoreModel(Base):
    __tablename__ = "collection_scores"

    __table_args__ = (
        UniqueConstraint(
            "collection_id",
            "score_content_id",
            name="uq_collection_scores_collection_content",
        ),
        # index for paging
        Index(
            "ix_collection_scores_collection_added",
            "collection_id",
            "added_at",
            "id",
        ),
    )

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )

    collection_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("collections.id", ondelete="CASCADE"),
    )
    score_content_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("score_contents.id", ondelete="CASCADE"),
        index=True,
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class CollectionModel(Base):
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
