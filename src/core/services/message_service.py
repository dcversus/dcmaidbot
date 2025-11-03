"""
Message Service - Manages message history storage and retrieval.

Stores all bot and user messages to database for conversation context.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.message import Message
from core.models.user import User


class MessageService:
    """Service for managing message history."""

    def __init__(self, session: AsyncSession):
        """Initialize MessageService with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def store_message(
        self,
        user_id: int,
        chat_id: int,
        message_text: str,
        is_bot: bool = False,
    ) -> Message:
        """Store a message to database.

        Args:
            user_id: Telegram user ID (will be mapped to internal DB user_id)
            chat_id: Telegram chat ID
            message_text: Message text content
            is_bot: Whether this is a bot message (default: False)

        Returns:
            Created Message object
        """
        # Map telegram_id to internal database user_id
        stmt = select(User.id).where(User.telegram_id == user_id)
        result = await self.session.execute(stmt)
        db_user_id = result.scalar_one_or_none()

        if db_user_id is None:
            # Create user if doesn't exist
            user = User(
                telegram_id=user_id,
                is_friend=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.session.add(user)
            await self.session.flush()  # Get the id without committing
            db_user_id = user.id

        message = Message(
            user_id=db_user_id,
            chat_id=chat_id,
            message_id=0,  # Dummy message_id for /call endpoint testing
            text=message_text,
            message_type="bot" if is_bot else "text",
            timestamp=datetime.utcnow(),
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def get_recent_messages(
        self,
        user_id: int,
        chat_id: int,
        limit: int = 20,
    ) -> list[Message]:
        """Get recent messages for a user/chat.

        Args:
            user_id: Telegram user ID
            chat_id: Telegram chat ID
            limit: Maximum number of messages to retrieve (default: 20)

        Returns:
            List of Message objects, ordered by most recent first
        """
        stmt = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(desc(Message.timestamp))
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        messages = result.scalars().all()

        # Return in chronological order (oldest first)
        return list(reversed(messages))

    async def get_message_count(
        self,
        user_id: Optional[int] = None,
        chat_id: Optional[int] = None,
    ) -> int:
        """Get message count for user/chat.

        Args:
            user_id: Optional Telegram user ID to filter
            chat_id: Optional Telegram chat ID to filter

        Returns:
            Count of messages matching filters
        """
        stmt = select(Message)

        if user_id is not None:
            stmt = stmt.where(Message.user_id == user_id)
        if chat_id is not None:
            stmt = stmt.where(Message.chat_id == chat_id)

        result = await self.session.execute(stmt)
        messages = result.scalars().all()
        return len(messages)
