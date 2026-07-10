"""Orchestration job tracking a pipeline run for one video."""
from __future__ import annotations

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import AgentStep, JobStatus
from app.models.mixins import TimestampMixin


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), index=True)
    video_id: Mapped[int | None] = mapped_column(ForeignKey("videos.id"), nullable=True, index=True)

    status: Mapped[JobStatus] = mapped_column(default=JobStatus.pending)
    current_step: Mapped[AgentStep | None] = mapped_column(nullable=True)

    # LangGraph state snapshot + step outputs for observability
    state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    trigger: Mapped[str] = mapped_column(String(32), default="manual")  # manual | scheduled
