"""A/B title experiment: rotate title variants on a live video, keep the winner."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin


class TitleExperiment(Base, TimestampMixin):
    __tablename__ = "title_experiments"

    id: Mapped[int] = mapped_column(primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"), unique=True, index=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), index=True)

    # ["Title A", "Title B", "Title C"]
    variants: Mapped[list] = mapped_column(JSON, default=list)
    current_index: Mapped[int] = mapped_column(Integer, default=0)

    # [{"index": 0, "title": str, "views": int, "tested_at": iso}]
    results: Mapped[list | None] = mapped_column(JSON, default=list)

    settled: Mapped[bool] = mapped_column(Boolean, default=False)
    winner_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_view_count: Mapped[int] = mapped_column(Integer, default=0)
    last_rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
