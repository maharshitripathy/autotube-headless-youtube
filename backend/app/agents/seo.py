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

        # Set up an A/B title experiment (variants rotate on the live video).
        try:
            variants = openai_client.generate_title_variants(
                ctx.video.topic or "", ctx.video.script or "", n=3
            )
            if ctx.video.title and ctx.video.title not in variants:
                variants = [ctx.video.title, *variants][:3]
            if len(variants) > 1:
                from app.models.experiment import TitleExperiment
                exp = (
                    ctx.db.query(TitleExperiment)
                    .filter(TitleExperiment.video_id == ctx.video.id)
                    .one_or_none()
                )
                if exp is None:
                    exp = TitleExperiment(video_id=ctx.video.id, channel_id=ctx.channel.id)
                    ctx.db.add(exp)
                exp.variants = variants
                exp.current_index = 0
                exp.results = []
                exp.settled = False
                ctx.video.title = variants[0]
                ctx.db.commit()
                ctx.log(f"created A/B experiment with {len(variants)} title variants")
        except Exception as exc:
            ctx.log(f"title experiment setup skipped: {exc}")

        ctx.log(f"seo title: {ctx.video.title}")
