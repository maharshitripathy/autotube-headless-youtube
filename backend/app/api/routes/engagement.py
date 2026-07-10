"""Comment engagement routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.database import get_db
from app.models.channel import Channel
from app.models.engagement import CommentReply

router = APIRouter(dependencies=[Depends(require_admin)])


class ReplyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    channel_id: int
    author: str | None = None
    comment_text: str | None = None
    reply_text: str | None = None
    action: str


@router.get("/{channel_id}", response_model=list[ReplyOut])
def list_replies(channel_id: int, db: Session = Depends(get_db)):
    stmt = (
        select(CommentReply)
        .where(CommentReply.channel_id == channel_id)
        .order_by(CommentReply.created_at.desc())
        .limit(50)
    )
    return db.execute(stmt).scalars().all()


@router.post("/{channel_id}/run")
def run_engagement(channel_id: int, db: Session = Depends(get_db)):
    channel = db.get(Channel, channel_id)
    if not channel:
        raise HTTPException(404, "Channel not found")
    from app.services.engagement import engage_channel
    return engage_channel(db, channel)
