import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os

from handlers import categories, activities, selection, info, help
from middlewares.private_only import PrivateChatMiddleware

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

# Get bot token from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def main():
    # Check if token is available
    if not BOT_TOKEN:
        logging.error("No BOT_TOKEN provided. Please check your .env file")
        return
    
    # Initialize Bot instance
    bot = Bot(token=BOT_TOKEN)
    
    # Initialize dispatcher with memory storage for FSM
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
    
    # Skip pending updates and start polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!") 