"""Channel management routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.database import get_db
from app.models.channel import Channel
from app.schemas import ChannelOut, ChannelUpdate

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("", response_model=list[ChannelOut])
def list_channels(db: Session = Depends(get_db)):
    return db.execute(select(Channel).where(Channel.active)).scalars().all()


@router.get("/{channel_id}", response_model=ChannelOut)
def get_channel(channel_id: int, db: Session = Depends(get_db)):
    channel = db.get(Channel, channel_id)
    if not channel:
        raise HTTPException(404, "Channel not found")
    return channel


@router.patch("/{channel_id}", response_model=ChannelOut)
def update_channel(channel_id: int, payload: ChannelUpdate, db: Session = Depends(get_db)):
    channel = db.get(Channel, channel_id)
    if not channel:
        raise HTTPException(404, "Channel not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(channel, field, value)
    db.commit()
    db.refresh(channel)
    return channel
