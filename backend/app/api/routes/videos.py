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


@router.get("/{video_id}/media")
def get_video_media(video_id: int, db: Session = Depends(get_db)):
    """Presigned URLs for previewing the rendered Short and its assets."""
    from app.services import storage

    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(404, "Video not found")
    return {
        "video_url": storage.presigned_url(video.video_key) if video.video_key else None,
        "audio_url": storage.presigned_url(video.audio_key) if video.audio_key else None,
        "thumbnail_url": storage.presigned_url(video.thumbnail_key) if video.thumbnail_key else None,
    }


@router.get("/{video_id}/detail")
def get_video_detail(video_id: int, db: Session = Depends(get_db)):
    """Combined video + media URLs + distributions for the Library drawer."""
    from app.services import storage
    from app.models.distribution import Distribution

    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(404, "Video not found")

    dists = db.execute(
        select(Distribution).where(Distribution.video_id == video_id)
    ).scalars().all()

    return {
        "video": VideoOut.model_validate(video).model_dump(),
        "media": {
            "video_url": storage.presigned_url(video.video_key) if video.video_key else None,
            "thumbnail_url": storage.presigned_url(video.thumbnail_key) if video.thumbnail_key else None,
        },
        "distributions": [
            {"platform": d.platform, "status": d.status, "caption": d.caption,
             "download_url": d.download_url, "external_id": d.external_id}
            for d in dists
        ],
    }
