"""
Friend Model
============

Database model for friend relationships and social features.
Implements PRP-019 Friends System functionality.
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Friendship(Base):
    """Friend relationship model."""

    __tablename__ = "friendships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, comment="User who initiated friendship")
    friend_id = Column(Integer, nullable=False, comment="User who received friendship")
    status = Column(
        String(20), nullable=False, default="pending", comment="pending/active/blocked"
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    message = Column(
        Text, nullable=True, comment="Optional message with friend request"
    )
    blocked_reason = Column(
        Text, nullable=True, comment="Reason for blocking if status=blocked"
    )

    # Relationships
    user = relationship(
        "User", foreign_keys=[user_id], back_populates="friendships_initiated"
    )
    friend = relationship(
        "User", foreign_keys=[friend_id], back_populates="friendships_received"
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_friendships_user_id", "user_id"),
        Index("idx_friendships_friend_id", "friend_id"),
        Index("idx_friendships_status", "status"),
        Index("idx_friendships_pair", "user_id", "friend_id", unique=True),
        Index("idx_friendships_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<Friendship(id={self.id}, user_id={self.user_id}, friend_id={self.friend_id}, status={self.status})>"

    def to_dict(self):
        """Convert friendship to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "friend_id": self.friend_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "message": self.message,
            "blocked_reason": self.blocked_reason,
        }

    @property
    def is_active(self) -> bool:
        """Check if friendship is active."""
        return self.status == "active"

    @property
    def is_pending(self) -> bool:
        """Check if friendship is pending."""
        return self.status == "pending"

    @property
    def is_blocked(self) -> bool:
        """Check if friendship is blocked."""
        return self.status == "blocked"


class FriendRequest(Base):
    """Friend request model for detailed tracking."""

    __tablename__ = "friend_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    from_user_id = Column(Integer, nullable=False, comment="User sending request")
    to_user_id = Column(Integer, nullable=False, comment="User receiving request")
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        comment="pending/accepted/declined/ignored",
    )
    message = Column(Text, nullable=True, comment="Optional message with request")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    responded_at = Column(
        DateTime, nullable=True, comment="When request was responded to"
    )
    response_message = Column(Text, nullable=True, comment="Optional response message")

    # Indexes
    __table_args__ = (
        Index("idx_friend_requests_from", "from_user_id"),
        Index("idx_friend_requests_to", "to_user_id"),
        Index("idx_friend_requests_status", "status"),
        Index("idx_friend_requests_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<FriendRequest(id={self.id}, from_user={self.from_user_id}, to_user={self.to_user_id}, status={self.status})>"

    def to_dict(self):
        """Convert friend request to dictionary."""
        return {
            "id": self.id,
            "from_user_id": self.from_user_id,
            "to_user_id": self.to_user_id,
            "status": self.status,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "responded_at": self.responded_at.isoformat()
            if self.responded_at
            else None,
            "response_message": self.response_message,
        }
