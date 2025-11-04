"""
Nudge Service for agent-to-user communication.

Provides two modes of messaging:
1. Direct: Send Markdown message via messenger abstraction
2. LLM: Process through dcmaidbot LLM pipeline for personalized messages
"""

import os
from typing import Any, Dict, List, Optional

from src.core.services.llm_service import LLMService
from src.core.services.messenger_service import (
    EmbedField,
    MessageType,
    RichContent,
    get_messenger_service,
)


class NudgeService:
    """Service for sending messages to admins via messenger abstraction.

    Uses the messenger service abstraction for platform-agnostic messaging.
    This allows for easy switching between messaging platforms and provides
    rich content rendering capabilities.
    """

    def __init__(self, platform: str = "telegram"):
        """Initialize NudgeService with messenger abstraction.

        Creates messenger service instance for rich content communication.
        This instance handles platform-specific message formatting and delivery.

        Args:
            platform: Messaging platform to use ("telegram" or "discord")

        Raises:
            ValueError: If required environment variables are not configured
        """
        self.platform = platform
        self.messenger_service = get_messenger_service(platform)
        self.llm_service = LLMService()

    def _get_admin_ids(self) -> list[int]:
        """Get admin IDs from platform-specific environment variables."""
        if self.platform.lower() == "discord":
            env_var = "DISCORD_ADMIN_IDS"
            fallback_var = "ADMIN_IDS"
        else:
            env_var = "ADMIN_IDS"
            fallback_var = None

        admin_ids_str = os.getenv(env_var, "") or (
            os.getenv(fallback_var, "") if fallback_var else ""
        )
        if not admin_ids_str:
            raise ValueError(f"{env_var} not configured in environment")

        # Parse comma-separated list of IDs
        try:
            admin_ids = [int(id_str.strip()) for id_str in admin_ids_str.split(",")]
            return admin_ids
        except ValueError as e:
            raise ValueError(f"Invalid {env_var} format: {e}")

    async def send_direct(
        self,
        message: str,
        user_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """Send message via messenger abstraction with rich content rendering.

        Args:
            message: Markdown-formatted message to send
            user_id: Optional specific user ID (default: all admins)

        Returns:
            dict: Results with sent message IDs

        Raises:
            ValueError: If ADMIN_IDS not configured
            Exception: If sending message fails
        """
        # Determine target user IDs
        target_ids = [user_id] if user_id else self._get_admin_ids()

        results = []
        errors = []

        # Send message to each target user via messenger service
        for uid in target_ids:
            try:
                # Parse markdown to platform-specific rich content
                rich_content = self.messenger_service.parse_markdown_to_platform(
                    message
                )

                # Send via messenger abstraction
                send_result = await self.messenger_service.send_rich_content(
                    uid, rich_content
                )

                results.append(
                    {
                        "user_id": uid,
                        "message_id": send_result.get("message_id"),
                        "status": send_result.get("status", "unknown"),
                        "content_length": send_result.get("content_length", 0),
                        "has_buttons": send_result.get("has_buttons", False),
                    }
                )

                # Add warning if present
                if send_result.get("status") == "warning":
                    results[-1]["warning"] = send_result.get("error", "Unknown warning")

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
            "platform": self.platform,
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
            ValueError: If ADMIN_IDS not configured
            Exception: If sending message fails
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
                    tools=None,  # Don't provide tools for this
                )

                # Handle tool calls (shouldn't happen with tools=None)
                final_message = llm_response
                if hasattr(llm_response, "content"):
                    final_message = llm_response.content

                # Send LLM-generated message via messenger abstraction
                rich_content = self.messenger_service.parse_markdown_to_platform(
                    final_message
                )
                send_result = await self.messenger_service.send_rich_content(
                    uid, rich_content
                )

                results.append(
                    {
                        "user_id": uid,
                        "message_id": send_result.get("message_id"),
                        "llm_response": final_message,
                        "status": send_result.get("status", "unknown"),
                        "content_length": send_result.get("content_length", 0),
                    }
                )

                # Add warning if present
                if send_result.get("status") == "warning":
                    results[-1]["warning"] = send_result.get("error", "Unknown warning")

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
            "platform": self.platform,
        }

    async def send_embed(
        self,
        title: str,
        description: Optional[str] = None,
        color: Optional[int] = None,
        fields: Optional[List[Dict[str, Any]]] = None,
        footer_text: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """Send Discord embed message (works on Telegram as formatted text)."""
        if self.platform.lower() != "discord":
            # Fallback to regular message for non-Discord platforms
            embed_content = f"**{title}**\n"
            if description:
                embed_content += f"{description}\n"
            if fields:
                for field in fields:
                    embed_content += f"• **{field['name']}**: {field['value']}\n"
            return await self.send_direct(embed_content, user_id)

        target_ids = [user_id] if user_id else self._get_admin_ids()
        results = []
        errors = []

        # Create embed fields
        embed_fields = []
        if fields:
            for field in fields:
                embed_field = EmbedField(
                    name=field["name"],
                    value=field["value"],
                    inline=field.get("inline", False),
                )
                embed_fields.append(embed_field)

        # Create embed using messenger service
        embed = self.messenger_service.create_embed(
            title=title,
            description=description,
            color=color,
            fields=embed_fields,
            footer_text=footer_text,
            thumbnail_url=thumbnail_url,
        )

        for uid in target_ids:
            try:
                # Create rich content with embed
                rich_content = RichContent(
                    content="",  # Main content can be empty when using embeds
                    message_type=MessageType.EMBED,
                    embeds=[embed],
                )

                send_result = await self.messenger_service.send_rich_content(
                    uid, rich_content
                )

                results.append(
                    {
                        "user_id": uid,
                        "message_id": send_result.get("message_id"),
                        "status": send_result.get("status", "unknown"),
                        "embed_title": title,
                        "has_embed": True,
                    }
                )

                if send_result.get("status") == "warning":
                    results[-1]["warning"] = send_result.get("error", "Unknown warning")

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
            "mode": "embed",
            "sent_count": len(results),
            "failed_count": len(errors),
            "results": results,
            "errors": errors if errors else None,
            "platform": self.platform,
        }
