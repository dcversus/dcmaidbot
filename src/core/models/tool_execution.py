"""Tool Execution model for logging external tool usage."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.services.database import Base


class ToolExecution(Base):
    """Tool execution log for auditing and analysis."""

    __tablename__ = "tool_executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)

    # Request details
    parameters: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    request_timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )

    # Response details
    response_data: Mapped[str] = mapped_column(Text, nullable=True)  # JSON string
    response_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    # Performance metrics
    execution_time_ms: Mapped[int] = mapped_column(Integer, nullable=True)

    def __repr__(self):
        return (
            f"<ToolExecution(id={self.id}, tool={self.tool_name}, "
            f"user_id={self.user_id}, success={self.success})>"
        )
