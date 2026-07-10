"""Cross-platform distribution: TikTok & Instagram Reels.

Official posting APIs (TikTok Content Posting API, Instagram Graph API) require
approved apps and business accounts. Until tokens are configured, distribution
produces a "ready_to_post" export package (download URL + tailored caption).
"""
from __future__ import annotations

import os

PLATFORM_STYLES = {
    "tiktok": "punchy, trend-aware, 3-5 niche hashtags, casual tone",
    "reels": "aesthetic, concise, 3-5 hashtags, a soft call to follow",
}


def generate_caption(platform: str, title: str, description: str) -> str:
    """Create a platform-tailored caption. Falls back to a simple template
    if OpenAI is unavailable."""
    style = PLATFORM_STYLES.get(platform, "concise with a few hashtags")
    try:
        from app.integrations import openai_client
        import json

        resp = openai_client._client().chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You write social captions. Return strict JSON."},
                {"role": "user", "content": (
                    f"Platform: {platform} ({style}).\nTitle: {title}\n"
                    f"Description: {description}\n"
                    'Return JSON: {"caption": str}'
                )},
            ],
        )
        return json.loads(resp.choices[0].message.content)["caption"]
    except Exception:
        return f"{title}\n\n#shorts #viral"


def is_configured(platform: str) -> bool:
    if platform == "tiktok":
        return bool(os.getenv("TIKTOK_ACCESS_TOKEN"))
    if platform == "reels":
        return bool(os.getenv("INSTAGRAM_ACCESS_TOKEN"))
    return False


def post_video(platform: str, video_url: str, caption: str) -> str:
    """Post to the platform via its API. Raises if not configured."""
    if not is_configured(platform):
        raise RuntimeError(f"{platform} API not configured; use the export package instead.")
    # Placeholder for the approved-app API integration.
    raise NotImplementedError(f"{platform} posting not yet wired to a live app.")
