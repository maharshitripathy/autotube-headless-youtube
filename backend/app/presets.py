"""Niche presets to spin up new faceless channels quickly.

Applying a preset configures a channel's niche, cadence, style hints, and
seeds default monetization. It does not create YouTube channels (ToS) — it
configures an already-onboarded channel.
"""
from __future__ import annotations

PRESETS: list[dict] = [
    {
        "id": "scary_stories",
        "name": "Scary Stories",
        "niche": "short horror stories and creepy facts",
        "uploads_per_day": 2,
        "style": "dark cinematic, tense music, whispered narration",
        "hero_video_provider": "veo",
        "cta_text": "Follow for a scary story every night",
    },
    {
        "id": "fun_facts",
        "name": "Fun Facts",
        "niche": "surprising facts that sound fake but are true",
        "uploads_per_day": 3,
        "style": "bright, fast-paced, punchy captions",
        "hero_video_provider": "none",
        "cta_text": "Follow for a daily mind-blowing fact",
    },
    {
        "id": "motivation",
        "name": "Motivation",
        "niche": "stoic and motivational one-minute pep talks",
        "uploads_per_day": 2,
        "style": "epic orchestral, sweeping visuals, confident voice",
        "hero_video_provider": "luma",
        "cta_text": "Follow for daily motivation",
    },
    {
        "id": "history",
        "name": "History Bites",
        "niche": "fascinating history moments in under a minute",
        "uploads_per_day": 1,
        "style": "documentary, warm narration, archival visuals",
        "hero_video_provider": "none",
        "cta_text": "Follow for a piece of history daily",
    },
    {
        "id": "tech_news",
        "name": "Tech in 60s",
        "niche": "daily tech and AI news explained fast",
        "uploads_per_day": 2,
        "style": "clean, modern, energetic",
        "hero_video_provider": "runway",
        "cta_text": "Follow for daily tech news",
    },
    {
        "id": "money_tips",
        "name": "Money Tips",
        "niche": "personal finance and money-saving tips",
        "uploads_per_day": 1,
        "style": "friendly, trustworthy, clean graphics",
        "hero_video_provider": "none",
        "cta_text": "Follow for daily money tips",
    },
]


def get_preset(preset_id: str) -> dict | None:
    return next((p for p in PRESETS if p["id"] == preset_id), None)
