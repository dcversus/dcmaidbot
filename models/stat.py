"""Stat model for dcmaidbot."""

from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class Stat(Base):
    """Stat model - stores user statistics and metrics."""

    __tablename__ = "stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    stat_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Type of stat: message_count, joke_reactions, etc",
    )
    value: Mapped[float] = mapped_column(
        Float, nullable=False, comment="Numeric value of stat"
    )
    extra_data: Mapped[str] = mapped_column(
        String(500), nullable=True, comment="Additional context as JSON"
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )

    def __repr__(self):
        return (
            f"<Stat(id={self.id}, user_id={self.user_id}, "
            f"type={self.stat_type}, value={self.value})>"
        )
