"""Agent 12 — QA / brand-safety: validate a video before publish.

Hard-fails (raises) on moderation-flagged content. Records soft warnings
otherwise so borderline videos can still be reviewed at the approval gate.
"""
from __future__ import annotations

from app.agents.base import BaseAgent, PipelineContext
from app.integrations import openai_client
from app.models.enums import AgentStep


class QAFailed(Exception):
    """Raised when a video fails a hard QA/safety check."""


class QAAgent(BaseAgent):
    name = "qa"
    step = AgentStep.render  # runs in the assembly phase, post-render

    MAX_SHORT_SECONDS = 60
    MIN_SHORT_SECONDS = 4

    def run(self, ctx: PipelineContext) -> None:
        notes: list[str] = []

        # Brand safety on the narration + metadata.
        text = f"{ctx.video.script or ''}\n{ctx.video.title or ''}\n{ctx.video.description or ''}"
        moderation = openai_client.moderate(text)
        if moderation["flagged"]:
            ctx.video.qa_passed = False
            ctx.video.qa_notes = [f"moderation: {', '.join(moderation['categories'])}"]
            ctx.db.commit()
            raise QAFailed(f"Content flagged: {moderation['categories']}")

        # Duration check.
        duration = ctx.data.get("duration") or 0
        if duration and duration > self.MAX_SHORT_SECONDS:
            notes.append(f"duration {duration:.1f}s exceeds Shorts limit")
        if duration and duration < self.MIN_SHORT_SECONDS:
            notes.append(f"duration {duration:.1f}s is very short")

        # Captions present.
        if not ctx.data.get("captions"):
            notes.append("no captions generated")

        # Metadata sanity.
        if not ctx.video.title:
            notes.append("missing title")
        elif len(ctx.video.title) > 100:
            notes.append("title exceeds 100 chars")
        if not ctx.video.video_key:
            notes.append("no rendered video file")

        ctx.video.qa_passed = len(notes) == 0
        ctx.video.qa_notes = notes
        ctx.db.commit()
        ctx.log(f"QA {'passed' if ctx.video.qa_passed else 'warnings: ' + '; '.join(notes)}")
