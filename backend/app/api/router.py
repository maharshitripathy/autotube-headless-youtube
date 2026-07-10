"""Aggregate API router."""
from fastapi import APIRouter

from app.api.routes import analytics, auth, calendar, channels, distribution, jobs, system, videos

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(channels.router, prefix="/channels", tags=["channels"])
api_router.include_router(videos.router, prefix="/videos", tags=["videos"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(distribution.router, prefix="/distribution", tags=["distribution"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
