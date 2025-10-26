"""Memory model for dcmaidbot."""
from datetime import datetime
from sqlalchemy import BigInteger, String, Text, Boolean, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class Memory(Base):
    """Memory model - stores bot memories and behavior patterns."""
    
    __tablename__ = "memories"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    admin_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="Admin who created memory")
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=True, comment="Specific chat or NULL for global")
    
    # Memory content
    prompt: Mapped[str] = mapped_column(Text, nullable=False, comment="Instructions for bot behavior")
    matching_expression: Mapped[str] = mapped_column(String(500), nullable=True, comment="Regex or text to match")
    action: Mapped[str] = mapped_column(String(255), nullable=True, comment="Action to take when matched")
    
    # Group chat allowance
    allowance_token: Mapped[str] = mapped_column(String(100), nullable=True, unique=True, comment="Token for group access")
    
    # Control
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, comment="Higher = checked first")
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Memory(id={self.id}, admin_id={self.admin_id}, prompt='{self.prompt[:50]}...')>"
