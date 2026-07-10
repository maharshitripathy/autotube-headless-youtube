"""YouTube OAuth onboarding routes.

Full token exchange + channel persistence is implemented in P1. These
endpoints define the onboarding flow surface used by the web wizard.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from app.api.deps import require_admin
from app.config import settings
from app.integrations import youtube as yt

router = APIRouter()


@router.get("/youtube/start", dependencies=[Depends(require_admin)])
def youtube_start():
    """Return the Google consent URL for connecting a channel."""
    url, state = yt.build_authorization_url()
    return {"authorization_url": url, "state": state}


@router.get("/youtube/callback")
def youtube_callback(code: str, state: str | None = None):
    """OAuth redirect target. Exchanges the code, stores the channel, then
    redirects the browser back to the web app's Channels page."""
    try:
        yt.handle_oauth_callback(code=code, state=state)
        return RedirectResponse(f"{settings.web_app_url}/channels?connected=1")
    except Exception as exc:  # surface the failure to the UI
        return RedirectResponse(f"{settings.web_app_url}/channels?error={exc}")
