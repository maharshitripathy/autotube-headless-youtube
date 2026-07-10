"""Comment engagement: auto-reply to recent viewer comments with moderation."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.integrations import openai_client, youtube
from app.models.channel import Channel
from app.models.engagement import CommentReply


def engage_channel(db: Session, channel: Channel, limit: int = 20) -> dict:
    """Fetch recent comments, skip already-handled ones, and post AI replies."""
    try:
        comments = youtube.list_recent_comments(channel, max_results=limit)
    except Exception as exc:
        return {"error": str(exc)}

    replied = flagged = skipped = 0
    for c in comments:
        # Skip comments we've already handled.
        existing = (
            db.query(CommentReply)
            .filter(CommentReply.comment_id == c["comment_id"])
            .one_or_none()
        )
        if existing:
            skipped += 1
            continue

        # Moderate first — flag toxic content instead of replying.
        mod = openai_client.moderate(c["text"])
        if mod.get("flagged"):
            db.add(CommentReply(
                channel_id=channel.id, comment_id=c["comment_id"],
                youtube_video_id=c.get("video_id"), author=c.get("author"),
                comment_text=c["text"], action="flag",
            ))
            flagged += 1
            continue

        decision = openai_client.generate_reply(channel.engage_persona or "", c["text"], "")
        action = decision.get("action", "ignore")
        reply_text = decision.get("reply", "")

        if action == "reply" and reply_text:
            try:
                youtube.reply_to_comment(channel, c["comment_id"], reply_text)
            except Exception:
                action = "ignore"
            else:
                replied += 1

        db.add(CommentReply(
            channel_id=channel.id, comment_id=c["comment_id"],
            youtube_video_id=c.get("video_id"), author=c.get("author"),
            comment_text=c["text"], reply_text=reply_text if action == "reply" else None,
            action=action,
        ))

    db.commit()
    return {"replied": replied, "flagged": flagged, "skipped": skipped}


def engage_all_channels(db: Session) -> dict:
    results = {}
    for channel in db.query(Channel).filter(Channel.active, Channel.auto_engage).all():
        results[channel.id] = engage_channel(db, channel)
    return results
