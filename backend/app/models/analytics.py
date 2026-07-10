"""Analytics snapshots pulled from the YouTube Analytics API."""
from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin


class AnalyticsSnapshot(Base, TimestampMixin):
    __tablename__ = "analytics_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), index=True)

    # Either channel-level (video_id NULL) or per-video
    youtube_video_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    day: Mapped[date] = mapped_column(Date, index=True)

    views: Mapped[int] = mapped_column(Integer, default=0)
    watch_time_minutes: Mapped[float] = mapped_column(Float, default=0.0)
    avg_view_duration_sec: Mapped[float] = mapped_column(Float, default=0.0)
    subscribers_gained: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    ctr: Mapped[float] = mapped_column(Float, default=0.0)
