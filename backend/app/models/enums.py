"""Enums shared across models."""
from __future__ import annotations

import enum


class JobStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    awaiting_approval = "awaiting_approval"
    approved = "approved"
    rejected = "rejected"
    completed = "completed"
    failed = "failed"


class VideoStatus(str, enum.Enum):
    draft = "draft"
    scripting = "scripting"
    rendering = "rendering"
    ready = "ready"
    scheduled = "scheduled"
    published = "published"
    failed = "failed"


class AgentStep(str, enum.Enum):
    research = "research"
    script = "script"
    voiceover = "voiceover"
    visuals = "visuals"
    captions = "captions"
    render = "render"
    seo = "seo"
    publish = "publish"
    analytics = "analytics"
    strategy = "strategy"
