"""Agent 7 — SEO/Metadata: title, description, tags."""
from __future__ import annotations

from app.agents.base import BaseAgent, PipelineContext
from app.integrations import openai_client
from app.models.enums import AgentStep
from app.services import cost_guard


class SeoAgent(BaseAgent):
    name = "seo"
    step = AgentStep.seo

    def run(self, ctx: PipelineContext) -> None:
        cost_guard.check_budget(ctx.db, openai_client.EST_SCRIPT_USD,
                                channel_id=ctx.channel.id, video_id=ctx.video.id)
        meta = openai_client.generate_metadata(ctx.video.topic or "", ctx.video.script or "")
        ctx.video.title = meta.get("title")
        ctx.video.description = meta.get("description")
        ctx.video.tags = meta.get("tags", [])
        ctx.db.commit()
        cost_guard.record_spend(ctx.db, "openai", "seo", openai_client.EST_SCRIPT_USD,
                                channel_id=ctx.channel.id, video_id=ctx.video.id)
        ctx.log(f"seo title: {ctx.video.title}")
