"""Pexels stock footage/photo search integration."""
from __future__ import annotations

import httpx

from app.config import settings

_BASE = "https://api.pexels.com"


def _headers() -> dict:
    return {"Authorization": settings.pexels_api_key}


def search_videos(query: str, per_page: int = 3, orientation: str = "portrait") -> list[dict]:
    """Search vertical stock video clips. Returns list of {url, width, height, duration}."""
    with httpx.Client(timeout=30) as client:
        resp = client.get(
            f"{_BASE}/videos/search",
            headers=_headers(),
            params={"query": query, "per_page": per_page, "orientation": orientation},
        )
        resp.raise_for_status()
        data = resp.json()

    results = []
    for video in data.get("videos", []):
        files = sorted(video.get("video_files", []), key=lambda f: f.get("height", 0), reverse=True)
        if files:
            best = files[0]
            results.append({
                "url": best["link"],
                "width": best.get("width"),
                "height": best.get("height"),
                "duration": video.get("duration"),
            })
    return results


def search_photos(query: str, per_page: int = 3, orientation: str = "portrait") -> list[str]:
    with httpx.Client(timeout=30) as client:
        resp = client.get(
            f"{_BASE}/v1/search",
            headers=_headers(),
            params={"query": query, "per_page": per_page, "orientation": orientation},
        )
        resp.raise_for_status()
        data = resp.json()
    return [p["src"]["large2x"] for p in data.get("photos", [])]
