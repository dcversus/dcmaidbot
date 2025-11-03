"""Telegram rich features tools for LLM integration.

This module provides tools that allow the LLM to generate and manage
Telegram UI elements, handle events, and create interactive experiences.
"""

import logging
from datetime import datetime
from typing import Any, Optional

from aiogram import Bot
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from utils.markdown_renderer import MarkdownRenderer, Platform

from core.services.event_service import ApiKeyService, EventService
from core.services.nudge_token_service import NudgeTokenService
from core.services.rpg_service import RPGService

logger = logging.getLogger(__name__)


class TelegramTools:
    """Collection of Telegram-rich feature tools for LLM use."""

    def __init__(self, session, bot: Bot, tool_executor=None):
        """Initialize Telegram tools with dependencies."""
        self.session = session
        self.bot = bot
        self.tool_executor = tool_executor
        self.event_service = EventService(session)
        self.api_key_service = ApiKeyService(session)
        self.nudge_token_service = NudgeTokenService(session)
        self.rpg_service = RPGService(session)
        self.markdown_renderer = MarkdownRenderer(Platform.TELEGRAM)

    async def send_telegram_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: Optional[dict] = None,
        disable_web_page_preview: bool = False,
        use_markdown_renderer: bool = True,
    ) -> dict[str, Any]:
        """Send a message with rich formatting and keyboards."""
        try:
            # Build keyboard if provided
            keyboard = None
            if reply_markup:
                keyboard = self._build_keyboard(reply_markup)

            # Apply markdown rendering if requested and not already HTML
            formatted_text = text
            if use_markdown_renderer and parse_mode != "HTML":
                formatted_text = self.markdown_renderer.parse_and_render_markdown(text)
            elif use_markdown_renderer and parse_mode == "HTML":
                # If parse_mode is HTML but we want markdown, we still render but keep HTML
                formatted_text = self.markdown_renderer.parse_and_render_markdown(text)

            message = await self.bot.send_message(
                chat_id=chat_id,
                text=formatted_text,
                parse_mode=parse_mode,
                reply_markup=keyboard,
                disable_web_page_preview=disable_web_page_preview,
            )

            return {
                "success": True,
                "message_id": message.message_id,
                "chat_id": message.chat.id,
                "text": message.text,
                "formatted_text": formatted_text,
                "message": "Message sent successfully",
            }

        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}", exc_info=True)
            return {"success": False, "error": f"Failed to send message: {str(e)}"}

    async def send_rich_message_to_user(
        self,
        user_id: int,
        title: str,
        content: str,
        sections: Optional[list[str]] = None,
        status: str = "info",
        include_separator: bool = True,
    ) -> dict[str, Any]:
        """Send a richly formatted message to a specific user (like Vasilisa!)."""
        try:
            # Build the rich message
            message_parts = []

            # Add title
            if title:
                message_parts.append(
                    self.markdown_renderer.render_heading(title, 1, "info")
                )

            # Add main content
            if content:
                message_parts.append(content)

            # Add sections if provided
            if sections:
                for section in sections:
                    message_parts.append("")
                    message_parts.append(
                        self.markdown_renderer.render_heading(section, 2, "info")
                    )

            # Add status line
            if status:
                message_parts.append("")
                message_parts.append(
                    self.markdown_renderer.format_status_line(status, status)
                )

            # Add separator
            if include_separator:
                message_parts.append("")
                message_parts.append(self.markdown_renderer.format_separator())

            # Join all parts
            full_message = "\n".join(message_parts)

            # Send the message
            return await self.send_telegram_message(
                chat_id=user_id,
                text=full_message,
                parse_mode="HTML",
                use_markdown_renderer=True,
                disable_web_page_preview=True,
            )

        except Exception as e:
            logger.error(
                f"Error sending rich message to user {user_id}: {e}", exc_info=True
            )
            return {
                "success": False,
                "error": f"Failed to send rich message: {str(e)}",
            }

    async def send_changelog_to_user(
        self,
        user_id: int,
        version: str,
        sections: dict[str, list[str]],
        title: str = None,
    ) -> dict[str, Any]:
        """Send a formatted changelog to a specific user."""
        try:
            # Create changelog using the markdown renderer
            changelog = self.markdown_renderer.render_changelog_entry(
                version, sections, title
            )

            # Add a nice header
            header_emoji = self.markdown_renderer.get_next_emoji(["🎉", "🚀", "⭐"])
            if not title:
                title = f"Update Release {version}"

            full_message = f"{header_emoji} {title}\n\n{changelog}"

            # Send the changelog
            return await self.send_telegram_message(
                chat_id=user_id,
                text=full_message,
                parse_mode="HTML",
                use_markdown_renderer=True,
                disable_web_page_preview=True,
            )

        except Exception as e:
            logger.error(
                f"Error sending changelog to user {user_id}: {e}", exc_info=True
            )
            return {
                "success": False,
                "error": f"Failed to send changelog: {str(e)}",
            }

    async def send_status_update(
        self,
        user_id: int,
        status: str,
        details: str = "",
        include_emoji: bool = True,
    ) -> dict[str, Any]:
        """Send a quick status update to a specific user."""
        try:
            if details:
                message = f"{status}\n\n{details}"
            else:
                message = status

            # Format with markdown if emoji is requested
            if include_emoji:
                formatted_message = self.markdown_renderer.format_status_line(
                    message, status
                )
            else:
                formatted_message = message

            return await self.send_telegram_message(
                chat_id=user_id,
                text=formatted_message,
                parse_mode="HTML",
                use_markdown_renderer=include_emoji,
                disable_web_page_preview=True,
            )

        except Exception as e:
            logger.error(
                f"Error sending status update to user {user_id}: {e}", exc_info=True
            )
            return {
                "success": False,
                "error": f"Failed to send status update: {str(e)}",
            }

    async def create_inline_keyboard(
        self, buttons: list[dict[str, Any]], row_width: int = 2
    ) -> dict[str, Any]:
        """Create an inline keyboard layout."""
        try:
            keyboard_rows = []
            current_row = []

            for button_data in buttons:
                button = InlineKeyboardButton(
                    text=button_data.get("text", ""),
                    callback_data=button_data.get("callback_data"),
                    url=button_data.get("url"),
                    web_app=button_data.get("web_app"),
                    callback_game=button_data.get("callback_game"),
                    pay=button_data.get("pay", False),
                    switch_inline_query=button_data.get("switch_inline_query"),
                    switch_inline_query_current_chat=button_data.get(
                        "switch_inline_query_current_chat"
                    ),
                    description=button_data.get("description"),
                )

                current_row.append(button)

                if len(current_row) >= row_width:
                    keyboard_rows.append(current_row)
                    current_row = []

            # Add remaining buttons
            if current_row:
                keyboard_rows.append(current_row)

            inline_keyboard = InlineKeyboardMarkup(inline_rows=keyboard_rows)

            return {
                "success": True,
                "keyboard": inline_keyboard,
                "button_count": len(buttons),
                "row_count": len(keyboard_rows),
            }

        except Exception as e:
            logger.error(f"Error creating inline keyboard: {e}", exc_info=True)
            return {"success": False, "error": f"Failed to create keyboard: {str(e)}"}

    async def create_reply_keyboard(
        self,
        buttons: list[str],
        resize_keyboard: bool = True,
        one_time_keyboard: bool = False,
        selective: bool = False,
        input_field_placeholder: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a reply keyboard layout."""
        try:
            # Arrange buttons in rows
            keyboard_rows = []
            current_row = []

            for button_text in buttons:
                button = KeyboardButton(
                    text=button_text,
                    request_contact=False,
                    request_location=False,
                    request_poll=None,
                    web_app=None,
                )

                current_row.append(button)

                # Auto-arrange in rows of 2-3 buttons
                if len(current_row) >= 2:
                    keyboard_rows.append(current_row)
                    current_row = []

            # Add remaining buttons
            if current_row:
                keyboard_rows.append(current_row)

            reply_keyboard = ReplyKeyboardMarkup(
                keyboard=keyboard_rows,
                resize_keyboard=resize_keyboard,
                one_time_keyboard=one_time_keyboard,
                selective=selective,
                input_field_placeholder=input_field_placeholder,
            )

            return {
                "success": True,
                "keyboard": reply_keyboard,
                "button_count": len(buttons),
                "row_count": len(keyboard_rows),
            }

        except Exception as e:
            logger.error(f"Error creating reply keyboard: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to create reply keyboard: {str(e)}",
            }

    async def manage_events(
        self,
        action: str,
        event_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Manage collected events (read, update status, get unread)."""
        try:
            if action == "get_unread":
                events = await self.event_service.get_unread_events(limit=limit)
                return {
                    "success": True,
                    "events": [event.to_dict() for event in events],
                    "count": len(events),
                    "action": "retrieved_unread",
                }

            elif action == "mark_read":
                if not event_id:
                    return {
                        "success": False,
                        "error": "event_id is required for mark_read action",
                    }

                success = await self.event_service.update_event_status(event_id, "read")
                return {
                    "success": success,
                    "event_id": event_id,
                    "action": "marked_read",
                    "message": "Event marked as read"
                    if success
                    else "Failed to mark event as read",
                }

            elif action == "mark_completed":
                if not event_id:
                    return {
                        "success": False,
                        "error": "event_id is required for mark_completed action",
                    }

                success = await self.event_service.update_event_status(
                    event_id, "completed"
                )
                return {
                    "success": success,
                    "event_id": event_id,
                    "action": "marked_completed",
                    "message": "Event marked as completed"
                    if success
                    else "Failed to mark event as completed",
                }

            elif action == "get_user_events":
                # This would need user_id from context
                return {
                    "success": False,
                    "error": "get_user_events requires user_id context",
                }

            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"Error managing events: {e}", exc_info=True)
            return {"success": False, "error": f"Failed to manage events: {str(e)}"}

    async def create_api_key(
        self,
        name: str,
        allowed_event_types: Optional[list[str]] = None,
        rate_limit_per_minute: int = 60,
        rate_limit_per_hour: int = 1000,
        description: Optional[str] = None,
        admin_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """Create an API key for event collection."""
        try:
            # Get admin user ID from context or parameter
            if not admin_id:
                admin_id = 1  # Placeholder - should come from user context

            api_key, raw_key = await self.api_key_service.create_api_key(
                name=name,
                created_by=admin_id,
                allowed_event_types=allowed_event_types,
                rate_limit_per_minute=rate_limit_per_minute,
                rate_limit_per_hour=rate_limit_per_hour,
                description=description,
            )

            return {
                "success": True,
                "api_key": {
                    "id": api_key.id,
                    "name": api_key.name,
                    "key_prefix": api_key.key_prefix,
                    "raw_key": raw_key,  # Only shown once!
                    "allowed_event_types": api_key.allowed_event_types,
                    "rate_limit_per_minute": api_key.rate_limit_per_minute,
                    "rate_limit_per_hour": api_key.rate_limit_per_hour,
                    "created_at": api_key.created_at.isoformat(),
                },
                "warning": "Store the raw_key securely - it will not be shown again!",
            }

        except Exception as e:
            logger.error(f"Error creating API key: {e}", exc_info=True)
            return {"success": False, "error": f"Failed to create API key: {str(e)}"}

    async def list_api_keys(self, admin_id: Optional[int] = None) -> dict[str, Any]:
        """List all API keys created by an admin."""
        try:
            # Get admin user ID from context or parameter
            if not admin_id:
                admin_id = 1  # Placeholder - should come from user context

            api_keys = await self.api_key_service.get_api_keys_by_creator(admin_id)

            keys_data = []
            for key in api_keys:
                key_data = {
                    "id": key.id,
                    "name": key.name,
                    "key_prefix": key.key_prefix,
                    "allowed_event_types": key.allowed_event_types,
                    "rate_limit_per_minute": key.rate_limit_per_minute,
                    "rate_limit_per_hour": key.rate_limit_per_hour,
                    "is_active": key.is_active,
                    "usage_count": key.usage_count,
                    "last_used_at": key.last_used_at.isoformat()
                    if key.last_used_at
                    else None,
                    "created_at": key.created_at.isoformat(),
                    "expires_at": key.expires_at.isoformat()
                    if key.expires_at
                    else None,
                    "description": key.description,
                }
                keys_data.append(key_data)

            return {
                "success": True,
                "count": len(keys_data),
                "api_keys": keys_data,
                "message": f"Found {len(keys_data)} API keys",
            }

        except Exception as e:
            logger.error(f"Error listing API keys: {e}", exc_info=True)
            return {"success": False, "error": f"Failed to list API keys: {str(e)}"}

    async def deactivate_api_key(
        self, api_key_id: int, admin_id: Optional[int] = None
    ) -> dict[str, Any]:
        """Deactivate an API key."""
        try:
            # Verify admin is the creator of this key (security check)
            if not admin_id:
                admin_id = 1  # Placeholder - should come from user context

            api_key = await self.api_key_service.get_api_key_by_id(api_key_id)
            if not api_key:
                return {"success": False, "error": "API key not found"}

            if api_key.created_by != admin_id:
                return {
                    "success": False,
                    "error": "Permission denied - you can only deactivate your own keys",
                }

            success = await self.api_key_service.deactivate_api_key(api_key_id)

            return {
                "success": success,
                "api_key_id": api_key_id,
                "message": "API key deactivated successfully"
                if success
                else "Failed to deactivate API key",
            }

        except Exception as e:
            logger.error(f"Error deactivating API key: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to deactivate API key: {str(e)}",
            }

    async def get_api_key_info(
        self, api_key_id: int, admin_id: Optional[int] = None
    ) -> dict[str, Any]:
        """Get detailed information about an API key."""
        try:
            # Verify admin is the creator of this key (security check)
            if not admin_id:
                admin_id = 1  # Placeholder - should come from user context

            api_key = await self.api_key_service.get_api_key_by_id(api_key_id)
            if not api_key:
                return {"success": False, "error": "API key not found"}

            if api_key.created_by != admin_id:
                return {
                    "success": False,
                    "error": "Permission denied - you can only view your own keys",
                }

            return {
                "success": True,
                "api_key": {
                    "id": api_key.id,
                    "name": api_key.name,
                    "key_prefix": api_key.key_prefix,
                    "allowed_event_types": api_key.allowed_event_types,
                    "rate_limit_per_minute": api_key.rate_limit_per_minute,
                    "rate_limit_per_hour": api_key.rate_limit_per_hour,
                    "is_active": api_key.is_active,
                    "usage_count": api_key.usage_count,
                    "last_used_at": api_key.last_used_at.isoformat()
                    if api_key.last_used_at
                    else None,
                    "created_at": api_key.created_at.isoformat(),
                    "expires_at": api_key.expires_at.isoformat()
                    if api_key.expires_at
                    else None,
                    "description": api_key.description,
                },
            }

        except Exception as e:
            logger.error(f"Error getting API key info: {e}", exc_info=True)
            return {"success": False, "error": f"Failed to get API key info: {str(e)}"}

    async def create_nudge_token(
        self,
        name: str,
        description: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        admin_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """Create a nudge token for /nudge endpoint authentication."""
        try:
            # Get admin user ID from context or parameter
            if not admin_id:
                admin_id = 1  # Placeholder - should come from user context

            nudge_token, raw_token = await self.nudge_token_service.create_nudge_token(
                name=name,
                created_by=admin_id,
                description=description,
                expires_at=expires_at,
            )

            return {
                "success": True,
                "nudge_token": {
                    "id": nudge_token.id,
                    "name": nudge_token.name,
                    "token_prefix": nudge_token.token_prefix,
                    "raw_token": raw_token,  # Only shown once!
                    "description": nudge_token.description,
                    "expires_at": nudge_token.expires_at.isoformat()
                    if nudge_token.expires_at
                    else None,
                    "created_at": nudge_token.created_at.isoformat(),
                },
                "warning": "Store the raw_token securely - it will not be shown again!",
                "usage": f"Use as: Authorization: Bearer {raw_token}",
            }

        except Exception as e:
            logger.error(f"Error creating nudge token: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to create nudge token: {str(e)}",
            }

    async def list_nudge_tokens(self, admin_id: Optional[int] = None) -> dict[str, Any]:
        """List all nudge tokens created by an admin."""
        try:
            # Get admin user ID from context or parameter
            if not admin_id:
                admin_id = 1  # Placeholder - should come from user context

            nudge_tokens = await self.nudge_token_service.get_nudge_tokens_by_creator(
                admin_id
            )

            tokens_data = []
            for token in nudge_tokens:
                token_data = {
                    "id": token.id,
                    "name": token.name,
                    "token_prefix": token.token_prefix,
                    "description": token.description,
                    "is_active": token.is_active,
                    "is_expired": token.is_expired(),
                    "is_valid": token.is_valid(),
                    "usage_count": token.usage_count,
                    "last_used_at": token.last_used_at.isoformat()
                    if token.last_used_at
                    else None,
                    "created_at": token.created_at.isoformat(),
                    "expires_at": token.expires_at.isoformat()
                    if token.expires_at
                    else None,
                }
                tokens_data.append(token_data)

            return {
                "success": True,
                "count": len(tokens_data),
                "nudge_tokens": tokens_data,
                "message": f"Found {len(tokens_data)} nudge tokens",
            }

        except Exception as e:
            logger.error(f"Error listing nudge tokens: {e}", exc_info=True)
            return {"success": False, "error": f"Failed to list nudge tokens: {str(e)}"}

    async def deactivate_nudge_token(
        self, token_id: int, admin_id: Optional[int] = None
    ) -> dict[str, Any]:
        """Deactivate a nudge token."""
        try:
            # Verify admin is the creator of this token (security check)
            if not admin_id:
                admin_id = 1  # Placeholder - should come from user context

            nudge_token = await self.nudge_token_service.get_nudge_token_by_id(token_id)
            if not nudge_token:
                return {"success": False, "error": "Nudge token not found"}

            if nudge_token.created_by != admin_id:
                return {
                    "success": False,
                    "error": "Permission denied - you can only deactivate your own tokens",
                }

            success = await self.nudge_token_service.deactivate_nudge_token(token_id)

            return {
                "success": success,
                "token_id": token_id,
                "message": "Nudge token deactivated successfully"
                if success
                else "Failed to deactivate nudge token",
            }

        except Exception as e:
            logger.error(f"Error deactivating nudge token: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to deactivate nudge token: {str(e)}",
            }

    async def get_nudge_token_info(
        self, token_id: int, admin_id: Optional[int] = None
    ) -> dict[str, Any]:
        """Get detailed information about a nudge token."""
        try:
            # Verify admin is the creator of this token (security check)
            if not admin_id:
                admin_id = 1  # Placeholder - should come from user context

            nudge_token = await self.nudge_token_service.get_nudge_token_by_id(token_id)
            if not nudge_token:
                return {"success": False, "error": "Nudge token not found"}

            if nudge_token.created_by != admin_id:
                return {
                    "success": False,
                    "error": "Permission denied - you can only view your own tokens",
                }

            return {
                "success": True,
                "nudge_token": {
                    "id": nudge_token.id,
                    "name": nudge_token.name,
                    "token_prefix": nudge_token.token_prefix,
                    "description": nudge_token.description,
                    "is_active": nudge_token.is_active,
                    "is_expired": nudge_token.is_expired(),
                    "is_valid": nudge_token.is_valid(),
                    "usage_count": nudge_token.usage_count,
                    "last_used_at": nudge_token.last_used_at.isoformat()
                    if nudge_token.last_used_at
                    else None,
                    "created_at": nudge_token.created_at.isoformat(),
                    "expires_at": nudge_token.expires_at.isoformat()
                    if nudge_token.expires_at
                    else None,
                },
            }

        except Exception as e:
            logger.error(f"Error getting nudge token info: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to get nudge token info: {str(e)}",
            }

    async def game_master_action(
        self,
        action: str,
        session_id: Optional[str] = None,
        user_id: Optional[int] = None,
        game_data: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Perform RPG game master actions."""
        try:
            if action == "create_session":
                if not game_data or not game_data.get("name"):
                    return {
                        "success": False,
                        "error": "Game data with 'name' is required for creating session",
                    }

                session = await self.rpg_service.create_game_session(
                    name=game_data["name"],
                    description=game_data.get("description"),
                    scenario_template=game_data.get("scenario_template", "default"),
                    difficulty_level=game_data.get("difficulty_level", "normal"),
                    max_players=game_data.get("max_players", 4),
                    created_by=user_id or 1,  # Placeholder
                )

                return {
                    "success": True,
                    "session": session.to_dict(include_hidden=True),
                    "message": f"Game session '{session.name}' created successfully",
                }

            elif action == "join_session":
                if not session_id or not user_id:
                    return {
                        "success": False,
                        "error": "session_id and user_id are required for joining session",
                    }

                character_name = game_data.get("character_name") if game_data else None
                player_state = await self.rpg_service.join_game_session(
                    session_id=session_id,
                    user_id=user_id,
                    character_name=character_name or "Player",
                )

                return {
                    "success": True,
                    "player_state": player_state.to_dict(),
                    "message": f"Joined game session as {player_state.character_name}",
                }

            elif action == "process_action":
                if not session_id or not user_id or not game_data:
                    return {
                        "success": False,
                        "error": "session_id, user_id, and game_data with 'action' are required",
                    }

                result = await self.rpg_service.process_player_action(
                    session_id=session_id,
                    user_id=user_id,
                    action=game_data["action"],
                    action_data=game_data.get("action_data", {}),
                )

                return {
                    "success": True,
                    "result": result,
                    "message": "Action processed successfully",
                }

            elif action == "get_session_state":
                if not session_id:
                    return {
                        "success": False,
                        "error": "session_id is required for getting session state",
                    }

                session_state = await self.rpg_service.get_session_state(
                    session_id=session_id, user_id=user_id
                )

                return {
                    "success": True,
                    "session_state": session_state,
                    "message": "Session state retrieved successfully",
                }

            else:
                return {
                    "success": False,
                    "error": f"Unknown game master action: {action}",
                }

        except Exception as e:
            logger.error(f"Error in game master action: {e}", exc_info=True)
            return {"success": False, "error": f"Game master action failed: {str(e)}"}

    def _build_keyboard(self, keyboard_data: dict) -> Optional[InlineKeyboardMarkup]:
        """Build keyboard from dictionary data."""
        try:
            if "inline_keyboard" in keyboard_data:
                return InlineKeyboardMarkup(
                    inline_rows=keyboard_data["inline_keyboard"]
                )
            return None
        except Exception as e:
            logger.error(f"Error building keyboard: {e}")
            return None

    async def send_media_group(
        self,
        chat_id: int,
        media_list: list[dict[str, Any]],
        disable_notification: bool = False,
    ) -> dict[str, Any]:
        """Send a group of media files (photos, videos, documents)."""
        try:
            # This would require proper media handling with aiogram
            # For now, return a placeholder response
            return {
                "success": False,
                "error": "Media group sending not yet implemented",
                "media_count": len(media_list),
            }

        except Exception as e:
            logger.error(f"Error sending media group: {e}", exc_info=True)
            return {"success": False, "error": f"Failed to send media group: {str(e)}"}

    async def edit_message(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Edit an existing message."""
        try:
            keyboard = None
            if reply_markup:
                keyboard = self._build_keyboard(reply_markup)

            message = await self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                parse_mode=parse_mode,
                reply_markup=keyboard,
            )

            return {
                "success": True,
                "message_id": message.message_id,
                "text": message.text,
                "message": "Message edited successfully",
            }

        except Exception as e:
            logger.error(f"Error editing message: {e}", exc_info=True)
            return {"success": False, "error": f"Failed to edit message: {str(e)}"}
