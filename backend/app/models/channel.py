"""YouTube channel connected via OAuth."""
from __future__ import annotations

from sqlalchemy import Boolean, Float, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin

class Channel(Base, TimestampMixin):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(primary_key=True)

    # YouTube identity
    youtube_channel_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    handle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # OAuth (encrypted at rest via app.security)
    encrypted_refresh_token: Mapped[str] = mapped_column(Text)
    scopes: Mapped[str] = mapped_column(Text, default="")

    # Automation settings
    niche: Mapped[str | None] = mapped_column(String(255), nullable=True)
    autonomous: Mapped[bool] = mapped_column(Boolean, default=False)
    require_approval: Mapped[bool] = mapped_column(Boolean, default=True)
    uploads_per_day: Mapped[int] = mapped_column(default=1)
    voice_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Per-channel cost cap override (0 = use global default)
    daily_cost_cap_usd: Mapped[float] = mapped_column(Float, default=0.0)

    # Cross-post targets, e.g. ["tiktok", "reels"]
    distribute_platforms: Mapped[list | None] = mapped_column(JSON, default=list)

    active: Mapped[bool] = mapped_column(Boolean, default=True)
