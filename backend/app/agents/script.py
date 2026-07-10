"""Agent 2 — Scriptwriter: hook + narration + visual beats."""
from __future__ import annotations

from app.agents.base import BaseAgent, PipelineContext
from app.integrations import openai_client
from app.models.enums import AgentStep
from app.services import cost_guard


class ScriptAgent(BaseAgent):
    name = "script"
    step = AgentStep.script

    def run(self, ctx: PipelineContext) -> None:
        cost_guard.check_budget(
            ctx.db, openai_client.EST_SCRIPT_USD,
            channel_id=ctx.channel.id, video_id=ctx.video.id,
        )
        topic = ctx.video.topic or "An interesting fact"
        if notes := ctx.data.get("extra_notes"):
            topic = f"{topic}\nExtra guidance: {notes}"

        result = openai_client.generate_script(topic, ctx.channel.niche)
        ctx.video.script = result["script"]
        ctx.data["beats"] = result.get("beats", [])
        ctx.data["hook"] = result.get("hook")

        # Insert a sponsor ad-read into the narration if configured.
        from app.models.monetization import Monetization
        mon = (
            ctx.db.query(Monetization)
            .filter(Monetization.channel_id == ctx.channel.id)
            .one_or_none()
        )
        if mon and mon.sponsor_active and mon.sponsor_script:
            if mon.sponsor_placement == "intro":
                ctx.video.script = f"{mon.sponsor_script}\n\n{ctx.video.script}"
            else:
                ctx.video.script = f"{ctx.video.script}\n\n{mon.sponsor_script}"

        ctx.db.commit()

        cost_guard.record_spend(
            ctx.db, "openai", "script", openai_client.EST_SCRIPT_USD,
            channel_id=ctx.channel.id, video_id=ctx.video.id,
        )
        ctx.log(f"scripted {len(ctx.data['beats'])} beats")
