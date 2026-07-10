"""Agent 11 — Monetize: enrich the description with affiliate links, CTA,
lead magnet, and prepare a pinned comment. Runs after SEO, before publish.
"""
from __future__ import annotations

from app.agents.base import BaseAgent, PipelineContext
from app.models.enums import AgentStep
from app.models.monetization import Monetization


class MonetizeAgent(BaseAgent):
    name = "monetize"
    step = AgentStep.seo  # shares the metadata phase

    def run(self, ctx: PipelineContext) -> None:
        mon = (
            ctx.db.query(Monetization)
            .filter(Monetization.channel_id == ctx.channel.id)
            .one_or_none()
        )
        if not mon:
            return

        text = (ctx.video.script or "") + " " + (ctx.video.topic or "")
        text_lower = text.lower()
        lines: list[str] = [ctx.video.description or ""]

        # Affiliate links whose keyword appears in the content (always include
        # those without a keyword as evergreen links).
        aff_lines = []
        for item in (mon.affiliate_links or []):
            kw = (item.get("keyword") or "").lower().strip()
            if not kw or kw in text_lower:
                label = item.get("label") or item.get("url")
                aff_lines.append(f"👉 {label}: {item['url']}")
        if aff_lines:
            lines.append("\n🛒 Links:")
            lines.extend(aff_lines)

        if mon.lead_url:
            cta = mon.cta_text or "Get more here"
            lines.append(f"\n✨ {cta}: {mon.lead_url}")

        if mon.sponsor_active and mon.sponsor_name:
            lines.append(f"\n🤝 Sponsored by {mon.sponsor_name}")

        ctx.video.description = "\n".join(p for p in lines if p).strip()

        # Pinned comment (first affiliate/lead link makes a good pin).
        if mon.pinned_comment:
            ctx.video.pinned_comment = mon.pinned_comment
        elif mon.lead_url:
            ctx.video.pinned_comment = f"{mon.cta_text or 'More here'} 👉 {mon.lead_url}"
        elif aff_lines:
            ctx.video.pinned_comment = aff_lines[0]

        ctx.db.commit()
        ctx.log("monetization applied to description/pinned comment")
