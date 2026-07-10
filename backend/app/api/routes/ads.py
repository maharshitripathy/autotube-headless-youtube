"""Paid promotion (ad) routes: plan, launch, track, and summarize campaigns."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.database import get_db
from app.models.ad_campaign import AdCampaign
from app.models.channel import Channel
from app.services import ads

router = APIRouter(dependencies=[Depends(require_admin)])


class CampaignOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    channel_id: int
    video_id: int | None = None
    youtube_video_id: str | None = None
    objective: str
    daily_budget_usd: float
    total_budget_usd: float
    spend_usd: float
    status: str
    impressions: int
    views: int
    clicks: int
    conversions: int


class SpendIn(BaseModel):
    amount_usd: float


class CampaignUpdate(BaseModel):
    daily_budget_usd: float | None = None
    total_budget_usd: float | None = None
    status: str | None = None
    objective: str | None = None


@router.get("/campaigns", response_model=list[CampaignOut])
def list_campaigns(channel_id: int | None = None, db: Session = Depends(get_db)):
    stmt = select(AdCampaign).order_by(AdCampaign.created_at.desc())
    if channel_id is not None:
        stmt = stmt.where(AdCampaign.channel_id == channel_id)
    return db.execute(stmt).scalars().all()


@router.get("/recommend")
def recommend(channel_id: int, db: Session = Depends(get_db)):
    channel = db.get(Channel, channel_id)
    if not channel:
        raise HTTPException(404, "Channel not found")
    return ads.recommend(db, channel)


@router.post("/plan", response_model=list[CampaignOut])
def plan(channel_id: int, db: Session = Depends(get_db)):
    channel = db.get(Channel, channel_id)
    if not channel:
        raise HTTPException(404, "Channel not found")
    return ads.plan_campaigns(db, channel)


@router.post("/campaigns/{campaign_id}/launch", response_model=CampaignOut)
def launch(campaign_id: int, db: Session = Depends(get_db)):
    camp = db.get(AdCampaign, campaign_id)
    if not camp:
        raise HTTPException(404, "Campaign not found")
    return ads.launch_campaign(db, camp)


@router.post("/campaigns/{campaign_id}/spend", response_model=CampaignOut)
def record_spend(campaign_id: int, payload: SpendIn, db: Session = Depends(get_db)):
    camp = db.get(AdCampaign, campaign_id)
    if not camp:
        raise HTTPException(404, "Campaign not found")
    ads.record_ad_spend(db, camp, payload.amount_usd)
    db.refresh(camp)
    return camp


@router.patch("/campaigns/{campaign_id}", response_model=CampaignOut)
def update_campaign(campaign_id: int, payload: CampaignUpdate, db: Session = Depends(get_db)):
    camp = db.get(AdCampaign, campaign_id)
    if not camp:
        raise HTTPException(404, "Campaign not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(camp, field, value)
    db.commit()
    db.refresh(camp)
    return camp


@router.get("/summary")
def summary(channel_id: int, db: Session = Depends(get_db)):
    channel = db.get(Channel, channel_id)
    if not channel:
        raise HTTPException(404, "Channel not found")
    return ads.channel_ad_summary(db, channel_id)
