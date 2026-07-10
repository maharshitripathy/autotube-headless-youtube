"""Google Ads (YouTube video promotion) integration.

The Google Ads API requires a developer token, OAuth, and an approved account.
Until configured, campaigns remain in a 'planned' state and spend is recorded
manually. This module defines the interface the planner calls.
"""
from __future__ import annotations

import os


def is_configured() -> bool:
    return bool(os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN") and os.getenv("GOOGLE_ADS_CUSTOMER_ID"))


def create_video_campaign(youtube_video_id: str, daily_budget_usd: float,
                          objective: str = "views") -> str:
    """Create a YouTube video-view campaign. Returns an external campaign id.

    Raises if the Google Ads API is not configured.
    """
    if not is_configured():
        raise RuntimeError("Google Ads API not configured; manage this campaign manually.")
    # Placeholder for the google-ads client wiring.
    raise NotImplementedError("Google Ads campaign creation not yet wired to a live account.")


def fetch_campaign_stats(external_id: str) -> dict:
    """Return {spend_usd, impressions, views, clicks, conversions} for a campaign."""
    if not is_configured():
        return {}
    raise NotImplementedError("Google Ads stats fetch not yet wired to a live account.")
