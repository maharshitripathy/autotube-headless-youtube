"""Pipeline runner: orchestrates agents, the approval gate, and scheduling.

A run proceeds through PRODUCTION_PIPELINE. If the channel requires approval,
the job pauses at `awaiting_approval` after production and before publish;
`resume_job` continues to the Publisher once approved.
"""
from __future__ import annotations

import logging

from app.agents import ANALYTICS_AGENT, PRODUCTION_PIPELINE, PUBLISH_AGENT, STRATEGY_AGENT
from app.agents.base import PipelineContext
from app.database import SessionLocal
from app.models.channel import Channel
from app.models.enums import JobStatus, VideoStatus
from app.models.job import Job
from app.models.video import Video
from app.services.cost_guard import CostCapExceeded

logger = logging.getLogger("autotube.orchestrator")


def _build_context(db, job: Job) -> PipelineContext:
    channel = db.get(Channel, job.channel_id)
    if job.video_id:
        video = db.get(Video, job.video_id)
    else:
        video = Video(channel_id=channel.id, status=VideoStatus.draft)
        db.add(video)
        db.commit()
        db.refresh(video)
        job.video_id = video.id
        db.commit()
    return PipelineContext(db=db, job=job, channel=channel, video=video, data=job.state or {})


def _run_production(ctx: PipelineContext) -> None:
    for agent in PRODUCTION_PIPELINE:
        ctx.job.current_step = agent.step
        ctx.db.commit()
        agent.run(ctx)


def run_job(job_id: int) -> dict:
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if not job:
            return {"error": "job not found"}
        job.status = JobStatus.running
        db.commit()

        ctx = _build_context(db, job)
        try:
            _run_production(ctx)
        except CostCapExceeded as exc:
            job.status = JobStatus.failed
            job.error = f"cost cap: {exc}"
            db.commit()
            return {"status": "failed", "reason": str(exc)}

        # Approval gate.
        if ctx.channel.require_approval:
            job.status = JobStatus.awaiting_approval
            db.commit()
            return {"status": "awaiting_approval", "video_id": ctx.video.id}

        return _publish(db, job, ctx)
    except Exception as exc:  # noqa: BLE001 - surface any failure on the job
        logger.exception("pipeline failed")
        job = db.get(Job, job_id)
        if job:
            job.status = JobStatus.failed
            job.error = str(exc)
            db.commit()
        return {"status": "failed", "error": str(exc)}
    finally:
        db.close()


def resume_job(job_id: int) -> dict:
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if not job or job.status != JobStatus.approved:
            return {"error": "job not approved"}
        ctx = _build_context(db, job)
        return _publish(db, job, ctx)
    finally:
        db.close()


def _publish(db, job: Job, ctx: PipelineContext) -> dict:
    job.current_step = PUBLISH_AGENT.step
    db.commit()
    PUBLISH_AGENT.run(ctx)
    job.status = JobStatus.completed
    db.commit()
    return {"status": "completed", "youtube_video_id": ctx.video.youtube_video_id}


def refresh_channel_analytics(channel_id: int) -> dict:
    db = SessionLocal()
    try:
        channel = db.get(Channel, channel_id)
        if not channel:
            return {"error": "channel not found"}
        count = ANALYTICS_AGENT.refresh(db, channel)
        # Re-plan the calendar based on fresh analytics.
        added = STRATEGY_AGENT.plan(db, channel)
        return {"snapshots": count, "planned": added}
    finally:
        db.close()


def tick_scheduler() -> dict:
    """Enqueue runs for autonomous channels whose calendar entries are due."""
    from datetime import datetime, timezone

    from app.models.calendar import CalendarEntry
    from app.workers.tasks import run_pipeline

    db = SessionLocal()
    triggered = []
    try:
        now = datetime.now(timezone.utc)
        channels = db.query(Channel).filter(Channel.active, Channel.autonomous).all()
        for channel in channels:
            due = (
                db.query(CalendarEntry)
                .filter(
                    CalendarEntry.channel_id == channel.id,
                    CalendarEntry.done.is_(False),
                    CalendarEntry.scheduled_for <= now,
                )
                .first()
            )
            if not due:
                continue
            job = Job(channel_id=channel.id, trigger="scheduled",
                      state={"topic": due.topic, "calendar_entry_id": due.id})
            db.add(job)
            db.commit()
            db.refresh(job)
            run_pipeline.delay(job.id)
            triggered.append(job.id)
        return {"triggered": triggered}
    finally:
        db.close()
