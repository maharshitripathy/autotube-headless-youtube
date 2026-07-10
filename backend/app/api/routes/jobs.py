"""Pipeline job routes: trigger runs and approval gate."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.database import get_db
from app.models.channel import Channel
from app.models.enums import JobStatus
from app.models.job import Job
from app.schemas import JobCreate, JobOut

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("", response_model=list[JobOut])
def list_jobs(channel_id: int | None = None, db: Session = Depends(get_db)):
    stmt = select(Job).order_by(Job.created_at.desc())
    if channel_id is not None:
        stmt = stmt.where(Job.channel_id == channel_id)
    return db.execute(stmt).scalars().all()


@router.post("", response_model=JobOut, status_code=201)
def create_job(payload: JobCreate, db: Session = Depends(get_db)):
    channel = db.get(Channel, payload.channel_id)
    if not channel:
        raise HTTPException(404, "Channel not found")

    job = Job(channel_id=channel.id, status=JobStatus.pending, trigger="manual",
              state={"topic": payload.topic} if payload.topic else {})
    db.add(job)
    db.commit()
    db.refresh(job)

    # Enqueue async pipeline run (implemented in workers).
    from app.workers.tasks import run_pipeline
    run_pipeline.delay(job.id)
    return job


@router.post("/{job_id}/approve", response_model=JobOut)
def approve_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status != JobStatus.awaiting_approval:
        raise HTTPException(409, "Job is not awaiting approval")
    job.status = JobStatus.approved
    db.commit()
    db.refresh(job)

    from app.workers.tasks import resume_pipeline
    resume_pipeline.delay(job.id)
    return job


@router.post("/{job_id}/reject", response_model=JobOut)
def reject_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    job.status = JobStatus.rejected
    db.commit()
    db.refresh(job)
    return job
