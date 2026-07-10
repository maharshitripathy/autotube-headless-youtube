"""Distribution routes: view and trigger cross-platform repurposing."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.database import get_db
from app.models.distribution import Distribution
from app.models.video import Video
from app.services.distribution import distribute_video

router = APIRouter(dependencies=[Depends(require_admin)])


class DistributionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    video_id: int
    channel_id: int
    platform: str
    status: str
    caption: str | None = None
    download_url: str | None = None
    external_id: str | None = None
    error: str | None = None


@router.get("", response_model=list[DistributionOut])
def list_distributions(channel_id: int | None = None, video_id: int | None = None,
                       db: Session = Depends(get_db)):
    stmt = select(Distribution).order_by(Distribution.created_at.desc())
    if channel_id is not None:
        stmt = stmt.where(Distribution.channel_id == channel_id)
    if video_id is not None:
        stmt = stmt.where(Distribution.video_id == video_id)
    return db.execute(stmt).scalars().all()


@router.post("/video/{video_id}", response_model=list[DistributionOut])
def distribute(video_id: int, db: Session = Depends(get_db)):
    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(404, "Video not found")
    return distribute_video(db, video)
