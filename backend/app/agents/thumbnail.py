"""Agent — Thumbnail: generate an eye-catching thumbnail for the video."""
from __future__ import annotations

from app.agents.base import BaseAgent, PipelineContext
from app.integrations import openai_client
from app.models.enums import AgentStep
from app.services import cost_guard, storage


def _thumbnail_prompt(title: str, topic: str) -> str:
    return (
        "Ultra eye-catching YouTube thumbnail, bold dramatic lighting, high contrast, "
        "vivid saturated colors, cinematic, single clear focal subject, lots of negative "
        f"space for text, no words. Theme: {topic or title}."
    )


class ThumbnailAgent(BaseAgent):
    name = "thumbnail"
    step = AgentStep.seo  # part of the metadata phase

    def run(self, ctx: PipelineContext) -> None:
        self.generate(ctx.db, ctx.channel, ctx.video)
        ctx.log("thumbnail generated")

    def generate(self, db, channel, video) -> str:
        cost_guard.check_budget(db, openai_client.EST_IMAGE_USD,
                                channel_id=channel.id, video_id=video.id)
        prompt = _thumbnail_prompt(video.title or "", video.topic or "")
        img = openai_client.generate_image(prompt, size="1792x1024")
        key = f"channels/{channel.id}/videos/{video.id}/thumbnail.png"
        storage.upload_bytes(key, img, content_type="image/png")
        video.thumbnail_key = key
        db.commit()
        cost_guard.record_spend(db, "openai", "thumbnail", openai_client.EST_IMAGE_USD,
                                channel_id=channel.id, video_id=video.id)
        return key
