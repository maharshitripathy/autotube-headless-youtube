"""Agent 10 — Strategy/Planner: adapt the content calendar from analytics."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.agents.base import BaseAgent, PipelineContext
from app.integrations import openai_client
from app.models.analytics import AnalyticsSnapshot
from app.models.calendar import CalendarEntry
from app.models.channel import Channel
from app.models.enums import AgentStep
from app.models.video import Video


class StrategyAgent(BaseAgent):
    name = "strategy"
    step = AgentStep.strategy

    def run(self, ctx: PipelineContext) -> None:
        self.plan(ctx.db, ctx.channel)

    def plan(self, db, channel: Channel, horizon_days: int = 7) -> int:
        """Fill the calendar up to `horizon_days` ahead, respecting locked entries."""
        now = datetime.now(timezone.utc)
        horizon_end = now + timedelta(days=horizon_days)

        # How many slots already planned (locked or not).
        planned = (
            db.query(CalendarEntry)
            .filter(
                CalendarEntry.channel_id == channel.id,
                CalendarEntry.done.is_(False),
                CalendarEntry.scheduled_for <= horizon_end,
            )
            .order_by(CalendarEntry.scheduled_for)
            .all()
        )
        target_slots = max(1, channel.uploads_per_day) * horizon_days
        needed = target_slots - len(planned)
        if needed <= 0:
            return 0

        recent = [
            v.title for v in db.query(Video)
            .filter(Video.channel_id == channel.id, Video.title.isnot(None))
            .order_by(Video.created_at.desc()).limit(15).all()
        ]
        # Bias suggestions with best-performing recent context.
        top = (
            db.query(AnalyticsSnapshot)
            .filter(AnalyticsSnapshot.channel_id == channel.id)
            .order_by(AnalyticsSnapshot.views.desc())
            .first()
        )
        niche = channel.niche or "general"
        if top:
            niche = f"{niche} (recent best day had {top.views} views)"

        topics = openai_client.suggest_topics(niche, recent, count=needed)

        # Next available slot after the last planned entry.
        interval = timedelta(hours=max(1, 24 // max(1, channel.uploads_per_day)))
        cursor = planned[-1].scheduled_for + interval if planned else now + interval

        added = 0
        for topic in topics:
            db.add(CalendarEntry(
                channel_id=channel.id,
                scheduled_for=cursor,
                topic=topic,
                source="strategy_agent",
                locked=False,
            ))
            cursor += interval
            added += 1
        db.commit()
        return added
