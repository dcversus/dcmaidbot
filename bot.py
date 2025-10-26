import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from handlers import waifu
from middlewares.admin_only import AdminOnlyMiddleware

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


def get_admin_ids() -> list[int]:
    """Retrieves admin IDs from environment variables."""
    vasilisa_id = os.getenv("ADMIN_VASILISA_ID")
    daniil_id = os.getenv("ADMIN_DANIIL_ID")
    admins = []
    if vasilisa_id:
        try:
            admins.append(int(vasilisa_id))
        except ValueError:
            logging.warning(f"Invalid ADMIN_VASILISA_ID: {vasilisa_id}")
    if daniil_id:
        try:
            admins.append(int(daniil_id))
        except ValueError:
            logging.warning(f"Invalid ADMIN_DANIIL_ID: {daniil_id}")
    if not admins:
        logging.warning("No admin IDs configured. Bot will not respond to anyone.")
    return admins


def setup_dispatcher() -> Dispatcher:
    """Initializes and configures the dispatcher."""
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Get admin IDs
    admin_ids = get_admin_ids()

    # Register the admin-only middleware
    dp.message.middleware(AdminOnlyMiddleware(admin_ids))
    dp.callback_query.middleware(AdminOnlyMiddleware(admin_ids))

    # Register waifu router
    dp.include_router(waifu.router)

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
