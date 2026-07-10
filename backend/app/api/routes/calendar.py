"""Content calendar routes (editable future upload plan)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.database import get_db
from app.models.calendar import CalendarEntry
from app.schemas import CalendarEntryCreate, CalendarEntryOut, CalendarEntryUpdate

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("", response_model=list[CalendarEntryOut])
def list_entries(channel_id: int, db: Session = Depends(get_db)):
    stmt = (
        select(CalendarEntry)
        .where(CalendarEntry.channel_id == channel_id, CalendarEntry.done.is_(False))
        .order_by(CalendarEntry.scheduled_for)
    )
    return db.execute(stmt).scalars().all()


@router.post("", response_model=CalendarEntryOut, status_code=201)
def create_entry(payload: CalendarEntryCreate, db: Session = Depends(get_db)):
    entry = CalendarEntry(
        channel_id=payload.channel_id,
        scheduled_for=payload.scheduled_for,
        topic=payload.topic,
        notes=payload.notes,
        source="user",
        locked=True,  # user-created entries are locked so the strategy agent won't overwrite
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.patch("/{entry_id}", response_model=CalendarEntryOut)
def update_entry(entry_id: int, payload: CalendarEntryUpdate, db: Session = Depends(get_db)):
    entry = db.get(CalendarEntry, entry_id)
    if not entry:
        raise HTTPException(404, "Calendar entry not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=204)
def delete_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.get(CalendarEntry, entry_id)
    if entry:
        db.delete(entry)
        db.commit()
