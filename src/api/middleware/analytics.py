"""
Analytics Middleware (PRP-012)

Middleware to automatically track all messages, commands, and interactions
for analytics and observability.
"""

import time
from typing import Any, Awaitable, Callable, Dict, Union

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, ChatJoinRequest, Message

from core.services.analytics_service import analytics


class AnalyticsMiddleware(BaseMiddleware):
    """Middleware to track all bot interactions"""

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery, ChatJoinRequest],
        data: Dict[str, Any],
    ) -> Any:
        # Skip analytics if disabled
        if not analytics.enabled:
            return await handler(event, data)

        start_time = time.time()
        error_type = None

        try:
            # Determine interaction type and track accordingly
            if isinstance(event, Message):
                await self._track_message(event, data)
            elif isinstance(event, CallbackQuery):
                await self._track_callback(event, data)
            elif isinstance(event, ChatJoinRequest):
                await self._track_chat_join(event, data)

            # Execute the handler
            result = await handler(event, data)
            return result

        except Exception as e:
            error_type = type(e).__name__
            analytics.track_error(error_type, "message_handler")
            raise

        finally:
            # Track processing time
            processing_time = time.time() - start_time
            event_type = type(event).__name__.lower()
            analytics.metrics.message_processing_time.labels(
                message_type=event_type
            ).observe(processing_time)

    async def _track_message(self, message: Message, data: Dict[str, Any]):
        """Track incoming message"""
        chat_type = message.chat.type
        language = message.from_user.language_code or "en"

        # Track the message
        analytics.track_message(
            chat_type=chat_type, language=language, status="success"
        )

        # Track if it's a command
        if message.text and message.text.startswith("/"):
            command = message.text.split()[0][1:]  # Remove '/'
            analytics.track_command(command, "success")

    async def _track_callback(self, callback: CallbackQuery, data: Dict[str, Any]):
        """Track callback query (button press)"""
        # Track as interaction
        analytics.track_message(
            chat_type=callback.message.chat.type if callback.message else "private",
            language=callback.from_user.language_code or "en",
            status="callback",
        )

        # Track callback data if present
        if callback.data:
            # Extract command/action from callback data
            action = (
                callback.data.split(":")[0] if ":" in callback.data else callback.data
            )
            analytics.track_command(f"callback_{action}", "success")

    async def _track_chat_join(
        self, join_request: ChatJoinRequest, data: Dict[str, Any]
    ):
        """Track chat join request"""
        analytics.track_message(
            chat_type=join_request.chat.type,
            language=join_request.from_user.language_code or "en",
            status="join_request",
        )
