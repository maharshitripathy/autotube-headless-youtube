"""A/B title experiment routes: inspect variants, promote a winner manually."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.database import get_db
from app.models.experiment import TitleExperiment
from app.models.video import Video

router = APIRouter(dependencies=[Depends(require_admin)])


class ExperimentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    video_id: int
    channel_id: int
    variants: list
    current_index: int
    results: list | None = None
    settled: bool
    winner_index: int | None = None


@router.get("", response_model=list[ExperimentOut])
def list_experiments(channel_id: int | None = None, db: Session = Depends(get_db)):
    stmt = select(TitleExperiment).order_by(TitleExperiment.created_at.desc())
    if channel_id is not None:
        stmt = stmt.where(TitleExperiment.channel_id == channel_id)
    return db.execute(stmt).scalars().all()


@router.post("/{experiment_id}/promote/{index}", response_model=ExperimentOut)
def promote(experiment_id: int, index: int, db: Session = Depends(get_db)):
    exp = db.get(TitleExperiment, experiment_id)
    if not exp:
        raise HTTPException(404, "Experiment not found")
    if index < 0 or index >= len(exp.variants):
        raise HTTPException(400, "Invalid variant index")

    video = db.get(Video, exp.video_id)
    exp.winner_index = index
    exp.settled = True
    if video and video.youtube_video_id:
        from app.integrations import youtube
        from app.models.channel import Channel
        channel = db.get(Channel, exp.channel_id)
        try:
            youtube.update_video_metadata(channel, video.youtube_video_id, title=exp.variants[index])
            video.title = exp.variants[index]
        except Exception:
            pass
    db.commit()
    db.refresh(exp)
    return exp
