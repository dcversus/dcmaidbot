"""Chat Buffer service for handling bulk message processing across multiple chats."""

import asyncio
import logging
import os
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Deque, Dict, List, Optional, Set

from services.llm_service import LLMService

logger = logging.getLogger(__name__)


class ChatType(Enum):
    """Chat type classification for processing priority."""

    PERSONAL = "personal"
    GROUP = "group"
    CHANNEL = "channel"
    SUPERGROUP = "supergroup"


@dataclass
class BufferedMessage:
    """Represents a message in the buffer."""

    id: int
    user_id: int
    chat_id: int
    message_id: int
    text: str
    message_type: str
    language: Optional[str]
    timestamp: datetime
    username: Optional[str]
    first_name: Optional[str]
    chat_type: ChatType
    is_admin: bool
    is_mention: bool
    processed: bool = False


@dataclass
class ChatSummary:
    """Summary of a chat's current state."""

    chat_id: int
    chat_title: str
    chat_type: ChatType
    message_count: int
    last_activity: datetime
    active_users: Set[int]
    admin_present: bool
    buffer_size: int
    needs_processing: bool = False
    last_summary: Optional[str] = None


class ChatBuffer:
    """Manages message buffering for bulk processing across multiple chats."""

    def __init__(self):
        self.buffer_size = 100  # Messages per chat before triggering processing
        self.max_buffer_age = timedelta(minutes=30)  # Max age before forced processing
        self.llm_service = LLMService()

        # Per-chat message buffers
        self.chat_buffers: Dict[int, Deque[BufferedMessage]] = defaultdict(
            lambda: deque(maxlen=200)
        )

        # Chat summaries for context
        self.chat_summaries: Dict[int, ChatSummary] = {}

        # Global statistics
        self.total_messages_processed = 0
        self.chats_active: Set[int] = set()

        # Processing flags
        self._processing_lock = asyncio.Lock()
        self._chat_processing: Set[int] = set()

    async def add_message(
        self,
        user_id: int,
        chat_id: int,
        message_id: int,
        text: str,
        message_type: str = "text",
        language: Optional[str] = None,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        chat_type: str = "group",
        is_mention: bool = False,
    ) -> bool:
        """Add a message to the buffer and check if processing should be triggered."""

        # Check if user is admin
        admin_ids = [
            int(id.strip())
            for id in os.getenv("ADMIN_IDS", "").split(",")
            if id.strip()
        ]
        is_admin = user_id in admin_ids

        # Create buffered message
        buffered_msg = BufferedMessage(
            id=message_id,
            user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            message_type=message_type,
            language=language,
            timestamp=datetime.utcnow(),
            username=username,
            first_name=first_name,
            chat_type=ChatType(chat_type),
            is_admin=is_admin,
            is_mention=is_mention,
        )

        # Add to chat buffer
        self.chat_buffers[chat_id].append(buffered_msg)
        self.chats_active.add(chat_id)
        self.total_messages_processed += 1

        # Update chat summary
        await self._update_chat_summary(chat_id, buffered_msg)

        # Check if processing should be triggered
        should_process = await self._should_process_chat(chat_id)

        if should_process:
            await self._trigger_memory_implicator(chat_id)

        return should_process

    async def _update_chat_summary(self, chat_id: int, message: BufferedMessage):
        """Update the summary for a specific chat."""

        if chat_id not in self.chat_summaries:
            self.chat_summaries[chat_id] = ChatSummary(
                chat_id=chat_id,
                chat_title=message.chat_type.value,
                chat_type=message.chat_type,
                message_count=0,
                last_activity=message.timestamp,
                active_users=set(),
                admin_present=message.is_admin,
                buffer_size=0,
            )

        summary = self.chat_summaries[chat_id]
        summary.message_count += 1
        summary.last_activity = message.timestamp
        summary.active_users.add(message.user_id)
        summary.buffer_size = len(self.chat_buffers[chat_id])

        if message.is_admin:
            summary.admin_present = True

        # Mark as needing processing if buffer is getting full
        summary.needs_processing = summary.buffer_size >= self.buffer_size

    async def _should_process_chat(self, chat_id: int) -> bool:
        """Determine if a chat should be processed based on various conditions."""

        buffer = self.chat_buffers[chat_id]
        summary = self.chat_summaries.get(chat_id)

        if not summary:
            return False

        # Trigger conditions
        conditions = [
            len(buffer) >= self.buffer_size,  # Buffer full
            (datetime.utcnow() - summary.last_activity)
            > self.max_buffer_age,  # Too old
            summary.admin_present
            and len(buffer) >= 20,  # Admin in chat with decent buffer
        ]

        return any(conditions)

    async def _trigger_memory_implicator(self, chat_id: int):
        """Trigger memory implicator for a specific chat."""

        if chat_id in self._chat_processing:
            return  # Already processing

        async with self._processing_lock:
            if chat_id not in self._chat_processing:
                self._chat_processing.add(chat_id)
                # Schedule processing in background
                asyncio.create_task(self._process_chat_buffer(chat_id))

    async def _process_chat_buffer(self, chat_id: int):
        """Process a chat's message buffer through memory implicator."""

        try:
            buffer = self.chat_buffers[chat_id]
            if not buffer:
                return

            # Get messages to process
            messages_to_process = list(buffer)

            # Mark as being processed
            for msg in messages_to_process:
                msg.processed = True

            logger.info(
                f"Processing {len(messages_to_process)} messages for chat {chat_id}"
            )

            # Import here to avoid circular imports
            from services.memory_implicator import MemoryImplicator

            implicator = MemoryImplicator()
            await implicator.process_messages(messages_to_process)

            # Update chat summary
            summary = self.chat_summaries.get(chat_id)
            if summary:
                summary.needs_processing = False
                summary.last_summary = await self._generate_chat_summary(
                    messages_to_process
                )

            # Clear processed messages from buffer (keep recent ones for context)
            messages_to_keep = len(buffer) // 3  # Keep 1/3 for context
            while len(buffer) > messages_to_keep:
                buffer.popleft()

        except Exception as e:
            logger.error(f"Error processing chat buffer for {chat_id}: {e}")
        finally:
            self._chat_processing.discard(chat_id)

    async def _generate_chat_summary(self, messages: List[BufferedMessage]) -> str:
        """Generate a summary of recent messages for chat context."""

        if not messages:
            return ""

        # Prepare message context
        message_texts = []
        for msg in messages[-20:]:  # Last 20 messages
            user_name = msg.first_name or msg.username or f"User{msg.user_id}"
            message_texts.append(f"{user_name}: {msg.text[:100]}...")

        context = "\n".join(message_texts)

        # Generate summary using cheap LLM
        prompt = f"""Summarize this chat conversation in 2-3 sentences:

{context}

Focus on:
1. Main topics discussed
2. Key participants
3. Any important events or decisions

Keep it concise and factual."""

        try:
            response = await self.llm_service.client.chat.completions.create(
                model="gpt-4o-mini",  # Use cheap model for summaries
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.3,
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating chat summary: {e}")
            return f"Chat activity with {len(messages)} messages"

    async def get_chat_context(
        self, chat_id: int, limit: int = 50
    ) -> List[BufferedMessage]:
        """Get recent messages for a chat as context."""

        buffer = self.chat_buffers.get(chat_id, deque())
        return list(buffer)[-limit:]

    async def get_global_status(self) -> Dict:
        """Get global processing status across all chats."""

        total_buffered = sum(len(buffer) for buffer in self.chat_buffers.values())
        active_chats = len(self.chats_active)
        processing_chats = len(self._chat_processing)

        return {
            "total_messages_processed": self.total_messages_processed,
            "total_buffered": total_buffered,
            "active_chats": active_chats,
            "processing_chats": processing_chats,
            "chat_summaries": {
                chat_id: asdict(summary)
                for chat_id, summary in self.chat_summaries.items()
            },
            "average_buffer_size": total_buffered / max(active_chats, 1),
        }

    async def force_process_all(self):
        """Force process all buffered messages (for shutdown or maintenance)."""

        logger.info("Force processing all buffered messages")

        for chat_id in list(self.chats_active):
            if self.chat_buffers[chat_id]:
                await self._trigger_memory_implicator(chat_id)

        # Wait for all processing to complete
        while self._chat_processing:
            await asyncio.sleep(1)

        logger.info("Force processing completed")


# Global buffer instance
chat_buffer = ChatBuffer()
