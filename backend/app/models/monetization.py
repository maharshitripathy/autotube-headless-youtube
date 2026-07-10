"""Per-channel monetization configuration (affiliate, sponsor, CTA)."""
from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin


class Monetization(Base, TimestampMixin):
    __tablename__ = "monetization"

    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), unique=True, index=True)

    # Affiliate links: [{"keyword": "camera", "url": "https://amzn.to/..", "label": "My camera"}]
    affiliate_links: Mapped[list | None] = mapped_column(JSON, default=list)

    # Sponsorship ad-read (voiced into the video when active)
    sponsor_active: Mapped[bool] = mapped_column(Boolean, default=False)
    sponsor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sponsor_script: Mapped[str | None] = mapped_column(Text, nullable=True)
    sponsor_placement: Mapped[str] = mapped_column(String(16), default="outro")  # intro | outro

    # Description CTA + lead magnet (newsletter / digital product / merch)
    cta_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    lead_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Pinned comment template posted after upload
    pinned_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
