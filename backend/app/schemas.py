"""Pydantic request/response schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChannelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    youtube_channel_id: str
    title: str
    handle: str | None = None
    thumbnail_url: str | None = None
    niche: str | None = None
    autonomous: bool
    require_approval: bool
    uploads_per_day: int
    active: bool


class ChannelUpdate(BaseModel):
    niche: str | None = None
    autonomous: bool | None = None
    require_approval: bool | None = None
    uploads_per_day: int | None = None
    voice_id: str | None = None
    daily_cost_cap_usd: float | None = None


class VideoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    channel_id: int
    status: str
    topic: str | None = None
    title: str | None = None
    description: str | None = None
    tags: list | None = None
    youtube_video_id: str | None = None
    scheduled_at: datetime | None = None
    published_at: datetime | None = None


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    channel_id: int
    video_id: int | None = None
    status: str
    current_step: str | None = None
    error: str | None = None
    trigger: str


class JobCreate(BaseModel):
    channel_id: int
    topic: str | None = None  # optional; research agent picks one if omitted


class CalendarEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    channel_id: int
    scheduled_for: datetime
    topic: str
    notes: str | None = None
    source: str
    locked: bool
    done: bool


class CalendarEntryCreate(BaseModel):
    channel_id: int
    scheduled_for: datetime
    topic: str
    notes: str | None = None


class CalendarEntryUpdate(BaseModel):
    scheduled_for: datetime | None = None
    topic: str | None = None
    notes: str | None = None
    locked: bool | None = None


class AnalyticsSummary(BaseModel):
    channel_id: int
    total_views: int
    total_watch_time_minutes: float
    subscribers_gained: int
    avg_ctr: float
    videos_published: int
