"""Preset library + bulk operations for scaling to many channels."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.database import get_db
from app.models.channel import Channel
from app.models.enums import JobStatus
from app.models.job import Job
from app.models.monetization import Monetization
from app.presets import PRESETS, get_preset

router = APIRouter(dependencies=[Depends(require_admin)])


class ApplyPreset(BaseModel):
    channel_ids: list[int]
    preset_id: str


class BulkRun(BaseModel):
    channel_ids: list[int]


class BulkAutonomy(BaseModel):
    channel_ids: list[int]
    autonomous: bool


@router.get("/presets")
def list_presets():
    return PRESETS


@router.post("/presets/apply")
def apply_preset(payload: ApplyPreset, db: Session = Depends(get_db)):
    preset = get_preset(payload.preset_id)
    if not preset:
        raise HTTPException(404, "Preset not found")

    applied = []
    for cid in payload.channel_ids:
        channel = db.get(Channel, cid)
        if not channel:
            continue
        channel.niche = preset["niche"]
        channel.uploads_per_day = preset["uploads_per_day"]
        channel.hero_video_provider = preset.get("hero_video_provider")

        mon = db.query(Monetization).filter(Monetization.channel_id == cid).one_or_none()
        if mon is None:
            mon = Monetization(channel_id=cid, affiliate_links=[])
            db.add(mon)
        if not mon.cta_text:
            mon.cta_text = preset.get("cta_text")
        applied.append(cid)
    db.commit()

    # Seed each channel's calendar with fresh topic ideas.
    from app.agents import STRATEGY_AGENT
    for cid in applied:
        channel = db.get(Channel, cid)
        try:
            STRATEGY_AGENT.plan(db, channel)
        except Exception:
            pass
    return {"applied": applied, "preset": payload.preset_id}


@router.post("/channels/run")
def bulk_run(payload: BulkRun, db: Session = Depends(get_db)):
    from app.workers.tasks import run_pipeline

    started = []
    for cid in payload.channel_ids:
        if not db.get(Channel, cid):
            continue
        job = Job(channel_id=cid, status=JobStatus.pending, trigger="bulk", state={})
        db.add(job)
        db.commit()
        db.refresh(job)
        run_pipeline.delay(job.id)
        started.append(job.id)
    return {"jobs": started}


@router.post("/channels/autonomy")
def bulk_autonomy(payload: BulkAutonomy, db: Session = Depends(get_db)):
    updated = 0
    for cid in payload.channel_ids:
        channel = db.get(Channel, cid)
        if channel:
            channel.autonomous = payload.autonomous
            updated += 1
    db.commit()
    return {"updated": updated, "autonomous": payload.autonomous}
