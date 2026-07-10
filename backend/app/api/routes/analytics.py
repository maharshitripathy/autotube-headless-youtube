"""Analytics routes: expose stored snapshots and trigger refresh."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.database import get_db
from app.models.analytics import AnalyticsSnapshot
from app.models.channel import Channel
from app.models.cost import CostLedgerEntry
from app.models.video import Video
from app.models.enums import VideoStatus
from app.schemas import AnalyticsSummary

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/{channel_id}/summary", response_model=AnalyticsSummary)
def channel_summary(channel_id: int, days: int = 28, db: Session = Depends(get_db)):
    channel = db.get(Channel, channel_id)
    if not channel:
        raise HTTPException(404, "Channel not found")

    since = date.today() - timedelta(days=days)
    rows = db.execute(
        select(
            func.coalesce(func.sum(AnalyticsSnapshot.views), 0),
            func.coalesce(func.sum(AnalyticsSnapshot.watch_time_minutes), 0.0),
            func.coalesce(func.sum(AnalyticsSnapshot.subscribers_gained), 0),
            func.coalesce(func.avg(AnalyticsSnapshot.ctr), 0.0),
        ).where(
            AnalyticsSnapshot.channel_id == channel_id,
            AnalyticsSnapshot.day >= since,
        )
    ).one()

    published = db.execute(
        select(func.count(Video.id)).where(
            Video.channel_id == channel_id, Video.status == VideoStatus.published
        )
    ).scalar_one()

    return AnalyticsSummary(
        channel_id=channel_id,
        total_views=int(rows[0]),
        total_watch_time_minutes=float(rows[1]),
        subscribers_gained=int(rows[2]),
        avg_ctr=float(rows[3]),
        videos_published=int(published),
    )


@router.post("/{channel_id}/refresh", status_code=202)
def refresh_analytics(channel_id: int, db: Session = Depends(get_db)):
    channel = db.get(Channel, channel_id)
    if not channel:
        raise HTTPException(404, "Channel not found")
    from app.workers.tasks import pull_analytics
    pull_analytics.delay(channel_id)
    return {"status": "queued"}


@router.get("/{channel_id}/revenue")
def revenue_summary(channel_id: int, days: int = 28, db: Session = Depends(get_db)):
    """Revenue, production spend (from the cost ledger), and net profit."""
    channel = db.get(Channel, channel_id)
    if not channel:
        raise HTTPException(404, "Channel not found")

    since_date = date.today() - timedelta(days=days)
    since_dt = datetime.now(timezone.utc) - timedelta(days=days)

    revenue = float(db.execute(
        select(func.coalesce(func.sum(AnalyticsSnapshot.estimated_revenue), 0.0)).where(
            AnalyticsSnapshot.channel_id == channel_id,
            AnalyticsSnapshot.day >= since_date,
        )
    ).scalar_one())
    avg_rpm = float(db.execute(
        select(func.coalesce(func.avg(AnalyticsSnapshot.rpm), 0.0)).where(
            AnalyticsSnapshot.channel_id == channel_id,
            AnalyticsSnapshot.day >= since_date,
            AnalyticsSnapshot.rpm > 0,
        )
    ).scalar_one())
    spend = float(db.execute(
        select(func.coalesce(func.sum(CostLedgerEntry.amount_usd), 0.0)).where(
            CostLedgerEntry.channel_id == channel_id,
            CostLedgerEntry.created_at >= since_dt,
        )
    ).scalar_one())

    return {
        "channel_id": channel_id,
        "estimated_revenue_usd": round(revenue, 2),
        "production_spend_usd": round(spend, 2),
        "net_profit_usd": round(revenue - spend, 2),
        "avg_rpm_usd": round(avg_rpm, 2),
        "roi_pct": round(((revenue - spend) / spend * 100) if spend else 0.0, 1),
    }


@router.get("/{channel_id}/daily")
def daily_series(channel_id: int, days: int = 28, db: Session = Depends(get_db)):
    """Daily views/watch-time series for charting."""
    since = date.today() - timedelta(days=days)
    rows = db.execute(
        select(AnalyticsSnapshot)
        .where(
            AnalyticsSnapshot.channel_id == channel_id,
            AnalyticsSnapshot.day >= since,
            AnalyticsSnapshot.youtube_video_id.is_(None),
        )
        .order_by(AnalyticsSnapshot.day)
    ).scalars().all()
    return [
        {
            "day": r.day.isoformat(),
            "views": r.views,
            "watch_time_minutes": r.watch_time_minutes,
            "subscribers_gained": r.subscribers_gained,
        }
        for r in rows
    ]
