"""Ad planner: decide which videos to promote and how to allocate budget.

Strategy — amplify winners, not losers:
  score = 0.6*retention + 0.3*engagement + 0.1*recency
where retention = avg_view_duration / assumed_length, engagement = (likes+comments)/views.
The monthly ad budget is split across the top-scoring published videos that
don't already have an active campaign, weighted by score. A target ROAS caps
per-video spend so we don't overspend relative to expected revenue.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.integrations import google_ads
from app.models.ad_campaign import AdCampaign
from app.models.analytics import AnalyticsSnapshot
from app.models.channel import Channel
from app.models.cost import CostLedgerEntry
from app.models.enums import VideoStatus
from app.models.settings import get_app_settings
from app.models.video import Video
from app.services import cost_guard


def _video_score(db: Session, video: Video) -> float:
    """Heuristic amplification score from stored analytics."""
    snap = (
        db.query(AnalyticsSnapshot)
        .filter(AnalyticsSnapshot.channel_id == video.channel_id)
        .order_by(AnalyticsSnapshot.day.desc())
        .first()
    )
    retention = min(1.0, (snap.avg_view_duration_sec / 45.0) if snap else 0.4)
    views = max(1, snap.views if snap else 1)
    engagement = min(1.0, ((snap.likes + snap.comments) / views) if snap else 0.05)
    age_days = (datetime.now(timezone.utc) - video.created_at).days if video.created_at else 30
    recency = max(0.0, 1.0 - age_days / 30.0)
    return round(0.6 * retention + 0.3 * engagement + 0.1 * recency, 4)


def recommend(db: Session, channel: Channel, limit: int = 5) -> list[dict]:
    """Return suggested promotions (not persisted) for the channel's best videos."""
    settings = get_app_settings(db)
    budget = settings.monthly_ad_budget_usd
    videos = db.execute(
        select(Video).where(
            Video.channel_id == channel.id,
            Video.status == VideoStatus.published,
            Video.youtube_video_id.isnot(None),
        )
    ).scalars().all()

    scored = sorted(
        ((v, _video_score(db, v)) for v in videos), key=lambda x: x[1], reverse=True
    )[:limit]
    total_score = sum(s for _, s in scored) or 1.0

    suggestions = []
    for v, score in scored:
        share = score / total_score
        total = round(budget * share, 2)
        suggestions.append({
            "video_id": v.id,
            "youtube_video_id": v.youtube_video_id,
            "title": v.title or v.topic,
            "score": score,
            "suggested_total_budget_usd": total,
            "suggested_daily_budget_usd": round(total / 30.0, 2),
        })
    return suggestions


def plan_campaigns(db: Session, channel: Channel, limit: int = 5) -> list[AdCampaign]:
    """Persist planned campaigns from recommendations (skips videos already promoted)."""
    created = []
    for s in recommend(db, channel, limit=limit):
        exists = db.execute(
            select(AdCampaign).where(
                AdCampaign.video_id == s["video_id"],
                AdCampaign.status.in_(["planned", "active", "paused"]),
            )
        ).scalar_one_or_none()
        if exists or s["suggested_total_budget_usd"] <= 0:
            continue
        camp = AdCampaign(
            channel_id=channel.id,
            video_id=s["video_id"],
            youtube_video_id=s["youtube_video_id"],
            daily_budget_usd=s["suggested_daily_budget_usd"],
            total_budget_usd=s["suggested_total_budget_usd"],
            status="planned",
        )
        db.add(camp)
        created.append(camp)
    db.commit()
    for c in created:
        db.refresh(c)
    return created


def launch_campaign(db: Session, campaign: AdCampaign) -> AdCampaign:
    """Activate a campaign (via Google Ads if configured, else mark active manually)."""
    campaign.status = "active"
    campaign.start_at = datetime.now(timezone.utc)
    if google_ads.is_configured() and campaign.youtube_video_id:
        try:
            campaign.external_id = google_ads.create_video_campaign(
                campaign.youtube_video_id, campaign.daily_budget_usd, campaign.objective
            )
        except Exception:
            pass
    db.commit()
    db.refresh(campaign)
    return campaign


def record_ad_spend(db: Session, campaign: AdCampaign, amount_usd: float) -> None:
    """Record ad spend to the campaign and the cost ledger (feeds ROI/profit)."""
    campaign.spend_usd = (campaign.spend_usd or 0.0) + amount_usd
    db.commit()
    cost_guard.record_spend(
        db, "ads", "promotion", amount_usd,
        channel_id=campaign.channel_id, video_id=campaign.video_id,
    )


def sync_campaigns(db: Session) -> dict:
    """Pull live stats for active campaigns and record incremental spend."""
    active = db.execute(
        select(AdCampaign).where(AdCampaign.status == "active")
    ).scalars().all()
    synced = 0
    for camp in active:
        if not (camp.external_id and google_ads.is_configured()):
            continue
        try:
            stats = google_ads.fetch_campaign_stats(camp.external_id)
        except Exception:
            continue
        new_spend = float(stats.get("spend_usd", 0.0))
        delta = max(0.0, new_spend - (camp.spend_usd or 0.0))
        camp.impressions = int(stats.get("impressions", camp.impressions))
        camp.views = int(stats.get("views", camp.views))
        camp.clicks = int(stats.get("clicks", camp.clicks))
        camp.conversions = int(stats.get("conversions", camp.conversions))
        if delta > 0:
            record_ad_spend(db, camp, delta)
        # Stop when the total budget is exhausted.
        if camp.total_budget_usd and camp.spend_usd >= camp.total_budget_usd:
            camp.status = "completed"
            camp.end_at = datetime.now(timezone.utc)
        db.commit()
        synced += 1
    return {"synced": synced}


def channel_ad_summary(db: Session, channel_id: int, days: int = 28) -> dict:
    """Ad spend vs attributed revenue → ROAS."""
    from datetime import date

    since_date = date.today() - timedelta(days=days)
    since_dt = datetime.now(timezone.utc) - timedelta(days=days)

    ad_spend = float(db.execute(
        select(func.coalesce(func.sum(CostLedgerEntry.amount_usd), 0.0)).where(
            CostLedgerEntry.channel_id == channel_id,
            CostLedgerEntry.provider == "ads",
            CostLedgerEntry.created_at >= since_dt,
        )
    ).scalar_one())
    revenue = float(db.execute(
        select(func.coalesce(func.sum(AnalyticsSnapshot.estimated_revenue), 0.0)).where(
            AnalyticsSnapshot.channel_id == channel_id,
            AnalyticsSnapshot.day >= since_date,
        )
    ).scalar_one())

    return {
        "channel_id": channel_id,
        "ad_spend_usd": round(ad_spend, 2),
        "attributed_revenue_usd": round(revenue, 2),
        "roas": round(revenue / ad_spend, 2) if ad_spend else 0.0,
    }
