"""System status/monitoring routes."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.database import get_db
from app.models.analytics import AnalyticsSnapshot
from app.models.channel import Channel
from app.models.cost import CostLedgerEntry
from app.models.enums import JobStatus, VideoStatus
from app.models.job import Job
from app.models.video import Video

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/status")
def system_status(db: Session = Depends(get_db)):
    day_start = datetime.now(timezone.utc) - timedelta(days=1)
    channels = db.execute(select(func.count(Channel.id)).where(Channel.active)).scalar_one()
    autonomous = db.execute(
        select(func.count(Channel.id)).where(Channel.active, Channel.autonomous)
    ).scalar_one()
    awaiting = db.execute(
        select(func.count(Job.id)).where(Job.status == JobStatus.awaiting_approval)
    ).scalar_one()
    running = db.execute(
        select(func.count(Job.id)).where(Job.status == JobStatus.running)
    ).scalar_one()
    spend_today = db.execute(
        select(func.coalesce(func.sum(CostLedgerEntry.amount_usd), 0.0)).where(
            CostLedgerEntry.created_at >= day_start
        )
    ).scalar_one()

    return {
        "channels_active": channels,
        "channels_autonomous": autonomous,
        "jobs_awaiting_approval": awaiting,
        "jobs_running": running,
        "spend_last_24h_usd": round(float(spend_today), 4),
    }


@router.get("/overview")
def empire_overview(days: int = 28, db: Session = Depends(get_db)):
    """Aggregate KPIs, a profit-ranked channel leaderboard, and recent activity."""
    since_date = date.today() - timedelta(days=days)
    since_dt = datetime.now(timezone.utc) - timedelta(days=days)

    channels = db.execute(select(Channel).where(Channel.active)).scalars().all()

    leaderboard = []
    tot_views = tot_revenue = tot_spend = 0.0
    for ch in channels:
        views = float(db.execute(
            select(func.coalesce(func.sum(AnalyticsSnapshot.views), 0)).where(
                AnalyticsSnapshot.channel_id == ch.id, AnalyticsSnapshot.day >= since_date
            )
        ).scalar_one())
        revenue = float(db.execute(
            select(func.coalesce(func.sum(AnalyticsSnapshot.estimated_revenue), 0.0)).where(
                AnalyticsSnapshot.channel_id == ch.id, AnalyticsSnapshot.day >= since_date
            )
        ).scalar_one())
        spend = float(db.execute(
            select(func.coalesce(func.sum(CostLedgerEntry.amount_usd), 0.0)).where(
                CostLedgerEntry.channel_id == ch.id, CostLedgerEntry.created_at >= since_dt
            )
        ).scalar_one())
        published = int(db.execute(
            select(func.count(Video.id)).where(
                Video.channel_id == ch.id, Video.status == VideoStatus.published
            )
        ).scalar_one())

        tot_views += views
        tot_revenue += revenue
        tot_spend += spend
        leaderboard.append({
            "channel_id": ch.id,
            "title": ch.title,
            "thumbnail_url": ch.thumbnail_url,
            "views": int(views),
            "revenue_usd": round(revenue, 2),
            "profit_usd": round(revenue - spend, 2),
            "videos_published": published,
            "autonomous": ch.autonomous,
        })

    leaderboard.sort(key=lambda x: x["profit_usd"], reverse=True)

    recent_jobs = db.execute(
        select(Job).order_by(Job.created_at.desc()).limit(12)
    ).scalars().all()
    activity = [
        {
            "id": j.id,
            "channel_id": j.channel_id,
            "status": j.status.value if hasattr(j.status, "value") else j.status,
            "step": j.current_step.value if getattr(j.current_step, "value", None) else j.current_step,
            "trigger": j.trigger,
            "created_at": j.created_at.isoformat() if j.created_at else None,
        }
        for j in recent_jobs
    ]

    total_published = int(db.execute(
        select(func.count(Video.id)).where(Video.status == VideoStatus.published)
    ).scalar_one())

    return {
        "totals": {
            "channels": len(channels),
            "views": int(tot_views),
            "revenue_usd": round(tot_revenue, 2),
            "spend_usd": round(tot_spend, 2),
            "profit_usd": round(tot_revenue - tot_spend, 2),
            "videos_published": total_published,
        },
        "leaderboard": leaderboard,
        "activity": activity,
    }
