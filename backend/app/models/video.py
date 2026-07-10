"""A single Short produced by the pipeline."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import VideoStatus
from app.models.mixins import TimestampMixin


class Video(Base, TimestampMixin):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), index=True)

    status: Mapped[VideoStatus] = mapped_column(default=VideoStatus.draft)

    # Content artifacts (populated as agents run)
    topic: Mapped[str | None] = mapped_column(String(500), nullable=True)
    script: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Media object-storage keys
    audio_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    captions_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    visuals: Mapped[list | None] = mapped_column(JSON, nullable=True)
    video_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    thumbnail_key: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Publishing
    youtube_video_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    pinned_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
