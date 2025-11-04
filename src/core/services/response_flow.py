"""Intelligent Response Flow service for managing when and how to respond."""

import asyncio
import logging
import os
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict

from aiogram import Bot
from aiogram.types import Message

logger = logging.getLogger(__name__)


class ResponsePriority(Enum):
    """Priority levels for responses."""

    IMMEDIATE = 0  # Admin mentions, critical situations
    HIGH = 1  # Friend mentions, important questions
    MEDIUM = 2  # Regular interactions in personal chats
    LOW = 3  # Group messages, casual interactions
    MINIMAL = 4  # Public channels, low importance


class UserType(Enum):
    """User classification for response logic."""

    ADMIN = "admin"  # Bot admins from ENV
    FRIEND = "friend"  # Known friends from memories
    KNOWN = "known"  # People seen before
    STRANGER = "stranger"  # Unknown users


@dataclass
class ResponseDecision:
    """Decision about whether and how to respond."""

    should_respond: bool
    priority: ResponsePriority
    delay_seconds: int
    response_type: str
    reason: str


class ResponseFlow:
    """Manages intelligent response flow with delays and admin detection."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.admin_ids = [
            int(id.strip())
            for id in os.getenv("ADMIN_IDS", "").split(",")
            if id.strip()
        ]

        # Response timing configuration
        self.immediate_response_time = 0  # Admins
        self.fast_response_range = (5, 30)  # Friends
        self.normal_response_range = (15, 60)  # Known users
        self.slow_response_range = (30, 120)  # Strangers

        # Track recent responses to avoid spam
        self.recent_responses: Dict[int, datetime] = {}
        self.response_cooldown = timedelta(minutes=2)

        # Track chat activity
        self.chat_activity: Dict[int, datetime] = {}
        self.last_bot_response: Dict[int, datetime] = {}

    async def should_respond(self, message: Message) -> ResponseDecision:
        """Determine if and how to respond to a message."""

        # Get user classification
        user_type = await self._classify_user(message.from_user.id, message.chat.id)

        # Check for mentions
        is_mentioned = await self._is_bot_mentioned(message)

        # Check chat type and admin presence
        chat_has_admin = await self._chat_has_admin(message.chat.id)
        is_personal_chat = message.chat.type in ["private"]

        # Determine priority
        priority = self._calculate_priority(
            user_type=user_type,
            is_mentioned=is_mentioned,
            is_personal_chat=is_personal_chat,
            chat_has_admin=chat_has_admin,
        )

        # Calculate delay
        delay = self._calculate_delay(user_type, priority, message.chat.id)

        # Determine if should respond
        should_respond = await self._should_respond_logic(
            message=message,
            user_type=user_type,
            priority=priority,
            delay=delay,
            chat_has_admin=chat_has_admin,
        )

        # Response type
        response_type = self._determine_response_type(message, user_type, priority)

        # Reason for decision
        reason = self._generate_reason(
            user_type=user_type,
            priority=priority,
            is_mentioned=is_mentioned,
            chat_has_admin=chat_has_admin,
            should_respond=should_respond,
        )

        return ResponseDecision(
            should_respond=should_respond,
            priority=priority,
            delay_seconds=delay,
            response_type=response_type,
            reason=reason,
        )

    async def _classify_user(self, user_id: int, chat_id: int) -> UserType:
        """Classify the user type for response logic."""

        # Check if admin
        if user_id in self.admin_ids:
            return UserType.ADMIN

        # Check if friend (from memories)
        # TODO: Implement friend lookup from memory service
        # if await self._is_friend(user_id):
        #     return UserType.FRIEND

        # Check if known user (seen before)
        # TODO: Implement known user lookup
        # if await self._is_known_user(user_id):
        #     return UserType.KNOWN

        # Default to stranger
        return UserType.STRANGER

    async def _is_bot_mentioned(self, message: Message) -> bool:
        """Check if the bot is mentioned in the message."""

        if not message.text:
            return False

        text_lower = message.text.lower()

        # Check for @username mentions
        if message.entities:
            for entity in message.entities:
                if entity.type == "mention":
                    mention_text = message.text[
                        entity.offset : entity.offset + entity.length
                    ].lower()
                    if "dcmaidbot" in mention_text or "dcnotabot" in mention_text:
                        return True

        # Check for name mentions
        bot_names = ["dcmaidbot", "dcnotabot", "bot", "девочка", "кавай", "nya"]
        return any(name in text_lower for name in bot_names)

    async def _chat_has_admin(self, chat_id: int) -> bool:
        """Check if any admin is present in the chat."""

        # For now, assume admins might be in any chat
        # TODO: Implement actual chat member checking
        return True

    def _calculate_priority(
        self,
        user_type: UserType,
        is_mentioned: bool,
        is_personal_chat: bool,
        chat_has_admin: bool,
    ) -> ResponsePriority:
        """Calculate response priority based on various factors."""

        # Immediate priority for admin mentions or personal admin chats
        if user_type == UserType.ADMIN and (is_mentioned or is_personal_chat):
            return ResponsePriority.IMMEDIATE

        # High priority for mentions from friends
        if user_type == UserType.FRIEND and is_mentioned:
            return ResponsePriority.HIGH

        # High priority for mentions in admin-present chats
        if is_mentioned and chat_has_admin:
            return ResponsePriority.HIGH

        # Medium priority for personal chats
        if is_personal_chat:
            return ResponsePriority.MEDIUM

        # Low priority for group messages
        return ResponsePriority.LOW

    def _calculate_delay(
        self, user_type: UserType, priority: ResponsePriority, chat_id: int
    ) -> int:
        """Calculate response delay based on user type and priority."""

        # Immediate response for highest priority
        if priority == ResponsePriority.IMMEDIATE:
            return self.immediate_response_time

        # No response if delay would be too long
        if user_type == UserType.STRANGER:
            delay = random.randint(*self.slow_response_range)
            if delay > 100:  # Don't respond if delay > 100s
                return -1  # Signal to not respond
            return delay

        # Calculate delay based on user type
        if user_type == UserType.FRIEND:
            return random.randint(*self.fast_response_range)
        elif user_type == UserType.KNOWN:
            return random.randint(*self.normal_response_range)
        else:
            delay = random.randint(*self.slow_response_range)
            return delay if delay <= 100 else -1

    async def _should_respond_logic(
        self,
        message: Message,
        user_type: UserType,
        priority: ResponsePriority,
        delay: int,
        chat_has_admin: bool,
    ) -> bool:
        """Final logic to determine if should respond."""

        # Don't respond if delay is -1 (too long)
        if delay == -1:
            return False

        # Always respond to immediate priority
        if priority == ResponsePriority.IMMEDIATE:
            return True

        # Check cooldowns
        if await self._is_in_cooldown(message.from_user.id, message.chat.id):
            return False

        # Don't respond in chats without admins unless mentioned
        if not chat_has_admin and not await self._is_bot_mentioned(message):
            return False

        # Check bot activity level (avoid being too active)
        if await self._is_bot_too_active(message.chat.id):
            return False

        return True

    async def _is_in_cooldown(self, user_id: int, chat_id: int) -> bool:
        """Check if bot is in cooldown for this user/chat."""

        cooldown_key = f"{user_id}:{chat_id}"
        last_response = self.recent_responses.get(cooldown_key)

        if last_response:
            if datetime.utcnow() - last_response < self.response_cooldown:
                return True

        return False

    async def _is_bot_too_active(self, chat_id: int) -> bool:
        """Check if bot has been too active in this chat recently."""

        last_response = self.last_bot_response.get(chat_id)

        if last_response:
            # Don't respond if we've responded in the last 5 minutes
            if datetime.utcnow() - last_response < timedelta(minutes=5):
                return True

        return False

    def _determine_response_type(
        self, message: Message, user_type: UserType, priority: ResponsePriority
    ) -> str:
        """Determine the type of response to generate."""

        if priority == ResponsePriority.IMMEDIATE:
            return "immediate_help"
        elif user_type == UserType.ADMIN:
            return "admin_response"
        elif self._is_bot_mentioned(message):
            return "mention_response"
        elif message.chat.type == "private":
            return "personal_chat"
        else:
            return "group_interaction"

    def _generate_reason(
        self,
        user_type: UserType,
        priority: ResponsePriority,
        is_mentioned: bool,
        chat_has_admin: bool,
        should_respond: bool,
    ) -> str:
        """Generate a reason for the response decision."""

        parts = []

        # User type
        parts.append(f"User: {user_type.value}")

        # Priority
        parts.append(f"Priority: {priority.name}")

        # Special conditions
        if is_mentioned:
            parts.append("Bot mentioned")
        if chat_has_admin:
            parts.append("Admin present")

        # Final decision
        if not should_respond:
            if priority == ResponsePriority.LOW:
                parts.append("Low priority - skipping")
            else:
                parts.append("Cooldown or too active")
        else:
            parts.append("Will respond")

        return " | ".join(parts)

    async def execute_response(
        self, message: Message, decision: ResponseDecision, response_text: str
    ) -> bool:
        """Execute the response with appropriate delay."""

        if not decision.should_respond:
            return False

        try:
            # Apply delay
            if decision.delay_seconds > 0:
                await asyncio.sleep(decision.delay_seconds)

            # Send response
            await self.bot.send_message(
                chat_id=message.chat.id,
                text=response_text,
                reply_to_message_id=message.message_id
                if decision.priority != ResponsePriority.MINIMAL
                else None,
            )

            # Update tracking
            self._update_response_tracking(message.from_user.id, message.chat.id)

            logger.info(
                f"Responded to message in chat {message.chat.id} with {decision.delay_seconds}s delay"
            )
            return True

        except Exception as e:
            logger.error(f"Error executing response: {e}")
            return False

    def _update_response_tracking(self, user_id: int, chat_id: int):
        """Update tracking information for cooldown and activity management."""

        now = datetime.utcnow()

        # Update recent responses
        cooldown_key = f"{user_id}:{chat_id}"
        self.recent_responses[cooldown_key] = now

        # Update last bot response
        self.last_bot_response[chat_id] = now

        # Update chat activity
        self.chat_activity[chat_id] = now

        # Cleanup old entries
        self._cleanup_old_tracking()

    def _cleanup_old_tracking(self):
        """Clean up old tracking entries to prevent memory leaks."""

        cutoff = datetime.utcnow() - timedelta(hours=24)

        # Clean recent responses
        old_keys = [
            key
            for key, timestamp in self.recent_responses.items()
            if timestamp < cutoff
        ]
        for key in old_keys:
            del self.recent_responses[key]

        # Clean chat activity
        old_chats = [
            chat_id
            for chat_id, timestamp in self.chat_activity.items()
            if timestamp < cutoff
        ]
        for chat_id in old_chats:
            del self.chat_activity[chat_id]

        # Clean last bot responses
        old_responses = [
            chat_id
            for chat_id, timestamp in self.last_bot_response.items()
            if timestamp < cutoff
        ]
        for chat_id in old_responses:
            del self.last_bot_response[chat_id]

    async def get_response_stats(self) -> Dict:
        """Get statistics about response behavior."""

        now = datetime.utcnow()

        return {
            "recent_responses": len(self.recent_responses),
            "active_chats": len(self.chat_activity),
            "bot_responses_last_24h": len(
                [
                    ts
                    for ts in self.last_bot_response.values()
                    if now - ts < timedelta(hours=24)
                ]
            ),
            "admin_ids": self.admin_ids,
        }
