"""Agent 9 — Analytics: pull YouTube Analytics and store snapshots."""
from __future__ import annotations

from datetime import date

from app.agents.base import BaseAgent, PipelineContext
from app.integrations import youtube
from app.models.analytics import AnalyticsSnapshot
from app.models.channel import Channel
from app.models.enums import AgentStep


class AnalyticsAgent(BaseAgent):
    name = "analytics"
    step = AgentStep.analytics

    def run(self, ctx: PipelineContext) -> None:  # not part of production pipeline
        self.refresh(ctx.db, ctx.channel)

    def refresh(self, db, channel: Channel, days: int = 28) -> int:
        rows = youtube.fetch_analytics(channel, days=days)
        revenue_by_day = {
            r["day"]: r for r in youtube.fetch_revenue(channel, days=days)
        }
        count = 0
        for row in rows:
            day = date.fromisoformat(row["day"])
            existing = (
                db.query(AnalyticsSnapshot)
                .filter(
                    AnalyticsSnapshot.channel_id == channel.id,
                    AnalyticsSnapshot.day == day,
                    AnalyticsSnapshot.youtube_video_id.is_(None),
                )
                .one_or_none()
            )
            snap = existing or AnalyticsSnapshot(channel_id=channel.id, day=day)
            snap.views = int(row.get("views", 0))
            snap.watch_time_minutes = float(row.get("estimatedMinutesWatched", 0))
            snap.avg_view_duration_sec = float(row.get("averageViewDuration", 0))
            snap.subscribers_gained = int(row.get("subscribersGained", 0))
            snap.likes = int(row.get("likes", 0))
            snap.comments = int(row.get("comments", 0))

            rev = revenue_by_day.get(row["day"], {})
            snap.estimated_revenue = float(rev.get("estimatedRevenue", 0.0))
            snap.cpm = float(rev.get("cpm", 0.0))
            snap.rpm = float(rev.get("playbackBasedCpm", 0.0))

            if existing is None:
                db.add(snap)
            count += 1
        db.commit()
        return count
