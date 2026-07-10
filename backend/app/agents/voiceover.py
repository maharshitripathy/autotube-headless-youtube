"""Agent 3 — Voiceover: narrate the script with ElevenLabs."""
from __future__ import annotations

from app.agents.base import BaseAgent, PipelineContext
from app.integrations import elevenlabs_client
from app.models.enums import AgentStep, VideoStatus
from app.services import cost_guard, storage


class VoiceoverAgent(BaseAgent):
    name = "voiceover"
    step = AgentStep.voiceover

    def run(self, ctx: PipelineContext) -> None:
        script = ctx.video.script or ""
        est = elevenlabs_client.estimate_cost(script)
        cost_guard.check_budget(ctx.db, est, channel_id=ctx.channel.id, video_id=ctx.video.id)

        audio = elevenlabs_client.synthesize(script, voice_id=ctx.channel.voice_id)
        key = f"channels/{ctx.channel.id}/videos/{ctx.video.id}/voiceover.mp3"
        storage.upload_bytes(key, audio, content_type="audio/mpeg")

        ctx.video.audio_key = key
        ctx.video.status = VideoStatus.rendering
        ctx.data["audio_bytes"] = audio
        ctx.db.commit()

        cost_guard.record_spend(
            ctx.db, "elevenlabs", "tts", est,
            channel_id=ctx.channel.id, video_id=ctx.video.id,
        )
        ctx.log("voiceover synthesized")
