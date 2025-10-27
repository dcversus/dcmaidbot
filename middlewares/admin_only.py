from typing import Callable, Dict, Any, Awaitable, Union
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery


class AdminOnlyMiddleware(BaseMiddleware):
    def __init__(self, admin_ids: list[int]):
        super().__init__()
        self.admin_ids = set(admin_ids)

    async def __call__(
        self,
        handler: Callable[
            [Union[Message, CallbackQuery], Dict[str, Any]], Awaitable[Any]
        ],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any],
    ) -> Any:
        # Allow if user is admin
        if event.from_user.id in self.admin_ids:
            return await handler(event, data)

        # Allow in groups/channels if admin is present in the chat
        if hasattr(event, "chat") and event.chat.type in ["group", "supergroup"]:
            # For groups, check if any admin is in the chat
            # This is simplified; in practice, you'd check chat members
            # For now, allow all group messages (will be filtered in handlers)
            return await handler(event, data)

        # For private chats, only allow admins
        # Skip processing for non-admins
        return
