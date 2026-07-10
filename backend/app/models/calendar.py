"""Planned future uploads (editable content calendar)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin


class CalendarEntry(Base, TimestampMixin):
    __tablename__ = "calendar_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), index=True)

    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    topic: Mapped[str] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)  # user-provided extra info

    # Source: 'strategy_agent' (auto-planned) or 'user' (manual override)
    source: Mapped[str] = mapped_column(String(32), default="strategy_agent")
    locked: Mapped[bool] = mapped_column(Boolean, default=False)  # user-locked, agent won't change
    done: Mapped[bool] = mapped_column(Boolean, default=False)
