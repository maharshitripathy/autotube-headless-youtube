"""Paid promotion campaign for a video (YouTube / Google Ads)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin


class AdCampaign(Base, TimestampMixin):
    __tablename__ = "ad_campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), index=True)
    video_id: Mapped[int | None] = mapped_column(ForeignKey("videos.id"), nullable=True, index=True)
    youtube_video_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    platform: Mapped[str] = mapped_column(String(32), default="youtube")
    objective: Mapped[str] = mapped_column(String(32), default="views")  # views | subscribers | traffic

    daily_budget_usd: Mapped[float] = mapped_column(Float, default=0.0)
    total_budget_usd: Mapped[float] = mapped_column(Float, default=0.0)
    spend_usd: Mapped[float] = mapped_column(Float, default=0.0)

    # planned | active | paused | completed
    status: Mapped[str] = mapped_column(String(16), default="planned")

    impressions: Mapped[int] = mapped_column(Integer, default=0)
    views: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)

    external_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
