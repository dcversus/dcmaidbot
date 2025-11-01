"""Chat Membership Validation service for managing chat access and auto-leave functionality."""

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

from aiogram import Bot
from aiogram.types import ChatMemberUpdated

logger = logging.getLogger(__name__)


class ChatAccessDecision(Enum):
    """Decision about chat access."""

    ALLOW = "allow"  # Bot can stay in chat
    LEAVE_IMMEDIATELY = "leave_immediately"  # Leave immediately
    LEAVE_WITH_MESSAGE = "leave_with_message"  # Leave with goodbye message


@dataclass
class ChatValidationResult:
    """Result of chat validation."""

    decision: ChatAccessDecision
    reason: str
    admin_ids: List[int]
    admin_present: bool
    added_by_admin: bool
    chat_type: str


class ChatValidator:
    """Validates chat membership and manages auto-leave functionality."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.admin_ids = [
            int(id.strip())
            for id in os.getenv("ADMIN_IDS", "").split(",")
            if id.strip()
        ]

        # Track validation results and decisions
        self.validation_history: Dict[int, List[ChatValidationResult]] = {}
        self.leave_attempts: Dict[int, int] = {}

        # Cooldown for validation checks
        self.validation_cooldown = timedelta(hours=1)
        self.last_validation: Dict[int, datetime] = {}

        # Messages for leaving chats
        self.goodbye_messages = [
            "Прощайте! 🐾 Было приятно познакомиться!",
            "Пока-пока! Кавай~ 🎀",
            "Time to say goodbye! Nyaa~ 💕",
            "Ботик уходит, но не прощается! ~",
            "До новых встреч! ✨",
            "Bye-bye! Don't forget me! 🌸",
            "Это было мило, но мне пора! 👋",
            "Спасибо за компанию, прощайте! 💖",
        ]

        self.joke_goodbyes = [
            "Ой, кажется, я случайно попала не туда! 🤭 Прощайте!",
            "Меня сюда позвали, но я кажется опоздала на вечеринку! 🎉 Пока!",
            "Кажется, это чат для взрослых... Я еще слишком маленькая! 👶 Bye!",
            "Ой, прости! Я thought this was the cat chat! 🐱 Прощайте!",
            "Я поняла, что здесь нет никого из моих друзей... Так что я ушла! 🚪💨",
            "Опа! Wrong chat! Прости, если помешала! 😅 Bye!",
            "Кажется, я потерялась... Пойду искать своих друзей! 🗺️ Прощайте!",
            "Этот чат слишком серьезный для меня! Я prefer кавайные чаты! ✨ Пока!",
        ]

    async def validate_chat_access(
        self, chat_id: int, chat_type: str, added_by: Optional[int] = None
    ) -> ChatValidationResult:
        """Validate if bot should have access to a chat."""

        # Check cooldown
        if await self._is_in_cooldown(chat_id):
            return self._get_last_validation_result(chat_id)

        try:
            # Get chat member information
            admin_ids, admin_present = await self._get_chat_admins(chat_id)

            # Check if added by admin
            added_by_admin = added_by in self.admin_ids if added_by else False

            # Make validation decision
            decision, reason = self._make_validation_decision(
                chat_type=chat_type,
                admin_ids=admin_ids,
                admin_present=admin_present,
                added_by_admin=added_by_admin,
            )

            result = ChatValidationResult(
                decision=decision,
                reason=reason,
                admin_ids=admin_ids,
                admin_present=admin_present,
                added_by_admin=added_by_admin,
                chat_type=chat_type,
            )

            # Store validation result
            self._store_validation_result(chat_id, result)

            return result

        except Exception as e:
            logger.error(f"Error validating chat {chat_id}: {e}")
            # Default to allow on error
            return ChatValidationResult(
                decision=ChatAccessDecision.ALLOW,
                reason="Validation error - allowing access",
                admin_ids=[],
                admin_present=False,
                added_by_admin=False,
                chat_type=chat_type,
            )

    async def _get_chat_admins(self, chat_id: int) -> tuple[List[int], bool]:
        """Get list of admin IDs in the chat and check if any known admin is present."""

        try:
            # Try to get chat administrators
            admins = await self.bot.get_chat_administrators(chat_id)
            admin_ids = [admin.user.id for admin in admins]

            # Check if any known admin is present
            admin_present = any(admin_id in self.admin_ids for admin_id in admin_ids)

            return admin_ids, admin_present

        except Exception as e:
            logger.error(f"Error getting chat admins for {chat_id}: {e}")
            # Fallback: assume no admins if we can't check
            return [], False

    def _make_validation_decision(
        self,
        chat_type: str,
        admin_ids: List[int],
        admin_present: bool,
        added_by_admin: bool,
    ) -> tuple[ChatAccessDecision, str]:
        """Make the validation decision based on chat criteria."""

        # Always allow in direct chats with admins
        if chat_type == "private":
            return ChatAccessDecision.ALLOW, "Private chat - always allowed"

        # Allow if added by admin
        if added_by_admin:
            return ChatAccessDecision.ALLOW, "Added by admin - allowed"

        # Allow if admin is present in chat
        if admin_present:
            return ChatAccessDecision.ALLOW, "Admin present in chat - allowed"

        # For channels - more permissive
        if chat_type in ["channel"]:
            # Allow if channel seems legitimate
            return ChatAccessDecision.ALLOW, "Channel access allowed"

        # For groups - stricter
        if chat_type in ["group", "supergroup"]:
            # Check if it's a large group (might be public)
            # If we can't determine, be cautious and leave
            return (
                ChatAccessDecision.LEAVE_WITH_MESSAGE,
                "No admin present - leaving with message",
            )

        # Default decision for unknown chat types
        return (
            ChatAccessDecision.LEAVE_WITH_MESSAGE,
            "Unknown chat type - leaving with message",
        )

    async def _is_in_cooldown(self, chat_id: int) -> bool:
        """Check if validation is in cooldown for this chat."""

        last_check = self.last_validation.get(chat_id)
        if last_check:
            if datetime.utcnow() - last_check < self.validation_cooldown:
                return True
        return False

    def _get_last_validation_result(self, chat_id: int) -> ChatValidationResult:
        """Get the last validation result for a chat."""

        history = self.validation_history.get(chat_id, [])
        return (
            history[-1]
            if history
            else ChatValidationResult(
                decision=ChatAccessDecision.ALLOW,
                reason="No previous validation - allowing",
                admin_ids=[],
                admin_present=False,
                added_by_admin=False,
                chat_type="unknown",
            )
        )

    def _store_validation_result(self, chat_id: int, result: ChatValidationResult):
        """Store validation result for the chat."""

        if chat_id not in self.validation_history:
            self.validation_history[chat_id] = []

        self.validation_history[chat_id].append(result)

        # Keep only last 10 results
        if len(self.validation_history[chat_id]) > 10:
            self.validation_history[chat_id] = self.validation_history[chat_id][-10:]

        # Update last validation time
        self.last_validation[chat_id] = datetime.utcnow()

    async def execute_leave_decision(
        self, chat_id: int, validation_result: ChatValidationResult
    ) -> bool:
        """Execute the leave decision if needed."""

        if validation_result.decision == ChatAccessDecision.ALLOW:
            return True  # Staying in chat

        try:
            if validation_result.decision == ChatAccessDecision.LEAVE_IMMEDIATELY:
                await self.bot.leave_chat(chat_id)
                logger.info(f"Left chat {chat_id} immediately")
                return True

            elif validation_result.decision == ChatAccessDecision.LEAVE_WITH_MESSAGE:
                # Send goodbye message first
                goodbye_msg = await self._get_goodbye_message(validation_result)
                await self.bot.send_message(chat_id, goodbye_msg)

                # Small delay to ensure message is sent
                await asyncio.sleep(2)

                # Leave chat
                await self.bot.leave_chat(chat_id)
                logger.info(f"Left chat {chat_id} with goodbye message")
                return True

        except Exception as e:
            logger.error(f"Error leaving chat {chat_id}: {e}")
            # Try to leave without message if sending failed
            try:
                await self.bot.leave_chat(chat_id)
                logger.info(f"Left chat {chat_id} after error")
                return True
            except Exception as e2:
                logger.error(f"Failed to leave chat {chat_id} even after retry: {e2}")
                return False

        return False

    async def _get_goodbye_message(
        self, validation_result: ChatValidationResult
    ) -> str:
        """Get an appropriate goodbye message."""

        import random

        # Mix of regular goodbyes and joke goodbyes
        all_messages = self.goodbye_messages + self.joke_goodbyes
        return random.choice(all_messages)

    async def handle_new_chat_member(self, event: ChatMemberUpdated) -> bool:
        """Handle when bot is added to a new chat."""

        if event.new_chat_member.user.id != self.bot.id:
            return True  # Not about bot

        chat_id = event.chat.id
        chat_type = event.chat.type

        # Try to determine who added the bot
        added_by = None
        if hasattr(event, "from_user") and event.from_user:
            added_by = event.from_user.id

        logger.info(f"Bot added to chat {chat_id} ({chat_type}) by {added_by}")

        # Validate access
        validation_result = await self.validate_chat_access(
            chat_id, chat_type, added_by
        )

        # Execute decision
        return await self.execute_leave_decision(chat_id, validation_result)

    async def periodic_validation_check(self):
        """Periodically check chats and leave if validation criteria changed."""

        logger.info("Starting periodic validation check")

        # Get all chats the bot is currently in
        try:
            # This would require getting all active chats from the database
            # For now, we'll check the validation history
            for chat_id, history in self.validation_history.items():
                if not history:
                    continue

                last_result = history[-1]

                # Only recheck chats we decided to stay in
                if last_result.decision == ChatAccessDecision.ALLOW:
                    # Check if validation is still valid
                    new_result = await self.validate_chat_access(
                        chat_id, last_result.chat_type
                    )

                    # If decision changed to leave, execute it
                    if new_result.decision != ChatAccessDecision.ALLOW:
                        logger.info(
                            f"Validation decision changed for chat {chat_id}: {new_result.reason}"
                        )
                        await self.execute_leave_decision(chat_id, new_result)

        except Exception as e:
            logger.error(f"Error in periodic validation check: {e}")

        logger.info("Periodic validation check completed")

    async def get_validation_stats(self) -> Dict:
        """Get statistics about validation decisions."""

        total_chats = len(self.validation_history)
        allowed_chats = sum(
            1
            for history in self.validation_history.values()
            if history and history[-1].decision == ChatAccessDecision.ALLOW
        )
        left_chats = total_chats - allowed_chats

        recent_validations = sum(
            1
            for timestamp in self.last_validation.values()
            if datetime.utcnow() - timestamp < timedelta(hours=24)
        )

        return {
            "total_chats_validated": total_chats,
            "current_chats_allowed": allowed_chats,
            "chats_left": left_chats,
            "recent_validations_24h": recent_validations,
            "admin_ids": self.admin_ids,
            "validation_history_size": sum(
                len(history) for history in self.validation_history.values()
            ),
        }

    def cleanup_old_data(self):
        """Clean up old validation data to prevent memory leaks."""

        cutoff = datetime.utcnow() - timedelta(days=30)

        # Clean validation history
        old_chats = [
            chat_id
            for chat_id, history in self.validation_history.items()
            if not history or history[-1].timestamp < cutoff
        ]
        for chat_id in old_chats:
            del self.validation_history[chat_id]

        # Clean last validation times
        old_validation_times = [
            chat_id
            for chat_id, timestamp in self.last_validation.items()
            if timestamp < cutoff
        ]
        for chat_id in old_validation_times:
            del self.last_validation[chat_id]

        logger.info(f"Cleaned up validation data for {len(old_chats)} old chats")
