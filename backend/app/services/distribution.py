"""Distribution service: repurpose a published video to other platforms."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.integrations import social
from app.models.channel import Channel
from app.models.distribution import Distribution
from app.models.video import Video
from app.services import storage


def distribute_video(db: Session, video: Video, platforms: list[str] | None = None) -> list[Distribution]:
    """Create distribution records (and post where APIs are configured)."""
    channel = db.get(Channel, video.channel_id)
    targets = platforms or (channel.distribute_platforms or [])
    if not video.video_key or not targets:
        return []

    download_url = storage.presigned_url(video.video_key, expires=7 * 24 * 3600)
    results: list[Distribution] = []

    for platform in targets:
        # Skip if we already distributed this video to the platform.
        existing = (
            db.query(Distribution)
            .filter(Distribution.video_id == video.id, Distribution.platform == platform)
            .one_or_none()
        )
        if existing:
            results.append(existing)
            continue

        caption = social.generate_caption(platform, video.title or "", video.description or "")
        dist = Distribution(
            video_id=video.id,
            channel_id=video.channel_id,
            platform=platform,
            caption=caption,
            download_url=download_url,
            status="ready_to_post",
        )
        if social.is_configured(platform):
            try:
                dist.external_id = social.post_video(platform, download_url, caption)
                dist.status = "posted"
            except Exception as exc:
                dist.status = "failed"
                dist.error = str(exc)
        db.add(dist)
        results.append(dist)

    db.commit()
    for r in results:
        db.refresh(r)
    return results
