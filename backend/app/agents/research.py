"""Agent 1 — Trend/Research: choose a topic for the next Short."""
from __future__ import annotations

from app.agents.base import BaseAgent, PipelineContext
from app.integrations import openai_client
from app.models.enums import AgentStep, VideoStatus
from app.models.video import Video


class ResearchAgent(BaseAgent):
    name = "research"
    step = AgentStep.research

    def run(self, ctx: PipelineContext) -> None:
        # 1) Explicit topic on the job wins.
        topic = (ctx.job.state or {}).get("topic")

        # 2) Otherwise take the next due calendar entry.
        if not topic:
            from app.models.calendar import CalendarEntry
            entry = (
                ctx.db.query(CalendarEntry)
                .filter(CalendarEntry.channel_id == ctx.channel.id, CalendarEntry.done.is_(False))
                .order_by(CalendarEntry.scheduled_for)
                .first()
            )
            if entry:
                topic = entry.topic
                ctx.data["calendar_entry_id"] = entry.id
                if entry.notes:
                    ctx.data["extra_notes"] = entry.notes

        # 3) Otherwise ask the model to suggest one from the niche.
        if not topic:
            recent = [
                v.title for v in ctx.db.query(Video)
                .filter(Video.channel_id == ctx.channel.id, Video.title.isnot(None))
                .order_by(Video.created_at.desc()).limit(10).all()
            ]
            suggestions = openai_client.suggest_topics(ctx.channel.niche or "general", recent, count=5)
            topic = suggestions[0] if suggestions else "An interesting fact you didn't know"

        ctx.video.topic = topic
        ctx.video.status = VideoStatus.scripting
        ctx.db.commit()
        ctx.log(f"research selected topic: {topic}")
