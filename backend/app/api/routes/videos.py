"""Video routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.database import get_db
from app.models.video import Video
from app.schemas import VideoOut

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("", response_model=list[VideoOut])
def list_videos(channel_id: int | None = None, db: Session = Depends(get_db)):
    stmt = select(Video).order_by(Video.created_at.desc())
    if channel_id is not None:
        stmt = stmt.where(Video.channel_id == channel_id)
    return db.execute(stmt).scalars().all()


@router.get("/{video_id}", response_model=VideoOut)
def get_video(video_id: int, db: Session = Depends(get_db)):
    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(404, "Video not found")
    return video
