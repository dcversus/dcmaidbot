"""API Key model for event endpoint authentication.

This model manages API keys that external systems can use
to send events to the dcmaidbot event collection endpoint.
"""

import secrets
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class ApiKey(Base):
    """API key model for authenticating event submissions."""

    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Key identification
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    key_prefix: Mapped[str] = mapped_column(String(8), nullable=False)  # First 8 chars for identification

    # Usage tracking
    usage_count: Mapped[int] = mapped_column(default=0)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Rate limiting
    rate_limit_per_minute: Mapped[int] = mapped_column(default=60)
    rate_limit_per_hour: Mapped[int] = mapped_column(default=1000)

    # Permissions and scope
    allowed_event_types: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Comma-separated list of event types
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status and lifecycle
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Created by (which admin created this key)
    created_by: Mapped[int] = mapped_column(nullable=False, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"ApiKey(id={self.id}, name='{self.name}', "
            f"prefix='{self.key_prefix}', active={self.is_active})"
        )

    @classmethod
    def generate_key(cls) -> str:
        """Generate a new secure API key."""
        return f"dcmaid_{secrets.token_urlsafe(32)}"

    @classmethod
    def hash_key(cls, key: str) -> str:
        """Hash an API key for storage."""
        import hashlib
        return hashlib.sha256(key.encode()).hexdigest()

    def get_prefix(self, key: str) -> str:
        """Get the prefix of a key for display purposes."""
        return key[:8]

    def verify_key(self, provided_key: str) -> bool:
        """Verify if the provided key matches this stored key."""
        return self.hash_key(provided_key) == self.key_hash

    def is_expired(self) -> bool:
        """Check if the API key has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def can_submit_event_type(self, event_type: str) -> bool:
        """Check if this API key is allowed to submit a specific event type."""
        if self.allowed_event_types is None:
            return True  # No restrictions

        allowed_types = [t.strip() for t in self.allowed_event_types.split(",")]
        return event_type in allowed_types

    def to_dict(self, include_hash: bool = False) -> dict:
        """Convert API key to dictionary representation."""
        result = {
            "id": self.id,
            "name": self.name,
            "key_prefix": self.key_prefix,
            "usage_count": self.usage_count,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "rate_limit_per_hour": self.rate_limit_per_hour,
            "allowed_event_types": self.allowed_event_types,
            "description": self.description,
            "is_active": self.is_active,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

        if include_hash:
            result["key_hash"] = self.key_hash

        return result
