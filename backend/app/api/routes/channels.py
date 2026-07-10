"""Channel management routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.database import get_db
from app.models.channel import Channel
from app.models.monetization import Monetization
from app.schemas import ChannelOut, ChannelUpdate, MonetizationOut, MonetizationUpdate

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("", response_model=list[ChannelOut])
def list_channels(db: Session = Depends(get_db)):
    return db.execute(select(Channel).where(Channel.active)).scalars().all()


@router.get("/voices")
def list_voices():
    """Available ElevenLabs voices for narration selection."""
    from app.integrations import elevenlabs_client
    try:
        return elevenlabs_client.list_voices()
    except Exception:
        return []


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


def _get_or_create_monetization(db: Session, channel_id: int) -> Monetization:
    mon = db.query(Monetization).filter(Monetization.channel_id == channel_id).one_or_none()
    if mon is None:
        mon = Monetization(channel_id=channel_id, affiliate_links=[])
        db.add(mon)
        db.commit()
        db.refresh(mon)
    return mon


@router.get("/{channel_id}/monetization", response_model=MonetizationOut)
def get_monetization(channel_id: int, db: Session = Depends(get_db)):
    if not db.get(Channel, channel_id):
        raise HTTPException(404, "Channel not found")
    return _get_or_create_monetization(db, channel_id)


@router.put("/{channel_id}/monetization", response_model=MonetizationOut)
def update_monetization(channel_id: int, payload: MonetizationUpdate, db: Session = Depends(get_db)):
    if not db.get(Channel, channel_id):
        raise HTTPException(404, "Channel not found")
    mon = _get_or_create_monetization(db, channel_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(mon, field, value)
    db.commit()
    db.refresh(mon)
    return mon
