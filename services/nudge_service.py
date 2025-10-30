"""
Nudge Service for agent-to-user communication.

Provides two modes of messaging:
1. Direct: Send Markdown message directly via Telegram API
2. LLM: Process through dcmaidbot LLM pipeline for personalized messages
"""

import os
from typing import Any, Optional

from aiogram import Bot
from aiogram.enums import ParseMode

from services.llm_service import LLMService


class NudgeService:
    """Service for sending messages to admins via Telegram."""

    def __init__(self):
        """Initialize NudgeService with Bot instance."""
        self.bot_token = os.getenv("BOT_TOKEN")
        if not self.bot_token:
            raise ValueError("BOT_TOKEN not configured in environment")

        self.bot = Bot(token=self.bot_token)
        self.llm_service = LLMService()

    def _get_admin_ids(self) -> list[int]:
        """Get admin IDs from ADMIN_IDS environment variable."""
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        if not admin_ids_str:
            raise ValueError("ADMIN_IDS not configured in environment")

        # Parse comma-separated list of IDs
        try:
            admin_ids = [int(id_str.strip()) for id_str in admin_ids_str.split(",")]
            return admin_ids
        except ValueError as e:
            raise ValueError(f"Invalid ADMIN_IDS format: {e}")

    async def send_direct(
        self,
        message: str,
        user_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """Send message directly via Telegram API with Markdown formatting.

        Args:
            message: Markdown-formatted message to send
            user_id: Optional specific user ID (default: all admins)

        Returns:
            dict: Results with sent message IDs

        Raises:
            ValueError: If BOT_TOKEN or ADMIN_IDS not configured
            TelegramAPIError: If sending message fails
        """
        # Determine target user IDs
        target_ids = [user_id] if user_id else self._get_admin_ids()

        results = []
        errors = []

        # Send message to each target user
        for uid in target_ids:
            try:
                sent_message = await self.bot.send_message(
                    chat_id=uid,
                    text=message,
                    parse_mode=ParseMode.MARKDOWN,
                )
                results.append(
                    {
                        "user_id": uid,
                        "message_id": sent_message.message_id,
                        "status": "success",
                    }
                )
            except Exception as e:
                errors.append(
                    {
                        "user_id": uid,
                        "error": str(e),
                        "status": "failed",
                    }
                )

        return {
            "success": len(errors) == 0,
            "mode": "direct",
            "sent_count": len(results),
            "failed_count": len(errors),
            "results": results,
            "errors": errors if errors else None,
        }

    async def send_via_llm(
        self,
        message: str,
        user_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """Process message through LLM pipeline and send personalized messages.

        Args:
            message: Prompt/message for LLM to process
            user_id: Optional specific user ID (default: all admins)

        Returns:
            dict: Results with sent message IDs and LLM responses

        Raises:
            ValueError: If BOT_TOKEN or ADMIN_IDS not configured
            TelegramAPIError: If sending message fails
        """
        # Determine target user IDs
        target_ids = [user_id] if user_id else self._get_admin_ids()

        results = []
        errors = []

        # Get lessons (bot personality context)
        # Note: Using a mock session for now since we don't have async_session here
        # In production, lessons should be fetched from the database
        lessons: list = []  # TODO: Fetch from LessonService if needed

        # Send personalized message to each target user
        for uid in target_ids:
            try:
                # Prepare LLM prompt with context
                llm_prompt = (
                    f"An external system has asked you to send a message to "
                    f"your admin (user_id: {uid}). Here's what they want you "
                    f"to communicate:\n\n"
                    f"{message}\n\n"
                    f"Please respond in your kawaii waifu personality! Keep it "
                    f"friendly, warm, and include relevant emojis. The message "
                    f"should feel natural and personal, not robotic. Nya~ 💕"
                )

                # Generate personalized response via LLM
                llm_response = await self.llm_service.get_response(
                    user_message=llm_prompt,
                    user_info={"telegram_id": uid, "username": f"admin_{uid}"},
                    chat_info={"chat_id": uid, "chat_type": "private"},
                    lessons=lessons,
                    memories=[],
                    message_history=[],
                    use_tools=False,  # Don't need tools for this
                )

                # Handle tool calls (shouldn't happen with use_tools=False)
                final_message = llm_response
                if hasattr(llm_response, "content"):
                    final_message = llm_response.content

                # Send LLM-generated message via Telegram
                sent_message = await self.bot.send_message(
                    chat_id=uid,
                    text=final_message,
                    parse_mode=ParseMode.MARKDOWN,
                )

                results.append(
                    {
                        "user_id": uid,
                        "message_id": sent_message.message_id,
                        "llm_response": final_message,
                        "status": "success",
                    }
                )

            except Exception as e:
                errors.append(
                    {
                        "user_id": uid,
                        "error": str(e),
                        "status": "failed",
                    }
                )

        return {
            "success": len(errors) == 0,
            "mode": "llm",
            "sent_count": len(results),
            "failed_count": len(errors),
            "results": results,
            "errors": errors if errors else None,
        }
