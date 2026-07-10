"""Cost guardrails: record spend and enforce per-video / per-channel / global caps."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.channel import Channel
from app.models.cost import CostLedgerEntry


class CostCapExceeded(Exception):
    """Raised when a planned spend would exceed a configured cap."""


def _effective_caps(db: Session) -> dict:
    """Cost caps with runtime AppSettings overrides taking precedence over env."""
    from app.models.settings import get_app_settings
    s = get_app_settings(db)
    return {
        "per_video": s.cost_cap_per_video_usd or settings.cost_cap_per_video_usd,
        "per_channel_daily": s.cost_cap_per_channel_daily_usd or settings.cost_cap_per_channel_daily_usd,
        "global_daily": s.cost_cap_global_daily_usd or settings.cost_cap_global_daily_usd,
    }


def _spend_since(db: Session, since: datetime, *, channel_id: int | None = None,
                 video_id: int | None = None) -> float:
    stmt = select(func.coalesce(func.sum(CostLedgerEntry.amount_usd), 0.0)).where(
        CostLedgerEntry.created_at >= since
    )
    if channel_id is not None:
        stmt = stmt.where(CostLedgerEntry.channel_id == channel_id)
    if video_id is not None:
        stmt = stmt.where(CostLedgerEntry.video_id == video_id)
    return float(db.execute(stmt).scalar_one())


def check_budget(db: Session, estimated_usd: float, *, channel_id: int | None = None,
                 video_id: int | None = None) -> None:
    """Raise CostCapExceeded if `estimated_usd` would breach any active cap."""
    now = datetime.now(timezone.utc)
    day_start = now - timedelta(days=1)
    caps = _effective_caps(db)

    # Per-video cap
    cap = caps["per_video"]
    if cap and video_id is not None:
        spent = _spend_since(db, datetime.min.replace(tzinfo=timezone.utc), video_id=video_id)
        if spent + estimated_usd > cap:
            raise CostCapExceeded(f"Per-video cap ${cap} would be exceeded (spent ${spent:.2f}).")

    # Per-channel daily cap (channel override wins if set)
    if channel_id is not None:
        channel = db.get(Channel, channel_id)
        cap = (channel.daily_cost_cap_usd if channel and channel.daily_cost_cap_usd
               else caps["per_channel_daily"])
        if cap:
            spent = _spend_since(db, day_start, channel_id=channel_id)
            if spent + estimated_usd > cap:
                raise CostCapExceeded(
                    f"Per-channel daily cap ${cap} would be exceeded (spent ${spent:.2f})."
                )

    # Global daily cap
    cap = caps["global_daily"]
    if cap:
        spent = _spend_since(db, day_start)
        if spent + estimated_usd > cap:
            raise CostCapExceeded(f"Global daily cap ${cap} would be exceeded (spent ${spent:.2f}).")


def record_spend(db: Session, provider: str, operation: str, amount_usd: float, *,
                 channel_id: int | None = None, video_id: int | None = None) -> None:
    """Persist an actual spend entry to the ledger."""
    db.add(CostLedgerEntry(
        provider=provider, operation=operation, amount_usd=amount_usd,
        channel_id=channel_id, video_id=video_id,
    ))
    db.commit()
