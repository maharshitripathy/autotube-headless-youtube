"""Agent 4 — Visual: pick/generate a vertical visual per beat.

Strategy per beat:
  1. Pexels stock video (cheap, reliable) — default backbone.
  2. DALL-E image (animated with Ken Burns in the renderer) — fallback.
  3. Veo 3 hero clip — only if enabled and the beat is flagged as a hero shot.
"""
from __future__ import annotations

from app.agents.base import BaseAgent, PipelineContext
from app.integrations import openai_client, pexels_client, vertex_veo
from app.models.enums import AgentStep
from app.services import cost_guard, storage


class VisualsAgent(BaseAgent):
    name = "visuals"
    step = AgentStep.visuals

    def run(self, ctx: PipelineContext) -> None:
        beats = ctx.data.get("beats") or [{"text": ctx.video.script, "visual_query": ctx.video.topic}]
        visuals: list[dict] = []

        for i, beat in enumerate(beats):
            query = beat.get("visual_query") or ctx.video.topic or "abstract background"
            visual = self._resolve_beat_visual(ctx, i, query, hero=beat.get("hero", False))
            visuals.append(visual)

        ctx.video.visuals = visuals
        ctx.db.commit()
        ctx.log(f"prepared {len(visuals)} visuals")

    def _resolve_beat_visual(self, ctx: PipelineContext, index: int, query: str, hero: bool) -> dict:
        # Hero shot via Veo (optional).
        if hero and vertex_veo.is_enabled():
            try:
                cost_guard.check_budget(ctx.db, vertex_veo.EST_VEO_USD_PER_CLIP,
                                        channel_id=ctx.channel.id, video_id=ctx.video.id)
                clip = vertex_veo.generate_clip(query)
                key = f"channels/{ctx.channel.id}/videos/{ctx.video.id}/veo_{index}.mp4"
                storage.upload_bytes(key, clip, content_type="video/mp4")
                cost_guard.record_spend(ctx.db, "vertex", "veo",
                                        vertex_veo.EST_VEO_USD_PER_CLIP,
                                        channel_id=ctx.channel.id, video_id=ctx.video.id)
                return {"type": "veo", "key": key, "query": query}
            except Exception as exc:  # fall back gracefully
                ctx.log(f"veo failed ({exc}); falling back to stock")

        # Stock video backbone.
        try:
            clips = pexels_client.search_videos(query, per_page=1)
            if clips:
                return {"type": "stock_video", "url": clips[0]["url"], "query": query}
        except Exception as exc:
            ctx.log(f"pexels failed ({exc}); falling back to AI image")

        # AI image fallback (animated in the renderer).
        cost_guard.check_budget(ctx.db, openai_client.EST_IMAGE_USD,
                                channel_id=ctx.channel.id, video_id=ctx.video.id)
        img = openai_client.generate_image(query)
        key = f"channels/{ctx.channel.id}/videos/{ctx.video.id}/img_{index}.png"
        storage.upload_bytes(key, img, content_type="image/png")
        cost_guard.record_spend(ctx.db, "openai", "image", openai_client.EST_IMAGE_USD,
                                channel_id=ctx.channel.id, video_id=ctx.video.id)
        return {"type": "image", "key": key, "query": query}
