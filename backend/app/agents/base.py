"""Pipeline context and base agent contract shared by all agents."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models.channel import Channel
from app.models.job import Job
from app.models.video import Video

logger = logging.getLogger("autotube.agents")


@dataclass
class PipelineContext:
    """Mutable state passed between agents during a pipeline run."""

    db: Session
    job: Job
    channel: Channel
    video: Video
    data: dict = field(default_factory=dict)  # scratch space for inter-agent hand-off

    def log(self, message: str) -> None:
        logger.info("[job %s] %s", self.job.id, message)


class BaseAgent:
    """Base class for a specialized agent. Subclasses implement `run`."""

    name: str = "base"
    step = None  # app.models.enums.AgentStep

    def run(self, ctx: PipelineContext) -> None:  # pragma: no cover - interface
        raise NotImplementedError
