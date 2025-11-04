"""Fact model for dcmaidbot."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Fact(Base):
    """Fact model - stores facts about users for personalization."""

    __tablename__ = "facts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    fact_text: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Fact about the user"
    )
    source: Mapped[str] = mapped_column(
        Text, nullable=True, comment="Where this fact was learned from"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )

    def __repr__(self):
        fact_preview = self.fact_text[:50] if self.fact_text else ""
        return f"<Fact(id={self.id}, user_id={self.user_id}, fact='{fact_preview}...')>"
