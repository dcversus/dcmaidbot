"""Admin token model for webapp authentication.

This model provides secure token-based authentication for admin access
to the Telegram webapp mini-game creator system.
"""

import secrets
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, String, Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column

from core.services.database import Base


class AdminToken(Base):
    """Model for managing admin authentication tokens."""

    __tablename__ = "admin_tokens"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    token_prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)  # Admin user ID
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    @hybrid_property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.utcnow() > self.expires_at

    @hybrid_property
    def is_valid(self) -> bool:
        """Check if token is both active and not expired."""
        return self.is_active and not self.is_expired

    @classmethod
    def generate_token(cls, length: int = 32) -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(length)

    @classmethod
    def hash_token(cls, token: str) -> str:
        """Create a secure hash of the token."""
        import hashlib

        return hashlib.sha256(token.encode()).hexdigest()

    def __repr__(self) -> str:
        return f"<AdminToken(id={self.id}, name='{self.name}', prefix='{self.token_prefix}')>"
