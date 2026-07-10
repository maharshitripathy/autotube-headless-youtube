"""Distribution record for cross-posting a video to another platform."""
from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin


class Distribution(Base, TimestampMixin):
    __tablename__ = "distributions"

    id: Mapped[int] = mapped_column(primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"), index=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), index=True)

    platform: Mapped[str] = mapped_column(String(32))  # tiktok | reels | youtube
    # ready_to_post (manual export), posted (via API), failed
    status: Mapped[str] = mapped_column(String(32), default="ready_to_post")
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    download_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
