"""Agent 6 — Assembly/Render: call the Remotion service to produce the MP4."""
from __future__ import annotations

import os

import httpx

from app.agents.base import BaseAgent, PipelineContext
from app.models.enums import AgentStep, VideoStatus
from app.services import storage

RENDER_SERVICE_URL = os.getenv("RENDER_SERVICE_URL", "http://render:3001")


class RenderAgent(BaseAgent):
    name = "render"
    step = AgentStep.render

    def run(self, ctx: PipelineContext) -> None:
        # Presign inputs so the Node renderer can fetch them.
        audio_url = storage.presigned_url(ctx.video.audio_key) if ctx.video.audio_key else None
        visuals = []
        for v in (ctx.video.visuals or []):
            if v.get("key"):
                visuals.append({**v, "url": storage.presigned_url(v["key"])})
            else:
                visuals.append(v)

        payload = {
            "video_id": ctx.video.id,
            "duration": ctx.data.get("duration", 30.0),
            "audio_url": audio_url,
            "captions": ctx.data.get("captions", []),
            "visuals": visuals,
            "hook": ctx.data.get("hook"),
            "music_url": ctx.channel.music_url,
            "music_volume": ctx.channel.music_volume,
        }

        with httpx.Client(timeout=600) as client:
            resp = client.post(f"{RENDER_SERVICE_URL}/render", json=payload)
            resp.raise_for_status()
            mp4 = resp.content

        key = f"channels/{ctx.channel.id}/videos/{ctx.video.id}/final.mp4"
        storage.upload_bytes(key, mp4, content_type="video/mp4")
        ctx.video.video_key = key
        ctx.video.status = VideoStatus.ready
        ctx.db.commit()
        ctx.log("rendered final.mp4")
