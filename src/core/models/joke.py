"""Joke model for dcmaidbot."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.services.database import Base


class Joke(Base):
    """Joke model - stores jokes and reaction learning data."""

    __tablename__ = "jokes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(
        BigInteger, nullable=True, comment="Telegram message ID of joke"
    )
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Joke content
    joke_text: Mapped[str] = mapped_column(Text, nullable=False)
    joke_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="setup_punchline, pun, transliteration, etc"
    )
    language: Mapped[str] = mapped_column(
        String(10), nullable=True, comment="ru, en, mix"
    )
    context: Mapped[str] = mapped_column(
        Text, nullable=True, comment="What triggered the joke"
    )

    # Learning metrics
    reactions_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="Total reactions received"
    )
    likes_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="Positive reactions"
    )

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )

    def __repr__(self):
        return f"<Joke(id={self.id}, type={self.joke_type}, likes={self.likes_count})>"
