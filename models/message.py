"""Message model for dcmaidbot."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Message(Base):
    """Message model - stores all chat messages for RAG."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=True)
    message_type: Mapped[str] = mapped_column(String(50), default="text")
    language: Mapped[str] = mapped_column(String(10), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )

    # For RAG (PRP-007) - will add pgvector column later
    # embedding: Mapped[list] = mapped_column(Vector(1536), nullable=True)

    def __repr__(self):
        return (
            f"<Message(id={self.id}, chat_id={self.chat_id}, user_id={self.user_id})>"
        )
