"""Singleton runtime-editable application settings (overrides env defaults)."""
from __future__ import annotations

from sqlalchemy import Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin


class AppSettings(Base, TimestampMixin):
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)

    # Cost-cap overrides (0/NULL = fall back to env defaults)
    cost_cap_per_video_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost_cap_per_channel_daily_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost_cap_global_daily_usd: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Paid promotion / ad planning
    monthly_ad_budget_usd: Mapped[float] = mapped_column(Float, default=0.0)
    ad_auto_promote: Mapped[bool] = mapped_column(Boolean, default=False)
    ad_target_roas: Mapped[float] = mapped_column(Float, default=2.0)  # target return on ad spend


def get_app_settings(db) -> "AppSettings":
    """Return the singleton settings row, creating it if needed."""
    row = db.get(AppSettings, 1)
    if row is None:
        row = AppSettings(id=1)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row
