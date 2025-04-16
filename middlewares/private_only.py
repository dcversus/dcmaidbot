from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject, CallbackQuery
from aiogram.enums import ChatType

class PrivateChatMiddleware(BaseMiddleware):
    """Middleware to restrict bot usage to private chats only"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # For messages, check if it's a private chat
        if isinstance(event, Message):
            if event.chat.type != ChatType.PRIVATE:
                # Send message and return None
                await event.answer("Бот работает только в личных сообщениях.")
                return None
        
        # For callback queries, check if the original message is from a private chat
        elif isinstance(event, CallbackQuery) and event.message:
            if event.message.chat.type != ChatType.PRIVATE:
                # Send message and return None
                await event.answer(
                    "Бот работает только в личных сообщениях.", show_alert=True
                )
                return None
        
        # Process event if it's from a private chat
        return await handler(event, data)