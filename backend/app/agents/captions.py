"""Agent 5 — Captions: word-level timing via local Whisper."""
from __future__ import annotations

import json

from app.agents.base import BaseAgent, PipelineContext
from app.integrations import whisper_local
from app.models.enums import AgentStep
from app.services import storage


class CaptionsAgent(BaseAgent):
    name = "captions"
    step = AgentStep.captions

    def run(self, ctx: PipelineContext) -> None:
        audio = ctx.data.get("audio_bytes")
        if audio is None and ctx.video.audio_key:
            audio = storage.download_bytes(ctx.video.audio_key)
        if not audio:
            raise RuntimeError("No audio available for captioning.")

        words = whisper_local.transcribe_words(audio)
        key = f"channels/{ctx.channel.id}/videos/{ctx.video.id}/captions.json"
        storage.upload_bytes(key, json.dumps(words).encode(), content_type="application/json")

        ctx.video.captions_key = key
        ctx.data["captions"] = words
        # Duration drives the render timeline.
        ctx.data["duration"] = words[-1]["end"] if words else 0.0
        ctx.db.commit()
        ctx.log(f"captioned {len(words)} words ({ctx.data['duration']}s)")
