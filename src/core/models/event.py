"""Event model for universal event collection system.

This model stores all Telegram button events, user interactions,
and other UI events for the dcmaidbot to process.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from core.services.database import Base


class Event(Base):
    """Universal event collection model for storing all user interactions."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Event identification
    event_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(nullable=False, index=True)
    chat_id: Mapped[Optional[int]] = mapped_column(nullable=True, index=True)

    # Event categorization
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    event_subtype: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Event data
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    button_text: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    callback_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Event status tracking
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="unread", index=True
    )  # unread, read, completed, failed

    # Processing metadata
    processed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    processing_attempts: Mapped[int] = mapped_column(default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("CURRENT_TIMESTAMP"), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"Event(id={self.id}, event_id={self.event_id}, "
            f"type={self.event_type}, status={self.status}, "
            f"user_id={self.user_id})"
        )

    def to_dict(self) -> dict:
        """Convert event to dictionary representation."""
        return {
            "id": self.id,
            "event_id": self.event_id,
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "event_type": self.event_type,
            "event_subtype": self.event_subtype,
            "data": self.data,
            "button_text": self.button_text,
            "callback_data": self.callback_data,
            "status": self.status,
            "processed_at": self.processed_at.isoformat()
            if self.processed_at
            else None,
            "processing_attempts": self.processing_attempts,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
