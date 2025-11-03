"""Nudge token model for dynamic nudge endpoint authentication.

This model allows dcmaidbot to create, manage, and rotate nudge tokens
for agent-to-user communication without requiring environment variable changes.
"""

import secrets
from datetime import datetime, timezone
from hashlib import sha256

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from core.services.database import Base


class NudgeToken(Base):
    """Dynamic nudge token for /nudge endpoint authentication."""

    __tablename__ = "nudge_tokens"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    token_prefix = Column(String(8), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    usage_count = Column(Integer, nullable=False, default=0)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, nullable=False, index=True)

    @staticmethod
    def generate_token() -> str:
        """Generate a cryptographically secure nudge token."""
        return f"nudge_{secrets.token_urlsafe(32)}"

    @staticmethod
    def hash_token(token: str) -> str:
        """Hash a token for secure storage."""
        return sha256(token.encode()).hexdigest()

    def is_expired(self) -> bool:
        """Check if the token is expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def is_valid(self) -> bool:
        """Check if the token is valid (active and not expired)."""
        return self.is_active and not self.is_expired()

    def __repr__(self) -> str:
        return (
            f"<NudgeToken(id={self.id}, name='{self.name}', "
            f"prefix='{self.token_prefix}', active={self.is_active})>"
        )
