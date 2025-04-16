import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from handlers import categories, activities, selection, info, help
from middlewares.private_only import PrivateChatMiddleware

# Load environment variables first
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

def get_bot_token() -> str:
    """Retrieves and validates the bot token from environment variables."""
    token = os.getenv("BOT_TOKEN")
    if not token:
        logging.error("No BOT_TOKEN provided. Please check your .env file")
        raise ValueError("BOT_TOKEN not found in environment variables")
    return token

def setup_dispatcher() -> Dispatcher:
    """Initializes and configures the dispatcher."""
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register the private chat middleware
    dp.message.middleware(PrivateChatMiddleware())
    dp.callback_query.middleware(PrivateChatMiddleware())
    
    # Register all routers
    dp.include_router(help.router)
    dp.include_router(categories.router)
    dp.include_router(activities.router)
    dp.include_router(selection.router)
    dp.include_router(info.router)
    
    return dp


async def main():
    """Main function to run the bot in polling mode."""
    try:
        token = get_bot_token()
    except ValueError as e:
        logging.error(e)
        return

    bot = Bot(token=token)
    dp = setup_dispatcher()

    # Skip pending updates and start polling
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Starting polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!") 