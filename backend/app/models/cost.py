"""Ledger of paid-API spend, used to enforce cost caps."""
from __future__ import annotations

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin


class CostLedgerEntry(Base, TimestampMixin):
    __tablename__ = "cost_ledger"

    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[int | None] = mapped_column(ForeignKey("channels.id"), nullable=True, index=True)
    video_id: Mapped[int | None] = mapped_column(ForeignKey("videos.id"), nullable=True, index=True)

    provider: Mapped[str] = mapped_column(String(64))   # openai | elevenlabs | vertex | pexels
    operation: Mapped[str] = mapped_column(String(64))  # e.g. script, tts, image, veo
    amount_usd: Mapped[float] = mapped_column(Float, default=0.0)
