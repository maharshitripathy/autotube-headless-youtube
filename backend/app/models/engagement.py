"""Record of an auto-generated reply to a viewer comment."""
from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin


class CommentReply(Base, TimestampMixin):
    __tablename__ = "comment_replies"

    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), index=True)

    comment_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    youtube_video_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    comment_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    reply_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    action: Mapped[str] = mapped_column(String(16), default="reply")  # reply | ignore | flag
