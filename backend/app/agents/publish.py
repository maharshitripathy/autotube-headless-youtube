"""Agent 8 — Publisher: upload to YouTube (respects approval + schedule)."""
from __future__ import annotations

from datetime import datetime, timezone

from app.agents.base import BaseAgent, PipelineContext
from app.integrations import youtube
from app.models.enums import AgentStep, VideoStatus
from app.services import storage


class PublishAgent(BaseAgent):
    name = "publish"
    step = AgentStep.publish

    def run(self, ctx: PipelineContext) -> None:
        if not ctx.video.video_key:
            raise RuntimeError("No rendered video to publish.")

        # Download rendered mp4 to a temp file for the resumable upload.
        import tempfile
        mp4 = storage.download_bytes(ctx.video.video_key)
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(mp4)
            path = f.name

        publish_at = None
        if ctx.video.scheduled_at and ctx.video.scheduled_at > datetime.now(timezone.utc):
            publish_at = ctx.video.scheduled_at.isoformat()

        video_id = youtube.upload_short(
            ctx.channel, path,
            title=ctx.video.title or ctx.video.topic or "Short",
            description=ctx.video.description or "",
            tags=ctx.video.tags or [],
            publish_at=publish_at,
        )

        ctx.video.youtube_video_id = video_id
        ctx.video.status = VideoStatus.scheduled if publish_at else VideoStatus.published
        if not publish_at:
            ctx.video.published_at = datetime.now(timezone.utc)

        # Post the pinned CTA comment (best-effort; needs force-ssl scope).
        if ctx.video.pinned_comment and not publish_at:
            try:
                youtube.post_top_comment(ctx.channel, video_id, ctx.video.pinned_comment)
            except Exception as exc:
                ctx.log(f"pinned comment failed: {exc}")

        # Mark the calendar entry done if this run came from one.
        if entry_id := ctx.data.get("calendar_entry_id"):
            from app.models.calendar import CalendarEntry
            entry = ctx.db.get(CalendarEntry, entry_id)
            if entry:
                entry.done = True

        ctx.db.commit()
        ctx.log(f"published youtube video {video_id}")

        # Repurpose to other platforms (best-effort).
        if not publish_at and (ctx.channel.distribute_platforms or []):
            try:
                from app.services.distribution import distribute_video
                dists = distribute_video(ctx.db, ctx.video)
                ctx.log(f"prepared {len(dists)} cross-platform distributions")
            except Exception as exc:
                ctx.log(f"distribution failed: {exc}")
