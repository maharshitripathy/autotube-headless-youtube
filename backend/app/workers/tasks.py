"""Celery tasks: pipeline execution, analytics refresh, scheduling.

Heavy imports (orchestrator, integrations) are performed lazily inside the
task bodies so the module stays importable even while later phases are WIP.
"""
from __future__ import annotations

from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.run_pipeline", bind=True, max_retries=2)
def run_pipeline(self, job_id: int) -> dict:
    """Run the full content pipeline for a job (P2+)."""
    from app.orchestrator.runner import run_job
    return run_job(job_id)


@celery_app.task(name="app.workers.tasks.resume_pipeline")
def resume_pipeline(job_id: int) -> dict:
    """Resume a job that was paused at the approval gate (P3)."""
    from app.orchestrator.runner import resume_job
    return resume_job(job_id)


@celery_app.task(name="app.workers.tasks.pull_analytics")
def pull_analytics(channel_id: int) -> dict:
    """Fetch and store analytics snapshots for a channel (P4)."""
    from app.orchestrator.runner import refresh_channel_analytics
    return refresh_channel_analytics(channel_id)


@celery_app.task(name="app.workers.tasks.scheduler_tick")
def scheduler_tick() -> dict:
    """Enqueue pipeline runs for channels whose calendar entries are due (P5)."""
    from app.orchestrator.runner import tick_scheduler
    return tick_scheduler()
