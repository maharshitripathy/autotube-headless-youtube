"""Celery application instance."""
from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "autotube",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_track_started=True,
    task_time_limit=60 * 30,
    worker_max_tasks_per_child=50,
    timezone="UTC",
)

# Periodic schedule (P5). The scheduler tick decides which channels are due.
celery_app.conf.beat_schedule = {
    "scheduler-tick": {
        "task": "app.workers.tasks.scheduler_tick",
        "schedule": 300.0,  # every 5 minutes
    },
    "daily-maintenance": {
        "task": "app.workers.tasks.daily_maintenance",
        "schedule": crontab(hour=3, minute=0),  # 03:00 UTC: refresh analytics + replan
    },
    "rotate-experiments": {
        "task": "app.workers.tasks.rotate_experiments",
        "schedule": crontab(minute=0, hour="*/6"),  # every 6h: A/B title rotation
    },
    "engage-comments": {
        "task": "app.workers.tasks.engage_comments",
        "schedule": crontab(minute=30, hour="*/4"),  # every 4h: comment engagement
    },
}
