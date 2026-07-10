"""System status/monitoring routes."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.database import get_db
from app.models.channel import Channel
from app.models.cost import CostLedgerEntry
from app.models.enums import JobStatus
from app.models.job import Job

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
