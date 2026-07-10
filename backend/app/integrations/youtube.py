"""YouTube Data + Analytics API integration (OAuth, upload, insights).

Onboards EXISTING channels via OAuth (the API cannot create new channels).
"""
from __future__ import annotations

import json
from datetime import date, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from app.config import settings
from app.security import decrypt, encrypt

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/yt-analytics-monetary.readonly",
]


def _client_config() -> dict:
    return {
        "web": {
            "client_id": settings.youtube_client_id,
            "client_secret": settings.youtube_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.youtube_redirect_uri],
        }
    }


def build_authorization_url() -> tuple[str, str]:
    flow = Flow.from_client_config(_client_config(), scopes=SCOPES)
    flow.redirect_uri = settings.youtube_redirect_uri
    url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent"
    )
    return url, state


def handle_oauth_callback(code: str, state: str | None = None) -> dict:
    """Exchange the auth code for tokens and persist/refresh the channel."""
    flow = Flow.from_client_config(_client_config(), scopes=SCOPES, state=state)
    flow.redirect_uri = settings.youtube_redirect_uri
    flow.fetch_token(code=code)
    creds = flow.credentials

    channel_info = _fetch_own_channel(creds)
    persisted = _upsert_channel(channel_info, creds)
    return {"connected": True, **persisted}


def _fetch_own_channel(creds: Credentials) -> dict:
    yt = build("youtube", "v3", credentials=creds)
    resp = yt.channels().list(part="snippet", mine=True).execute()
    items = resp.get("items", [])
    if not items:
        raise ValueError("No channel found for this Google account.")
    item = items[0]
    snippet = item["snippet"]
    return {
        "youtube_channel_id": item["id"],
        "title": snippet.get("title", ""),
        "handle": snippet.get("customUrl"),
        "thumbnail_url": snippet.get("thumbnails", {}).get("default", {}).get("url"),
    }


def _upsert_channel(info: dict, creds: Credentials) -> dict:
    from app.database import SessionLocal
    from app.models.channel import Channel

    db = SessionLocal()
    try:
        channel = (
            db.query(Channel)
            .filter(Channel.youtube_channel_id == info["youtube_channel_id"])
            .one_or_none()
        )
        enc = encrypt(creds.refresh_token) if creds.refresh_token else ""
        if channel is None:
            channel = Channel(
                youtube_channel_id=info["youtube_channel_id"],
                title=info["title"],
                handle=info.get("handle"),
                thumbnail_url=info.get("thumbnail_url"),
                encrypted_refresh_token=enc,
                scopes=" ".join(SCOPES),
            )
            db.add(channel)
        else:
            channel.title = info["title"]
            channel.handle = info.get("handle")
            channel.thumbnail_url = info.get("thumbnail_url")
            if enc:
                channel.encrypted_refresh_token = enc
        db.commit()
        db.refresh(channel)
        return {"channel_id": channel.id, "title": channel.title}
    finally:
        db.close()


def credentials_for_channel(channel) -> Credentials:
    """Build refreshable Credentials from a stored channel."""
    creds = Credentials(
        token=None,
        refresh_token=decrypt(channel.encrypted_refresh_token),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.youtube_client_id,
        client_secret=settings.youtube_client_secret,
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return creds


def upload_short(channel, file_path: str, title: str, description: str,
                 tags: list[str] | None = None, publish_at: str | None = None) -> str:
    """Upload a Short. Returns the YouTube video id."""
    creds = credentials_for_channel(channel)
    yt = build("youtube", "v3", credentials=creds)

    status = {"privacyStatus": "private" if publish_at else "public",
              "selfDeclaredMadeForKids": False}
    if publish_at:
        status["publishAt"] = publish_at  # RFC3339; schedules the video

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or [],
            "categoryId": "22",
        },
        "status": status,
    }
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = yt.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        _, response = request.next_chunk()
    return response["id"]


def fetch_analytics(channel, days: int = 28) -> list[dict]:
    """Fetch daily channel analytics rows for the last `days`."""
    creds = credentials_for_channel(channel)
    ya = build("youtubeAnalytics", "v2", credentials=creds)
    end = date.today()
    start = end - timedelta(days=days)
    resp = ya.reports().query(
        ids=f"channel=={channel.youtube_channel_id}",
        startDate=start.isoformat(),
        endDate=end.isoformat(),
        metrics="views,estimatedMinutesWatched,averageViewDuration,"
                "subscribersGained,likes,comments",
        dimensions="day",
    ).execute()

    headers = [h["name"] for h in resp.get("columnHeaders", [])]
    rows = []
    for row in resp.get("rows", []):
        rows.append(dict(zip(headers, row)))
    return rows


def update_video_metadata(channel, video_id: str, title: str | None = None,
                          description: str | None = None) -> None:
    """Update a live video's title/description (used for A/B title rotation)."""
    creds = credentials_for_channel(channel)
    yt = build("youtube", "v3", credentials=creds)
    current = yt.videos().list(part="snippet", id=video_id).execute()
    items = current.get("items", [])
    if not items:
        return
    snippet = items[0]["snippet"]
    if title is not None:
        snippet["title"] = title
    if description is not None:
        snippet["description"] = description
    yt.videos().update(part="snippet", body={"id": video_id, "snippet": snippet}).execute()


def get_video_stats(channel, video_id: str) -> dict:
    """Return cumulative statistics for a video (viewCount, likeCount, ...)."""
    creds = credentials_for_channel(channel)
    yt = build("youtube", "v3", credentials=creds)
    resp = yt.videos().list(part="statistics", id=video_id).execute()
    items = resp.get("items", [])
    stats = items[0].get("statistics", {}) if items else {}
    return {k: int(v) for k, v in stats.items() if str(v).isdigit()}


def set_thumbnail(channel, video_id: str, image_bytes: bytes) -> None:
    """Set a custom thumbnail for a video (requires a verified channel)."""
    from googleapiclient.http import MediaInMemoryUpload

    creds = credentials_for_channel(channel)
    yt = build("youtube", "v3", credentials=creds)
    media = MediaInMemoryUpload(image_bytes, mimetype="image/png")
    yt.thumbnails().set(videoId=video_id, media_body=media).execute()


def post_top_comment(channel, video_id: str, text: str) -> str | None:
    """Post a top-level comment (used for a pinned CTA). Best-effort."""
    creds = credentials_for_channel(channel)
    yt = build("youtube", "v3", credentials=creds)
    resp = yt.commentThreads().insert(
        part="snippet",
        body={
            "snippet": {
                "videoId": video_id,
                "topLevelComment": {"snippet": {"textOriginal": text}},
            }
        },
    ).execute()
    return resp.get("id")


def list_recent_comments(channel, max_results: int = 20) -> list[dict]:
    """List recent top-level comments across the channel's videos."""
    creds = credentials_for_channel(channel)
    yt = build("youtube", "v3", credentials=creds)
    resp = yt.commentThreads().list(
        part="snippet",
        allThreadsRelatedToChannelId=channel.youtube_channel_id,
        order="time",
        maxResults=max_results,
        textFormat="plainText",
    ).execute()

    comments = []
    for item in resp.get("items", []):
        top = item["snippet"]["topLevelComment"]
        snip = top["snippet"]
        comments.append({
            "comment_id": top["id"],
            "video_id": snip.get("videoId"),
            "author": snip.get("authorDisplayName"),
            "text": snip.get("textOriginal", ""),
            "reply_count": item["snippet"].get("totalReplyCount", 0),
        })
    return comments


def reply_to_comment(channel, parent_id: str, text: str) -> str | None:
    """Post a reply to a top-level comment."""
    creds = credentials_for_channel(channel)
    yt = build("youtube", "v3", credentials=creds)
    resp = yt.comments().insert(
        part="snippet",
        body={"snippet": {"parentId": parent_id, "textOriginal": text}},
    ).execute()
    return resp.get("id")


def fetch_video_analytics(channel, youtube_video_id: str, days: int = 28) -> list[dict]:
    """Fetch daily analytics rows for a single video."""
    creds = credentials_for_channel(channel)
    ya = build("youtubeAnalytics", "v2", credentials=creds)
    end = date.today()
    start = end - timedelta(days=days)
    try:
        resp = ya.reports().query(
            ids=f"channel=={channel.youtube_channel_id}",
            startDate=start.isoformat(),
            endDate=end.isoformat(),
            metrics="views,estimatedMinutesWatched,averageViewDuration,likes,comments",
            dimensions="day",
            filters=f"video=={youtube_video_id}",
        ).execute()
    except Exception:
        return []
    headers = [h["name"] for h in resp.get("columnHeaders", [])]
    return [dict(zip(headers, row)) for row in resp.get("rows", [])]


def fetch_revenue(channel, days: int = 28) -> list[dict]:
    """Fetch daily monetary metrics. Returns [] if the channel isn't monetized
    or the monetary scope wasn't granted."""
    creds = credentials_for_channel(channel)
    ya = build("youtubeAnalytics", "v2", credentials=creds)
    end = date.today()
    start = end - timedelta(days=days)
    try:
        resp = ya.reports().query(
            ids=f"channel=={channel.youtube_channel_id}",
            startDate=start.isoformat(),
            endDate=end.isoformat(),
            metrics="estimatedRevenue,cpm,playbackBasedCpm",
            dimensions="day",
        ).execute()
    except Exception:
        return []

    headers = [h["name"] for h in resp.get("columnHeaders", [])]
    rows = []
    for row in resp.get("rows", []):
        rows.append(dict(zip(headers, row)))
    return rows
