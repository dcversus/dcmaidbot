import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from handlers import waifu
from middlewares.admin_only import AdminOnlyMiddleware
from services.migration_service import check_migrations
from database import engine

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
    """Retrieves admin IDs from environment variables (NEVER logs actual IDs)."""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    admins: list[int] = []

    if not admin_ids_str:
        logging.warning("No ADMIN_IDS configured. Bot will not respond to anyone.")
        return admins

    # Parse comma-separated admin IDs
    for admin_id in admin_ids_str.split(","):
        admin_id = admin_id.strip()
        if not admin_id:
            continue
        try:
            admins.append(int(admin_id))
        except ValueError:
            # PRIVACY: Never log the actual ID value
            logging.warning("Invalid admin ID format detected (skipped)")

    if admins:
        logging.info(f"Loaded {len(admins)} admin(s) from ADMIN_IDS")
    else:
        logging.warning("No valid admin IDs found. Bot will not respond.")

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

    # Check database migrations FIRST (blocks startup if not up to date)
    await check_migrations(engine)

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
