"""
DCMaidBot - Webhook Mode
Kawai waifu bot with webhook support for production deployment.
"""

import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from dotenv import load_dotenv

from handlers import waifu
from middlewares.admin_only import AdminOnlyMiddleware

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)


def get_bot_token() -> str:
    """Retrieves and validates the bot token."""
    token = os.getenv("BOT_TOKEN")
    if not token:
        logging.error("No BOT_TOKEN provided")
        raise ValueError("BOT_TOKEN not found")
    return token


def get_admin_ids() -> list[int]:
    """Retrieves admin IDs (NEVER logs actual IDs)."""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    admins = []

    if not admin_ids_str:
        logging.warning("No ADMIN_IDS configured")
        return admins

    for admin_id in admin_ids_str.split(","):
        admin_id = admin_id.strip()
        if not admin_id:
            continue
        try:
            admins.append(int(admin_id))
        except ValueError:
            logging.warning("Invalid admin ID format (skipped)")

    if admins:
        logging.info(f"Loaded {len(admins)} admin(s)")
    else:
        logging.warning("No valid admin IDs found")

    return admins


def get_webhook_config():
    """Get webhook configuration."""
    return {
        "url": os.getenv("WEBHOOK_URL", ""),
        "path": os.getenv("WEBHOOK_PATH", "/webhook"),
        "host": os.getenv("WEBHOOK_HOST", "0.0.0.0"),
        "port": int(os.getenv("WEBHOOK_PORT", "8080")),
        "secret": os.getenv("WEBHOOK_SECRET", "dcmaidbot-secret-token"),
    }


def setup_dispatcher() -> Dispatcher:
    """Setup dispatcher with handlers and middleware."""
    dp = Dispatcher()

    admin_ids = get_admin_ids()
    dp.message.middleware(AdminOnlyMiddleware(admin_ids))
    dp.callback_query.middleware(AdminOnlyMiddleware(admin_ids))

    dp.include_router(waifu.router)

    return dp


async def on_startup(bot: Bot, webhook_url: str, secret: str):
    """Set webhook on startup."""
    await bot.set_webhook(
        url=webhook_url,
        secret_token=secret,
        allowed_updates=["message", "callback_query"],
    )
    logging.info(f"Webhook set to: {webhook_url}")


async def on_shutdown(bot: Bot):
    """Cleanup on shutdown."""
    await bot.delete_webhook()
    logging.info("Webhook deleted")


def main():
    """Main function for webhook mode."""
    token = get_bot_token()
    webhook_config = get_webhook_config()

    # Check if webhook mode is enabled
    webhook_mode = os.getenv("WEBHOOK_MODE", "false").lower() == "true"

    if not webhook_mode or not webhook_config["url"]:
        logging.error("WEBHOOK_MODE=true and WEBHOOK_URL required for webhook mode")
        logging.error("Use bot.py for polling mode instead")
        return

    bot = Bot(token=token)
    dp = setup_dispatcher()

    # Create aiohttp application
    app = web.Application()

    # Setup webhook handler
    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=webhook_config["secret"],
    )
    webhook_handler.register(app, path=webhook_config["path"])

    # Setup application
    setup_application(app, dp, bot=bot)

    # Set webhook on startup
    app.on_startup.append(
        lambda app: on_startup(bot, webhook_config["url"], webhook_config["secret"])
    )
    app.on_shutdown.append(lambda app: on_shutdown(bot))

    # Run web server
    host = webhook_config["host"]
    port = webhook_config["port"]
    logging.info(f"Starting webhook server on {host}:{port}")
    web.run_app(
        app,
        host=webhook_config["host"],
        port=webhook_config["port"],
    )


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")
